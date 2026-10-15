import json
import os
from pathlib import Path
from time import perf_counter
from urllib.request import urlretrieve

import mlflow
import mlflow.sklearn
import optuna
import pandas as pd
from dotenv import load_dotenv
from mlflow import MlflowClient
from mlflow.models import infer_signature
from optuna.samplers import GridSampler, TPESampler
from prefect import flow, get_run_logger, task
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

RAIZ = Path(__file__).resolve().parents[2]
CARPETA_TAREA = Path(__file__).resolve().parent
RUTA_PARAMETROS = CARPETA_TAREA / "mejores-parametros.json"
URL_BASE = "https://d37ci6vzurychx.cloudfront.net/trip-data"
MESES = {"marzo": "2026-03", "abril": "2026-04"}

EXPERIMENTO = "/Shared/pcd-otono-2026-tarea-06-nyc-taxi"
NOMBRE_MODELO = "workspace.default.nyc_taxi_trip_duration_tarea_06"
ALIASES = ["champion", "challenger", "candidate"]
SEMILLA = 42
COMUN = {"course": "proyecto-ciencia-datos", "term": "otono-2026", "task": "06"}

COLUMNAS_CRUDAS = [
    "lpep_pickup_datetime", "lpep_dropoff_datetime", "trip_distance",
    "passenger_count", "PULocationID", "DOLocationID",
]
FEATURES_NUMERICAS = ["distancia_km", "pasajeros", "hora_recoleccion"]
FEATURES_CATEGORICAS = ["zona_origen", "zona_destino"]
FEATURES = FEATURES_NUMERICAS + FEATURES_CATEGORICAS
TARGET = "duracion_minutos"
FAMILIAS = ["linear_regression", "random_forest", "gradient_boosting"]


class ContratoInvalido(ValueError):
    """Los datos no cumplen el schema esperado; reintentar no lo arregla."""


def nombre_archivo(periodo: str) -> str:
    return f"green_tripdata_{periodo}.parquet"


# --- Datos -------------------------------------------------------------------

@task(retries=3, retry_delay_seconds=[5, 15, 30])
def descargar_mes(periodo: str, destino: Path) -> Path:
    logger = get_run_logger()
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".parquet.part")
    logger.info("Descargando %s", nombre_archivo(periodo))
    urlretrieve(f"{URL_BASE}/{nombre_archivo(periodo)}", temporal)
    temporal.replace(destino)
    return destino


@task
def asegurar_datos(directorio: Path) -> dict[str, Path]:
    logger = get_run_logger()
    rutas = {}
    for mes, periodo in MESES.items():
        ruta = directorio / nombre_archivo(periodo)
        if ruta.exists():
            logger.info("%s ya existe; no se descarga", ruta.name)
        else:
            descargar_mes(periodo, ruta)
        rutas[mes] = ruta
    return rutas


@task
def preparar_y_validar(ruta: Path) -> pd.DataFrame:
    viajes = pd.read_parquet(ruta)
    faltantes = [c for c in COLUMNAS_CRUDAS if c not in viajes.columns]
    if faltantes:
        raise ContratoInvalido(f"{ruta.name}: faltan columnas {faltantes}")
    for columna in ["lpep_pickup_datetime", "lpep_dropoff_datetime"]:
        if not pd.api.types.is_datetime64_any_dtype(viajes[columna]):
            raise ContratoInvalido(f"{ruta.name}: {columna} no es datetime")

    viajes[TARGET] = (
        viajes["lpep_dropoff_datetime"] - viajes["lpep_pickup_datetime"]
    ).dt.total_seconds() / 60
    viajes["distancia_km"] = viajes["trip_distance"] * 1.60934
    viajes["pasajeros"] = viajes["passenger_count"]
    viajes["hora_recoleccion"] = viajes["lpep_pickup_datetime"].dt.hour
    viajes["zona_origen"] = viajes["PULocationID"]
    viajes["zona_destino"] = viajes["DOLocationID"]

    validos = (
        viajes[TARGET].between(1, 60)
        & viajes["distancia_km"].between(0.1, 100)
        & viajes["pasajeros"].between(1, 6)
        & viajes["zona_origen"].gt(0)
        & viajes["zona_destino"].gt(0)
    )
    preparados = viajes.loc[validos, FEATURES + [TARGET]].dropna().copy()
    enteras = ["pasajeros", "hora_recoleccion", "zona_origen", "zona_destino"]
    preparados[enteras] = preparados[enteras].astype(int)

    if preparados.empty:
        raise ContratoInvalido(f"{ruta.name}: no quedan filas válidas")
    if not preparados["hora_recoleccion"].between(0, 23).all():
        raise ContratoInvalido(f"{ruta.name}: hora_recoleccion fuera de 0-23")
    get_run_logger().info("%s: %d filas válidas", ruta.name, len(preparados))
    return preparados


