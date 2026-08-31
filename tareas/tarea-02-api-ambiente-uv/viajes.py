"""Funciones y datos de viajes para la Tarea 2."""

VIAJES = [
    {
        "origen": "Centro",
        "destino": "Chapultepec",
        "distancia_km": 3.2,
        "pasajeros": 1,
        "fin_de_semana": False,
    },
    {
        "origen": "ITESO",
        "destino": "Centro",
        "distancia_km": 12.5,
        "pasajeros": 3,
        "fin_de_semana": False,
    },
    {
        "origen": "Tlaquepaque",
        "destino": "Aeropuerto",
        "distancia_km": 15.8,
        "pasajeros": 2,
        "fin_de_semana": True,
    },
]


def estimar_duracion(distancia_km: float, pasajeros: int, fin_de_semana: bool) -> float:
    if distancia_km <= 0:
        raise ValueError("La distancia debe ser positiva")
    duracion = 4 * distancia_km + 2
    if pasajeros > 2:
        duracion += 3
    if fin_de_semana:
        duracion *= 0.9
    return round(duracion, 1)


def resumir_viajes(viajes: list[dict]) -> list[dict]:
    resumen = []
    for viaje in viajes:
        nuevo = dict(viaje)
        nuevo["duracion_estimada_min"] = estimar_duracion(
            viaje["distancia_km"], viaje["pasajeros"], viaje["fin_de_semana"]
        )
        resumen.append(nuevo)
    return resumen
