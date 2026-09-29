# T3 — Parseo y transformación de JSON/CSV grandes

Implementa en **{language}** (runtime: `{runtime}`) un servicio HTTP que
transforme datos de forma eficiente en CPU y memoria (streaming si es posible):

- `POST /transform` recibe `{ "records": [ {id, name, category, amount}, ... ] }`
  y devuelve `{ "count": N, "total_amount": S, "by_category": {...} }`.
- `POST /transform/csv` recibe un CSV en el cuerpo (`Content-Type: text/csv`)
  con cabecera `id,name,category,amount` y devuelve el mismo resultado.
- `GET /health` devuelve 200.

Incluye `README.md` con instrucciones para ejecutar el servicio en el puerto
8005. Escribe cada fichero en un bloque de código con su ruta.
