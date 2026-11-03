import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=False)

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000/api/v1/predicciones",
)

st.set_page_config(page_title="Duración de viajes Green Taxi")
st.title("Duración estimada de un viaje Green Taxi")
st.write("Captura las cinco características disponibles antes del viaje.")

with st.sidebar:
    st.header("Datos del viaje")
    distancia_km = st.number_input(
        "Distancia aproximada (km)",
        min_value=0.1,
        max_value=100.0,
        value=4.2,
        step=0.1,
        format="%.1f",
        help="Distancia disponible antes de iniciar el viaje.",
    )
    pasajeros = st.number_input("Número de pasajeros", min_value=1, max_value=6, value=2, step=1)
    hora_recoleccion = st.number_input(
        "Hora de recolección", min_value=0, max_value=23, value=18, step=1
    )
    zona_origen = st.number_input("Zona de origen", min_value=1, max_value=265, value=75, step=1)
    zona_destino = st.number_input("Zona de destino", min_value=1, max_value=265, value=42, step=1)

entrada = {
    "distancia_km": float(distancia_km),
    "pasajeros": int(pasajeros),
    "hora_recoleccion": int(hora_recoleccion),
    "zona_origen": int(zona_origen),
    "zona_destino": int(zona_destino),
}

if st.button("Estimar duración", type="primary"):
    try:
        respuesta = httpx.post(API_URL, json=entrada, timeout=10.0)
        respuesta.raise_for_status()
    except httpx.HTTPStatusError as error:
        st.error(f"La API rechazó la solicitud: {error.response.text}")
    except httpx.RequestError:
        st.error("No fue posible conectarse con la API de predicción.")
    else:
        resultado = respuesta.json()
        st.metric(
            "Duración estimada",
            f"{resultado['duracion_estimada_minutos']:.1f} min",
        )
        st.caption(
            f"Modelo: {resultado['modelo']} · alias: {resultado['alias']} · "
            f"versión: {resultado['version']}"
        )
