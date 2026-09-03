import pickle
from pathlib import Path

from preparar_datos import FEATURES, FEATURES_CATEGORICAS, TARGET, preparar_viajes
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

RAIZ = Path(__file__).resolve().parents[2]
train = preparar_viajes(RAIZ / "data/nyc-taxi/green_tripdata_2026-03.parquet")
validacion = preparar_viajes(
    RAIZ / "data/nyc-taxi/green_tripdata_2026-04.parquet"
)
preprocesamiento = ColumnTransformer(
    [("zonas", OneHotEncoder(handle_unknown="ignore"), FEATURES_CATEGORICAS)],
    remainder="passthrough",
)
modelo = Pipeline(
    [("preprocesamiento", preprocesamiento), ("regresion", LinearRegression())]
).fit(train[FEATURES], train[TARGET])

predicciones = modelo.predict(validacion[FEATURES])
rmse = root_mean_squared_error(validacion[TARGET], predicciones)
artefacto = {
    "modelo": modelo,
    "features": FEATURES,
    "version": "green-taxi-2026-03-linear-zonas-1",
    "rmse_validacion": float(rmse),
}
ruta_modelo = RAIZ / "artifacts/nyc-taxi/modelo-duracion.pkl"
with ruta_modelo.open("wb") as archivo:
    pickle.dump(artefacto, archivo)

print(f"Entrenamiento: {len(train)} filas")
print(f"Validación: {len(validacion)} filas")
print(f"RMSE: {rmse:.2f} minutos")