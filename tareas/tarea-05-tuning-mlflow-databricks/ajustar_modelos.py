import os
from pathlib import Path
from time import perf_counter

import mlflow
import mlflow.data
import mlflow.sklearn
import optuna
import pandas as pd
from dotenv import load_dotenv
from mlflow import MlflowClient
from mlflow.models import infer_signature
from optuna.samplers import GridSampler, TPESampler
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

load_dotenv(override=True)
if not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"):
    raise ValueError("Faltan DATABRICKS_HOST o DATABRICKS_TOKEN en .env")

RAIZ = Path(__file__).resolve().parents[2]
EXPERIMENTO = "/Shared/pcd-otono-2026-tarea-05-nyc-taxi"
CATALOGO = "workspace"
NOMBRE_MODELO = f"{CATALOGO}.default.nyc_taxi_trip_duration_tarea_05"
ALIASES = ["champion", "challenger", "candidate"]
SEMILLA = 42
COMUN = {"course": "proyecto-ciencia-datos", "term": "otono-2026", "task": "05"}

FEATURES_NUMERICAS = ["distancia_km", "pasajeros", "hora_recoleccion"]
FEATURES_CATEGORICAS = ["zona_origen", "zona_destino"]
FEATURES = FEATURES_NUMERICAS + FEATURES_CATEGORICAS
TARGET = "duracion_minutos"


def preparar_viajes(ruta: Path) -> pd.DataFrame:
    viajes = pd.read_parquet(ruta)
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
    return preparados


marzo = preparar_viajes(RAIZ / "data/nyc-taxi/green_tripdata_2026-03.parquet")
abril = preparar_viajes(RAIZ / "data/nyc-taxi/green_tripdata_2026-04.parquet")
marzo_train, marzo_tuning = train_test_split(marzo, test_size=0.2, random_state=SEMILLA)

DATASET_TRAIN = mlflow.data.from_pandas(
    marzo_train, source="data/nyc-taxi/green_tripdata_2026-03.parquet", targets=TARGET,
    name="green-taxi-2026-03-train-interno",
)
DATASET_TUNING = mlflow.data.from_pandas(
    marzo_tuning, source="data/nyc-taxi/green_tripdata_2026-03.parquet", targets=TARGET,
    name="green-taxi-2026-03-validacion-tuning",
)
DATASET_MARZO = mlflow.data.from_pandas(
    marzo, source="data/nyc-taxi/green_tripdata_2026-03.parquet", targets=TARGET,
    name="green-taxi-2026-03-completo",
)
DATASET_ABRIL = mlflow.data.from_pandas(
    abril, source="data/nyc-taxi/green_tripdata_2026-04.parquet", targets=TARGET,
    name="green-taxi-2026-04-final",
)


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


def crear_objetivo(familia: str, espacio):
    def objetivo(trial: optuna.trial.Trial) -> float:
        params = espacio(trial)
        pipeline = construir_pipeline(construir_estimador(familia, params))
        inicio = perf_counter()
        pipeline.fit(marzo_train[FEATURES], marzo_train[TARGET])
        tiempo = perf_counter() - inicio
        rmse = root_mean_squared_error(
            marzo_tuning[TARGET], pipeline.predict(marzo_tuning[FEATURES])
        )
        with mlflow.start_run(run_name=f"trial-{trial.number:03d}", nested=True):
            mlflow.log_params(params)
            mlflow.log_metrics({"tuning_rmse": rmse, "training_time_seconds": tiempo})
            mlflow.set_tags({**COMUN, "role": "tuning-trial", "model_family": familia})
        return rmse

    return objetivo


