# T4 — Algoritmo CPU-intensivo

Implementa en **{language}** (runtime: `{runtime}`) un servicio HTTP que realice
cómputo intensivo:

- `POST /compute` recibe `{ "values": [int, ...] }` y devuelve
  `{ "sorted": [int, ...] }` con los valores ordenados de menor a mayor.
- `POST /hash` recibe `{ "input": "texto" }` y devuelve
  `{ "sha256": "<hex digest>" }` del input.
- `GET /health` devuelve 200.

La ordenación y el hash deben implementarse de forma eficiente. Incluye
`README.md` con instrucciones para ejecutar el servicio en el puerto 8005.
Escribe cada fichero en un bloque de código con su ruta.
