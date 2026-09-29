# Benchmark de lenguajes para LLM + rendimiento

Estructura y harness del benchmark descrito en `../spec.md`.

## Uso rápido

1. Copiar configuración y fijar la API key:
   ```sh
   cp config.example.json config.json
   export OPENAI_API_KEY=...
   ```
2. Revisión de prompts sin llamar a la API:
   ```sh
   python3 harness/run_llm.py --config config.json --dry-run
   ```
3. Ejecutar una combinación concreta:
   ```sh
   python3 harness/run_llm.py --config config.json \
     --model gpt-4o --task T1-rest-crud --language python --reps 1
   ```
4. Contar tokens (tokenizador real del modelo):
   ```sh
   python3 harness/count_tokens.py gpt-4o languages/python/T1-rest-crud
   ```
5. Tests de aceptación (HTTP, independientes del lenguaje):
   ```sh
   harness/run_acceptance.sh T1-rest-crud http://127.0.0.1:8005
   ```
6. Prueba de carga (warm-up + sostenida + varias concurrencias):
   ```sh
   harness/run_load.sh T1-rest-crud python http://127.0.0.1:8005 k6
   ```

## Componentes

- `harness/run_llm.py` — bucle LLM: prompt → generar → tests → corregir hasta verde.
- `harness/lib.py` — cliente chat (OpenAI-compatible), extracción de ficheros, coste.
- `harness/count_tokens.py` — conteo con `tiktoken` (nunca caracteres/líneas).
- `harness/acceptance.py` — ejecutor de `checks.json` (tests externos por HTTP y/o CLI).
- `harness/orchestrate.py` — build/start/stop del servicio generado vía `run.sh`.
- `harness/run_acceptance.sh` — wrapper del ejecutor de aceptación.
- `harness/run_load.sh` + `harness/load_scenario.js` — carga con `k6`/`oha`/`wrk`.

## Flujo de ficheros

- Prompts neutros: `tasks/<T#>/prompt.md` (placeholders `{language}`, `{framework}`, `{runtime}`).
- Tests de aceptación: `tasks/<T#>/acceptance/checks.json`.
- Datos comunes: `tasks/<T#>/data/`.
- Código generado: `languages/<lang>/<task>/`.
- Resultados crudos: `results/raw/<model>/<task>/<lang>/repNN.json`.
- Resúmenes y carga: `results/summary/`.

## Esquema de `checks.json`

- Cabecera: `port`, `startup_retries`, `startup_delay_s`, `steps`.
- Paso HTTP (por defecto): `method`, `path`, `headers`, `json`/`body`,
  `expect_status` (entero o lista), `expect_json` (subconjunto),
  `json_path`, `save`, `retries`/`retry_delay_s`.
- Paso CLI: `command` (usa `bash run.sh ...`), `expect_exit`,
  `expect_stdout_contains`, `expect_stdout_json`, `json_path`, `save`.
- `{variable}` en path/body/json se sustituye por lo guardado con `save`.

`run_llm.py` escribe el código generado en `languages/<lang>/<task>/`, y para cada
iteración orquesta: `run.sh start` → tests de aceptación → `run.sh stop`. Para
tareas CLI (solo pasos `command`) no gestiona servicio.

## Contrato `run.sh` (generado por el modelo)

- HTTP: `run.sh start` construye/instala dependencias, arranca el servicio en
  segundo plano en el puerto 8005, escribe su PID en `server.pid` y devuelve 0;
  `run.sh stop` lo detiene y borra `server.pid`.
- CLI: `run.sh` reenvía sus subcomandos (p. ej. `init`/`add`/`list`).
- La salida de start/stop queda en `run.start.log` / `run.stop.log`.

## Notas

- Requiere `requests` y `tiktoken`. Con venv:
  `python3 -m venv .venv && .venv/bin/pip install requests tiktoken`.
  Usar `./.venv/bin/python harness/...` en los ejemplos.
- `run_load.sh` requiere `k6` (recomendado), `oha` o `wrk` instalados.
- Para modelos no OpenAI, usar un endpoint OpenAI-compatible o suministrar
  tokenizador propio; sin él, el conteo se marca como `fallback`.
