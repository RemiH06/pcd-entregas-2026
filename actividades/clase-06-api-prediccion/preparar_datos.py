from pathlib import Path

import pandas as pd

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