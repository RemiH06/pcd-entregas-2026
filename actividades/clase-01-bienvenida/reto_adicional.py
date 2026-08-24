"""Reto adicional de funciones y colecciones. Resolver sin ayuda de IA."""

VIAJES = [
    {
        "origen": "Centro",
        "destino": "Chapultepec",
        "distancia_km": 3.2,
    },
    {
        "origen": "ITESO",
        "destino": "Centro",
        "distancia_km": 12.5,
    },
    {
        "origen": "Tlaquepaque",
        "destino": "Aeropuerto",
        "distancia_km": 15.8,
    },
]


def clasificar_distancia(distancia_km: float) -> str:
    """Clasifica un viaje como corto, medio o largo."""
    # TODO 1: producir ValueError si la distancia no es positiva.
    if distancia_km <= 0:
        raise ValueError("La distancia debe ser positiva")
    # TODO 2: devolver "corto" hasta 5 km, "medio" hasta 12 km y "largo" para distancias mayores.
    if distancia_km <= 5:
        return "corto"
    elif distancia_km <= 12:
        return "medio"
    else:
        return "largo"


def resumir_viajes(viajes: list[dict]) -> list[dict]:
    """Crea un resumen nuevo sin modificar la lista recibida."""
    # TODO 3: construir una lista de diccionarios con estas claves:
    # ruta, categoria y duracion_estimada_min.
    # Duración = 4 minutos por km + 2 minutos fijos, redondeada
    # a una cifra decimal.
    resumen = []
    for viaje in viajes:
        ruta = f"{viaje['origen']} - {viaje['destino']}"
        categoria = clasificar_distancia(viaje['distancia_km'])
        duracion = (4 * viaje['distancia_km']) + 2
        duracion_redondeada = round(duracion, 1)
        
        nuevo_viaje = {
            'ruta': ruta,
            'categoria': categoria,
            'duracion_estimada_min': duracion_redondeada
        }
        resumen.append(nuevo_viaje)
    return resumen


# TODO 4: agrega a VIAJES un registro inventado por ti.

VIAJES.append({
    "origen": "Zapopan",
    "destino": "Guadalajara",
    "distancia_km": 6.9,
})


resumen = resumir_viajes(VIAJES)
for viaje in resumen:
    print(
        f"{viaje['ruta']} | {viaje['categoria']} | "
        f"{viaje['duracion_estimada_min']} min"
    )