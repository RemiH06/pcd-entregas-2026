import pickle
import time
from pathlib import Path

from preparar_datos import FEATURES, FEATURES_CATEGORICAS, TARGET, preparar_viajes
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

RAIZ = Path(__file__).resolve().parents[2]
train = preparar_viajes(RAIZ / "data/nyc-taxi/green_tripdata_2026-03.parquet")
validacion = preparar_viajes(RAIZ / "data/nyc-taxi/green_tripdata_2026-04.parquet")

preprocesamiento = ColumnTransformer(
    [("zonas", OneHotEncoder(handle_unknown="ignore"), FEATURES_CATEGORICAS)],
    remainder="passthrough",
)
modelo = Pipeline(
    [("preprocesamiento", preprocesamiento), ("regresion", LinearRegression())]
)

inicio = time.perf_counter()
modelo.fit(train[FEATURES], train[TARGET])
tiempo_entrenamiento = time.perf_counter() - inicio

predicciones = modelo.predict(validacion[FEATURES])
rmse = root_mean_squared_error(validacion[TARGET], predicciones)

artefacto = {
    "pipeline": modelo,
    "features": FEATURES,
    "algoritmo": "regresion-lineal",
    "version": "green-taxi-2026-03-lineal-1",
    "rmse_validacion": float(rmse),
}
ruta_modelo = RAIZ / "artifacts/nyc-taxi/modelo-duracion-lineal.pkl"
ruta_modelo.parent.mkdir(parents=True, exist_ok=True)
with ruta_modelo.open("wb") as archivo:
    pickle.dump(artefacto, archivo)

tamano_mib = ruta_modelo.stat().st_size / (1024 * 1024)
print(f"entrenamiento: {tiempo_entrenamiento:.2f} s")
print(f"rmse validacion: {rmse:.2f} min")
print(f"artefacto: {ruta_modelo} ({tamano_mib:.2f} MiB)")
