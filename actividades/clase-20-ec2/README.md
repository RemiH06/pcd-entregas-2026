# Clase 20: despliegue en EC2 con Docker Compose

Aplicación de dos servicios que estima la duración de un viaje Green Taxi:

- `api/`: FastAPI. Carga una vez la versión del modelo que apunta el alias en el Registry de Databricks y expone `GET /health` y `POST /api/v1/predicciones`.
- `ui/`: Streamlit. Captura las cinco features y consulta la API desde su proceso Python.

Ambos servicios usan `network_mode: host`. La API escucha en `127.0.0.1:8000`, sólo dentro del servidor; Streamlit escucha en `0.0.0.0:8501` y el grupo de seguridad decide quién puede entrar. Por eso `API_URL` conserva `127.0.0.1` también en EC2.

## Variables

Se leen de un único `.env` junto a `docker-compose.yaml`. Créalo desde la plantilla y completa los valores en el servidor; nunca se versiona.

| Variable | Uso |
|---|---|
| `DATABRICKS_HOST`, `DATABRICKS_TOKEN` | Acceso al workspace. |
| `MLFLOW_TRACKING_URI`, `MLFLOW_REGISTRY_URI` | `databricks` y `databricks-uc`. |
| `MODELO_REGISTRADO`, `ALIAS_MODELO` | Modelo de Unity Catalog y alias a cargar. |
| `API_URL` | Endpoint que consulta la UI: `http://127.0.0.1:8000/api/v1/predicciones`. |

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

## Arrancar y detener

Desde esta carpeta:

```bash
sudo docker compose config --quiet
sudo docker compose up --build
```

Espera `Application startup complete` en los logs de la API. Para detener: `Ctrl+C` y después `sudo docker compose down`.

## Comprobar una predicción

Dentro del servidor:

```bash
curl http://127.0.0.1:8000/health
```

Debe responder `{"status":"ok","version_api":"v1"}`. Después abre `http://IP_PUBLICA:8501` desde una computadora autorizada, captura distancia 4.2 km, 2 pasajeros, hora 18, zona de origen 75 y zona de destino 42, y pulsa **Estimar duración**. La pantalla muestra los minutos estimados junto con el modelo, el alias y la versión cargada.