@task
def dividir_marzo(marzo: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    return train_test_split(marzo, test_size=0.2, random_state=SEMILLA)


# --- Modelos -----------------------------------------------------------------

def construir_pipeline(estimador) -> Pipeline:
    preprocesamiento = ColumnTransformer(
        [("zonas", OneHotEncoder(handle_unknown="ignore"), FEATURES_CATEGORICAS)],
        remainder="passthrough",
    )
    return Pipeline([("preprocesamiento", preprocesamiento), ("modelo", estimador)])


def construir_estimador(familia: str, params: dict):
    if familia == "linear_regression":
        return LinearRegression(**params)
    if familia == "random_forest":
        return RandomForestRegressor(random_state=SEMILLA, n_jobs=-1, **params)
    if familia == "gradient_boosting":
        return GradientBoostingRegressor(random_state=SEMILLA, **params)
    raise ValueError(f"Familia no reconocida: {familia}")


def espacio_lineal(trial: optuna.trial.Trial) -> dict:
    return {"fit_intercept": trial.suggest_categorical("fit_intercept", [True, False])}


def espacio_bosque(trial: optuna.trial.Trial) -> dict:
    return {
        "n_estimators": trial.suggest_int("n_estimators", 50, 150, step=50),
        "max_depth": trial.suggest_int("max_depth", 8, 16, step=4),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 3, 7, step=2),
    }


def espacio_gradient_boosting(trial: optuna.trial.Trial) -> dict:
    return {
        "n_estimators": trial.suggest_int("n_estimators", 50, 200, step=50),
        "learning_rate": trial.suggest_float("learning_rate", 0.03, 0.2, log=True),
        "max_depth": trial.suggest_int("max_depth", 2, 4),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 3, 7, step=2),
    }


ESTUDIOS = {
    "linear_regression": (
        espacio_lineal, lambda: GridSampler({"fit_intercept": [True, False]}), 2,
    ),
    "random_forest": (
        espacio_bosque, lambda: TPESampler(seed=SEMILLA, n_startup_trials=3), 8,
    ),
    "gradient_boosting": (
        espacio_gradient_boosting, lambda: TPESampler(seed=SEMILLA, n_startup_trials=3), 8,
    ),
}


def crear_objetivo(familia: str, espacio, train: pd.DataFrame, validacion: pd.DataFrame):
    def objetivo(trial: optuna.trial.Trial) -> float:
        pipeline = construir_pipeline(construir_estimador(familia, espacio(trial)))
        pipeline.fit(train[FEATURES], train[TARGET])
        return root_mean_squared_error(validacion[TARGET], pipeline.predict(validacion[FEATURES]))

    return objetivo


@task(task_run_name="hpo-{familia}")
def ajustar_familia(familia: str, train: pd.DataFrame, validacion: pd.DataFrame) -> dict:
    espacio, sampler, n_trials = ESTUDIOS[familia]
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    estudio = optuna.create_study(direction="minimize", sampler=sampler())
    estudio.optimize(crear_objetivo(familia, espacio, train, validacion), n_trials=n_trials)
    get_run_logger().info(
        "%s: mejor trial %d, RMSE tuning %.3f, %s",
        familia, estudio.best_trial.number, estudio.best_value, estudio.best_params,
    )
    return {
        "params": dict(estudio.best_params),
        "tuning_rmse": round(estudio.best_value, 4),
        "best_trial": estudio.best_trial.number,
        "n_trials": n_trials,
    }


@task
def guardar_parametros(mejores: dict) -> Path:
    RUTA_PARAMETROS.write_text(json.dumps(mejores, indent=2) + "\n", encoding="utf-8")
    return RUTA_PARAMETROS


@task
def cargar_parametros() -> dict:
    if not RUTA_PARAMETROS.exists():
        raise FileNotFoundError(f"No existe {RUTA_PARAMETROS.name}; corre con hacer_tuning=True")
    mejores = json.loads(RUTA_PARAMETROS.read_text(encoding="utf-8"))
    faltantes = [f for f in FAMILIAS if f not in mejores]
    if faltantes:
        raise ContratoInvalido(f"{RUTA_PARAMETROS.name}: faltan familias {faltantes}")
    get_run_logger().info("Reutilizando parámetros de %s", RUTA_PARAMETROS.name)
    return mejores