def entrenar_final(familia: str, params: dict) -> dict:
    pipeline = construir_pipeline(construir_estimador(familia, params))
    inicio = perf_counter()
    pipeline.fit(marzo[FEATURES], marzo[TARGET])
    tiempo = perf_counter() - inicio
    rmse = root_mean_squared_error(abril[TARGET], pipeline.predict(abril[FEATURES]))
    ejemplo = abril[FEATURES].head(5)
    slug = familia.replace("_", "-")
    with mlflow.start_run(run_name=f"{slug}-final", nested=True) as final:
        mlflow.log_input(DATASET_MARZO, context="training")
        mlflow.log_input(DATASET_ABRIL, context="final-validation")
        mlflow.log_params(params)
        mlflow.log_metrics({"validation_rmse": rmse, "training_time_seconds": tiempo})
        mlflow.set_tags({**COMUN, "role": "family-final", "model_family": familia})
        info = mlflow.sklearn.log_model(
            pipeline,
            name="model",
            input_example=ejemplo,
            signature=infer_signature(ejemplo, pipeline.predict(ejemplo)),
            registered_model_name=NOMBRE_MODELO,
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_PICKLE,
        )
    return {
        "familia": familia,
        "version": str(info.registered_model_version),
        "rmse": rmse,
        "tiempo": tiempo,
        "params": params,
    }


def estudiar_familia(familia, espacio, sampler, n_trials: int, optimizador: str, extra: dict):
    estudio = optuna.create_study(direction="minimize", sampler=sampler)
    slug = familia.replace("_", "-")
    with mlflow.start_run(run_name=f"tuning-{slug}"):
        mlflow.log_input(DATASET_TRAIN, context="training")
        mlflow.log_input(DATASET_TUNING, context="tuning-validation")
        mlflow.log_params(
            {"optimizer": optimizador, "n_trials": n_trials, "objective_metric": "tuning_rmse", **extra}
        )
        mlflow.set_tags({**COMUN, "role": "tuning-study", "model_family": familia})
        estudio.optimize(crear_objetivo(familia, espacio), n_trials=n_trials)
        mejor = estudio.best_trial
        mlflow.log_param("best_trial_number", mejor.number)
        mlflow.log_params({f"best_{clave}": valor for clave, valor in mejor.params.items()})
        mlflow.log_metric("best_tuning_rmse", estudio.best_value)
        return entrenar_final(familia, dict(mejor.params))


mlflow.set_tracking_uri("databricks")
mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment(EXPERIMENTO)

resultados = [
    estudiar_familia(
        "linear_regression", espacio_lineal, GridSampler({"fit_intercept": [True, False]}),
        n_trials=2, optimizador="optuna-grid", extra={"sampler": "GridSampler"},
    ),
    estudiar_familia(
        "random_forest", espacio_bosque, TPESampler(seed=SEMILLA, n_startup_trials=3),
        n_trials=8, optimizador="optuna-tpe",
        extra={"sampler": "TPESampler", "sampler_seed": SEMILLA, "sampler_startup_trials": 3},
    ),
    estudiar_familia(
        "gradient_boosting", espacio_gradient_boosting, TPESampler(seed=SEMILLA, n_startup_trials=3),
        n_trials=8, optimizador="optuna-tpe",
        extra={"sampler": "TPESampler", "sampler_seed": SEMILLA, "sampler_startup_trials": 3},
    ),
]

cliente = MlflowClient()
resultados.sort(key=lambda r: r["rmse"])
for resultado, alias in zip(resultados, ALIASES):
    cliente.set_registered_model_alias(NOMBRE_MODELO, alias, resultado["version"])
    cliente.set_model_version_tag(NOMBRE_MODELO, resultado["version"], "model_family", resultado["familia"])
    cliente.set_model_version_tag(NOMBRE_MODELO, resultado["version"], "validation_rmse", f"{resultado['rmse']:.4f}")
    cliente.set_model_version_tag(NOMBRE_MODELO, resultado["version"], "validation_period", "2026-04")

for resultado, alias in zip(resultados, ALIASES):
    print(f"{alias:10} {resultado['familia']:18} v{resultado['version']} RMSE abril={resultado['rmse']:.3f} min tiempo={resultado['tiempo']:.2f} s")

muestra = abril[FEATURES].head(5)
predicciones = pd.DataFrame(
    {
        alias: mlflow.sklearn.load_model(f"models:/{NOMBRE_MODELO}@{alias}").predict(muestra)
        for alias in ALIASES
    }
)
print(predicciones.round(1))
