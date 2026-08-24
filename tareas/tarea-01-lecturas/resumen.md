# Tarea 1 — Primeras perspectivas sobre MLOps 

### Lecturas
- AWS [https://aws.amazon.com/what-is/mlops/]
- RedHat [https://www.redhat.com/en/topics/ai/what-is-mlops]
- Microsoft [https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/mlops-maturity-model]
- MLOps.org [https://ml-ops.org/]

---
## Definición

MLOps (Machine Learning Operations) es un conjunto de prácticas que busca unificar el desarrollo (Dev) y la operación (Ops) de sistemas de Machine Learning. Automatiza y estandariza todo el ciclo de vida de un modelo. Desde la preparación de datos, el entrenamiento y la validación, hasta el despliegue, monitoreo y reentrenamiento continuo. Su objetivo es hacer que los modelos de ML sean reproducibles, testeables y evolutivos, aplicando principios de DevOps, pero adaptados a las particularidades de los datos y los modelos.

---
## Síntesis

MLOps gestiona la complejidad del ciclo de vida del ML, que incluye datos, modelos y código. Sus pilares fundamentales son:
- **Versionado**: Control de versiones de datos, código y modelos para garantizar reproducibilidad y auditoría.
- **Automatización**: Automatizar los pipelines de datos, entrenamiento, pruebas y despliegue.
- **Integración y Despliegue Continuos (CI/CD)**: Extender las prácticas de CI/CD para probar y desplegar no solo código, sino también datos y modelos.
- **Monitoreo y Gobernanza**: Supervisar el rendimiento del modelo en producción (deriva de datos o concepto) y gestionar el cumplimiento, la seguridad y la colaboración entre equipos.

La implementación de MLOps suele describirse en niveles de madurez, que van desde un proceso completamente manual (Nivel 0) hasta un sistema automatizado y auto-optimizable (Nivel 4).

---
## Coincidencias y Diferencias

#### Coincidencias:
1. Definición y Propósito: Las cuatro fuentes coinciden en que MLOps es la aplicación de principios DevOps al ML para automatizar y estandarizar el ciclo de vida del modelo, mejorando la colaboración y la velocidad de despliegue.
2. Beneficios Clave: Todas destacan beneficios como la reproducibilidad, la automatización de tareas manuales, la integración continua (CI/CD/CD/CT) y la monitorización para detectar y corregir la deriva del modelo.
3. Niveles de Madurez: AWS, RedHat y Microsoft presentan modelos de madurez con tres niveles (AWS, RedHat) o cinco (Microsoft), donde el nivel más alto representa la automatización completa del ciclo de vida.

Diferencias:
1. Énfasis y Enfoque: MLOps.org ofrece una visión más conceptual y centrada en la ingeniería de software. Contrasta con AWS, RedHat y Microsoft, que tienen un enfoque más práctico y orientado a sus respectivas plataformas en la nube (SageMaker, OpenShift, Azure).
2. Estructura de Madurez:
    - AWS y RedHat simplifican la madurez en tres niveles (0: Manual, 1: Pipeline Automatizado, 2: CI/CD Completo).
    - Microsoft detalla cinco niveles (0: Sin MLOps, 1: DevOps sin MLOps, 2: Entrenamiento Automatizado, 3: Despliegue Automatizado, 4: Operaciones Automatizadas completas), ofreciendo una granularidad más fina que incluye aspectos de cultura y procesos.
3. Contexto DevOps vs. MLOps: RedHat explica explícitamente cómo el testing y el despliegue difieren en MLOps (se testean datos y modelos, no solo código), mientras que las otras fuentes asumen esta diferencia.


---
## Ejemplo de problema que MLOps busca resolver

Una empresa de comercio electrónico despliega un modelo para recomendar productos. Inicialmente, un científico de datos entrena el modelo manualmente y lo entrega al equipo de ingeniería para desplegarlo (un problema, proceso manual y desconectado).

Con el tiempo, el comportamiento de los clientes cambia (por una temporada de rebajas o algún caso esquina no contempaldo). El rendimiento del modelo baja sin que el equipo lo note (otro problema, falta de monitoreo). Cuando se dan cuenta, el científico reentrena el modelo, pero el proceso de pruebas, validación y despliegue es nuevamente manual y lento, tomando semanas (problema, despliegue lento y poco fiable).

MLOps resuelve esto automatizando un pipeline que:
1. Monitorea continuamente el rendimiento del modelo y los datos de entrada.
2. Al detectar una caída en el rendimiento (deriva), activa automáticamente el reentrenamiento del modelo con datos nuevos.
3. Ejecuta pruebas automatizadas del modelo recién entrenado.
4. Si pasa las pruebas, lo despliega automáticamente en producción mediante un CI/CD sin intervención manual, reduciendo el tiempo de inactividad del modelo a minutos u horas.

---
## Reflexión

MLOps surge como una respuesta necesaria a la creciente complejidad y los fallos en la implementación de proyectos de Machine Learning. La lectura de las cuatro fuentes deja claro que MLOps no puede reducirse a solo una herramienta, sino que es toda una disciplina cultural y técnica que busca "industrializar" el ML, haciéndolo fiable, escalable y rentable.

Un punto clave es cómo todas las fuentes coinciden en que el principal impulsor de MLOps es el cambio. Los datos cambian, los objetivos de negocio cambian, y el modelo debe adaptarse. La capacidad de gestionar este cambio de forma sistemática y automatizada es lo que diferencia a una organización que experimenta de una que realmente obtiene valor del ML.

Para mí, el gran valor de adoptar un modelo de madurez es que proporciona una hoja de ruta pragmática. Permite a las organizaciones no sentirse abrumadas por la idea de la automatización total desde el día uno, sino comenzar por resolver sus cuellos de botella más inmediatos (como automatizar el reentrenamiento) e ir evolucionando incrementalmente hacia un sistema más completo y robusto. La meta no es solo "automatizar por automatizar", sino construir un sistema que genere confianza y permita iterar sobre modelos predictivos con la misma agilidad que se itera sobre el código de una aplicación tradicional.