@task(task_run_name="final-{familia}")
def entrenar_y_evaluar(familia: str, params: dict, marzo: pd.DataFrame, abril: pd.DataFrame) -> dict:
    pipeline = construir_pipeline(construir_estimador(familia, params))
    inicio = perf_counter()
    pipeline.fit(marzo[FEATURES], marzo[TARGET])
    tiempo = perf_counter() - inicio
    rmse = root_mean_squared_error(abril[TARGET], pipeline.predict(abril[FEATURES]))
    get_run_logger().info("%s: RMSE abril %.3f min, entrenamiento %.2f s", familia, rmse, tiempo)
    return {
        "familia": familia, "params": params, "pipeline": pipeline,
        "rmse": rmse, "tiempo": tiempo, "ejemplo": abril[FEATURES].head(5),
    }


@task(retries=2, retry_delay_seconds=10, task_run_name="registrar-{resultado[familia]}")
def registrar_modelo(resultado: dict, origen_parametros: str) -> str:
    familia = resultado["familia"]
    pipeline = resultado["pipeline"]
    ejemplo = resultado["ejemplo"]
    with mlflow.start_run(run_name=f"{familia.replace('_', '-')}-final"):
        mlflow.log_params(resultado["params"])
        mlflow.log_param("params_source", origen_parametros)
        mlflow.log_metrics({
            "validation_rmse": resultado["rmse"],
            "training_time_seconds": resultado["tiempo"],
        })
        mlflow.set_tags({
            **COMUN, "role": "family-final", "model_family": familia,
            "training_period": "2026-03", "validation_period": "2026-04",
        })
        info = mlflow.sklearn.log_model(
            pipeline,
            name="model",
            input_example=ejemplo,
            signature=infer_signature(ejemplo, pipeline.predict(ejemplo)),
            registered_model_name=NOMBRE_MODELO,
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_PICKLE,
        )
    return str(info.registered_model_version)


@task(retries=2, retry_delay_seconds=10)
def asignar_aliases(resultados: list[dict], versiones: list[str]) -> list[dict]:
    cliente = MlflowClient()
    ranking = sorted(
        [{**r, "version": v} for r, v in zip(resultados, versiones)], key=lambda r: r["rmse"]
    )
    logger = get_run_logger()
    tabla = []
    for posicion, alias in zip(ranking, ALIASES):
        version = posicion["version"]
        cliente.set_registered_model_alias(NOMBRE_MODELO, alias, version)
        cliente.set_model_version_tag(NOMBRE_MODELO, version, "model_family", posicion["familia"])
        cliente.set_model_version_tag(NOMBRE_MODELO, version, "validation_rmse", f"{posicion['rmse']:.4f}")
        cliente.set_model_version_tag(NOMBRE_MODELO, version, "validation_period", "2026-04")
        logger.info(
            "%-10s %-18s v%s RMSE abril=%.3f min tiempo=%.2f s",
            alias, posicion["familia"], version, posicion["rmse"], posicion["tiempo"],
        )
        tabla.append({
            "alias": alias, "familia": posicion["familia"], "version": version,
            "rmse_abril": round(posicion["rmse"], 4), "tiempo_s": round(posicion["tiempo"], 2),
        })
    return tabla


# --- Flow --------------------------------------------------------------------

@flow(name="nyc-taxi-entrenamiento", log_prints=True)
def pipeline_entrenamiento(hacer_tuning: bool = False, directorio_datos: str = "data/nyc-taxi"):
    load_dotenv(RAIZ / ".env", override=True)
    if not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"):
        raise ValueError("Faltan DATABRICKS_HOST o DATABRICKS_TOKEN en .env")

    rutas = asegurar_datos(RAIZ / directorio_datos)
    marzo = preparar_y_validar.with_options(task_run_name="preparar-marzo")(rutas["marzo"])
    abril = preparar_y_validar.with_options(task_run_name="preparar-abril")(rutas["abril"])

    if hacer_tuning:
        marzo_train, marzo_tuning = dividir_marzo(marzo)
        mejores = {f: ajustar_familia(f, marzo_train, marzo_tuning) for f in FAMILIAS}
        guardar_parametros(mejores)
    else:
        mejores = cargar_parametros()
    origen = "hpo" if hacer_tuning else "mejores-parametros.json"

    resultados = [entrenar_y_evaluar(f, mejores[f]["params"], marzo, abril) for f in FAMILIAS]

    mlflow.set_tracking_uri("databricks")
    mlflow.set_registry_uri("databricks-uc")
    mlflow.set_experiment(EXPERIMENTO)
    versiones = [registrar_modelo(r, origen) for r in resultados]
    return asignar_aliases(resultados, versiones)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--hacer-tuning", action="store_true")
    parser.add_argument("--directorio-datos", default="data/nyc-taxi")
    argumentos = parser.parse_args()
    pipeline_entrenamiento(
        hacer_tuning=argumentos.hacer_tuning, directorio_datos=argumentos.directorio_datos
    )
