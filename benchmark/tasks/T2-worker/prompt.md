# T2 — Worker con cola y concurrencia

Implementa en **{language}** (runtime: `{runtime}`) un worker que:

- Recibe trabajos por HTTP: `POST /jobs` encola un trabajo `{id, payload}` y
  responde 200/201/202.
- `POST /jobs/batch` encola varios trabajos de una vez (cuerpo `{jobs: [...]}`).
- Procesa los trabajos en paralelo con un grado de concurrencia configurable.
- `GET /jobs/{id}` devuelve `{id, status}` con `status` en `queued`/`in_progress`/`done`.
- `GET /stats` devuelve `{queued, in_progress, done}` como números.
- `GET /health` devuelve 200.

Incluye `README.md` con instrucciones para ejecutar el worker en el puerto 8005.
Escribe cada fichero en un bloque de código con su ruta.
