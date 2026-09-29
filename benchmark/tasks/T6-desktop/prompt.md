# T6 — Aplicación de escritorio o CLI simple

Implementa en **{language}** (runtime: `{runtime}`) una utilidad CLI con un
almacén local de entradas (nombre + valor numérico). Debe incluir un script
`run.sh` que construya (si es necesario) y ejecute el programa pasándole los
argumentos recibidos. Comandos que debe soportar:

- `run.sh init` — crea el fichero de datos (vacío). Sale con 0.
- `run.sh add <name> <value>` — añade una entrada `{name, value}`.
- `run.sh list --format json` — imprime por stdout JSON:
  `{ "entries": [ { "name": "...", "value": N }, ... ] }`.

La salida JSON debe ser exactamente ese objeto (sin texto adicional). Incluye
`README.md` con instrucciones. Escribe cada fichero en un bloque de código con
su ruta.
