# Tarea 2 — De funciones de viajes a una API local

## Cliente y servidor

- **Servidor**: `main.py` expone una app FastAPI. Cada endpoint reutiliza las funciones de `viajes.py` (`estimar_duracion`, `resumir_viajes`, `VIAJES`); ningún endpoint recalcula las fórmulas.
- **Cliente**: cualquier cliente HTTP (`curl`, el navegador en `/docs`, o Postman) consultando `http://127.0.0.1:8000`.

## Ejecución

Desde la raíz del repositorio:

```bash
uv sync --locked
```

Desde esta carpeta:

```bash
cd tareas/tarea-02-api-ambiente-uv
uv run fastapi dev
```

## Contrato

| Solicitud | Respuesta |
| --- | --- |
| `GET /` | JSON con un mensaje que identifica la API local de viajes. |
| `GET /api/v1/viajes` | JSON con la clave `viajes`: el resumen de `VIAJES` (cada viaje original + `duracion_estimada_min`). |
| `GET /api/v1/duracion/{distancia_km}?pasajeros=1&fin_de_semana=false` | JSON con `distancia_km` (float), `pasajeros` (int), `fin_de_semana` (bool) y `duracion_estimada_min`. |

## Verificación

Servidor corriendo en `http://127.0.0.1:8001` (puerto de prueba), probado con `curl -i`:

**GET / → 200**
```
HTTP/1.1 200 OK
{"mensaje":"API local de viajes del curso PCD"}
```
Confirma que la app está activa y responde el mensaje de identificación.

**GET /api/v1/viajes → 200**
```
HTTP/1.1 200 OK
{"viajes":[
  {"origen":"Centro","destino":"Chapultepec","distancia_km":3.2,"pasajeros":1,"fin_de_semana":false,"duracion_estimada_min":14.8},
  {"origen":"ITESO","destino":"Centro","distancia_km":12.5,"pasajeros":3,"fin_de_semana":false,"duracion_estimada_min":55.0},
  {"origen":"Tlaquepaque","destino":"Aeropuerto","distancia_km":15.8,"pasajeros":2,"fin_de_semana":true,"duracion_estimada_min":58.7}
]}
```
El endpoint devuelve el resumen de los tres viajes de `VIAJES`, cada uno con su `duracion_estimada_min` calculada por `resumir_viajes`.

**GET /api/v1/duracion/12.5?pasajeros=3&fin_de_semana=false → 200, duración 55.0**
```
HTTP/1.1 200 OK
{"distancia_km":12.5,"pasajeros":3,"fin_de_semana":false,"duracion_estimada_min":55.0}
```
12.5 km × 4 + 2 = 52 min; +3 min por llevar más de 2 pasajeros = 55.0 min (sin descuento de fin de semana).

**GET /ruta-inexistente → 404**
```
HTTP/1.1 404 Not Found
{"detail":"Not Found"}
```
Ruta no registrada en la app; FastAPI responde con el 404 estándar.

**GET /api/v1/duracion/no-es-numero → 422**
```
HTTP/1.1 422 Unprocessable Entity
{"detail":[{"type":"float_parsing","loc":["path","distancia_km"], ...}]}
```
`distancia_km` está tipado como `float` en la ruta; un valor no numérico falla la validación automática de FastAPI.

**GET /docs → 200**: la documentación interactiva (Swagger UI) generada automáticamente por FastAPI carga correctamente y lista los tres endpoints.
