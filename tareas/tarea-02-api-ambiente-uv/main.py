"""API local de viajes construida con FastAPI."""

from fastapi import FastAPI

from viajes import VIAJES, estimar_duracion, resumir_viajes

app = FastAPI(title="API local de viajes")


@app.get("/")
def inicio() -> dict[str, str]:
    return {"mensaje": "API local de viajes del curso PCD"}


@app.get("/api/v1/viajes")
def listar_viajes() -> dict[str, list[dict]]:
    return {"viajes": resumir_viajes(VIAJES)}


@app.get("/api/v1/duracion/{distancia_km}")
def duracion(distancia_km: float, pasajeros: int = 1, fin_de_semana: bool = False) -> dict:
    return {
        "distancia_km": distancia_km,
        "pasajeros": pasajeros,
        "fin_de_semana": fin_de_semana,
        "duracion_estimada_min": estimar_duracion(distancia_km, pasajeros, fin_de_semana),
    }
