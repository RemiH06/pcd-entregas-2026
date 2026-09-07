import pickle
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

RAIZ = Path(__file__).resolve().parents[2]

with (RAIZ / "artifacts/nyc-taxi/modelo-duracion-lineal.pkl").open("rb") as archivo:
    artefacto_lineal = pickle.load(archivo)

with (RAIZ / "artifacts/nyc-taxi/modelo-duracion-bosque.pkl").open("rb") as archivo:
    artefacto_bosque = pickle.load(archivo)


class SolicitudPrediccion(BaseModel):
    distancia_km: float = Field(gt=0, le=100)
    pasajeros: int = Field(ge=1, le=6)
    hora_recoleccion: int = Field(ge=0, le=23)
    zona_origen: int = Field(ge=1, le=265)
    zona_destino: int = Field(ge=1, le=265)


class RespuestaPrediccion(BaseModel):
    duracion_estimada_minutos: float
    modelo: str
    version_modelo: str


app = FastAPI(title="API de comparación de modelos de duración")


def predecir(artefacto: dict, solicitud: SolicitudPrediccion, nombre_modelo: str) -> RespuestaPrediccion:
    entrada = pd.DataFrame([solicitud.model_dump()])[artefacto["features"]]
    duracion = float(artefacto["pipeline"].predict(entrada)[0])
    return RespuestaPrediccion(
        duracion_estimada_minutos=round(duracion, 1),
        modelo=nombre_modelo,
        version_modelo=artefacto["version"],
    )


@app.post("/predicciones/regresion-lineal", response_model=RespuestaPrediccion)
def predecir_regresion_lineal(solicitud: SolicitudPrediccion) -> RespuestaPrediccion:
    return predecir(artefacto_lineal, solicitud, "regresion-lineal")


@app.post("/predicciones/bosque-aleatorio", response_model=RespuestaPrediccion)
def predecir_bosque_aleatorio(solicitud: SolicitudPrediccion) -> RespuestaPrediccion:
    return predecir(artefacto_bosque, solicitud, "bosque-aleatorio")
