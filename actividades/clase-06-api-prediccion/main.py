import pickle
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

RAIZ = Path(__file__).resolve().parents[2]
RUTA_MODELO = RAIZ / "artifacts/nyc-taxi/modelo-duracion.pkl"
with RUTA_MODELO.open("rb") as archivo:
    artefacto = pickle.load(archivo)


class SolicitudPrediccion(BaseModel):
    distancia_km: float = Field(gt=0, le=100)
    pasajeros: int = Field(ge=1, le=6)
    hora_recoleccion: int = Field(ge=0, le=23)
    zona_origen: int = Field(ge=1, le=265)
    zona_destino: int = Field(ge=1, le=265)


class RespuestaPrediccion(BaseModel):
    duracion_estimada_minutos: float
    version_modelo: str


app = FastAPI(title="API de duración de viajes Green Taxi")


@app.post("/predicciones", response_model=RespuestaPrediccion)
def crear_prediccion(solicitud: SolicitudPrediccion) -> RespuestaPrediccion:
    entrada = pd.DataFrame([solicitud.model_dump()])[artefacto["features"]]
    duracion = float(artefacto["modelo"].predict(entrada)[0])
    return RespuestaPrediccion(
        duracion_estimada_minutos=round(duracion, 1),
        version_modelo=artefacto["version"],
    )