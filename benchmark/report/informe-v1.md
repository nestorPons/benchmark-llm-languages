# Informe v1 — Benchmark LLM + rendimiento (piloto)

## Alcance

- Modelos: gpt-4o-mini, gpt-4o (temp 0).
- Tareas: T1, T3, T4, T7, T8. T2/T5 con checks definidos, sin ejecutar.
- Lenguajes piloto: python, typescript, go (todos aplican T1-T8; ver `../applicability.json`).
- Reps: 5 en combos verdes principales; 1 en el resto. Carga k6: VUS 1/10, 5 reps.

## Eje A — desarrollo con LLM (de mejor a peor: pass, coste)

| Modelo | Tarea | Lang | n | pass | pass@1 | iters med | coste med |
|---|---|---|---|---|---|---|---|
| mini | T4 | python | 1 | 1.00 | 1.00 | 1 | $0.0003 |
| mini | T7 | python | 5 | 1.00 | 1.00 | 1 | $0.0020 |
| mini | T8 | python | 1 | 1.00 | 1.00 | 1 | $0.0021 |
| gpt-4o | T1 | go | 5 | 1.00 | 1.00 | 1 | $0.019 |
| gpt-4o | T1 | typescript | 5 | 0.80 | 0.40 | 5 | $0.129 |
| mini | T3 | python | 1 | 0.00 | 0.00 | 10 | $0.015 |
| mini | T1 | typescript | 1 | 0.00 | 0.00 | 10 | $0.028 |
| mini | T1 | go | 1 | 0.00 | 0.00 | 10 | $0.032 |
| gpt-4o | T1 | python | 1 | 0.00 | 0.00 | 10 | $0.52 |

- Go/gpt-4o: 5/5 pass@1, coste p25-p75 $0.018-0.019 (estable).
- TS/gpt-4o: 4/5 pass, coste p25-p75 $0.018-0.226 (inestable).
- Mini solo rinde en modificar/simple (T7/T8/T4); greenfield falla.

## Eje B — rendimiento (`GET /health`, mediana 5 reps; de mejor a peor por throughput a 10 VU)

| Lang | 1 VU | 10 VU |
|---|---|---|
| Go | 459 req/s, p95 4 ms | ~1280 req/s, p95 13 ms |
| TypeScript | ~530 req/s, p95 4.5 ms | ~820 req/s, p95 24 ms |
| Python | 81 req/s, p95 22 ms | ~110 req/s, p95 186 ms |

Orden: Go > TS > Python (igual que Eje A con gpt-4o).

## Puntuación

- Pesos: salida .15, contexto .15, errores .20, ejecución .30, coste IA .20.
- Ranking: Go/T1/gpt-4o (0.98) > TS/T1/gpt-4o (0.74) > T4/mini (0.70) > T7/T8/mini (0.68).
- Sensibilidad (prod_heavy, perf_heavy): el orden Go > TS se mantiene; ver `sensitivity.json`.
- Gráficos: `radar.png` (5 objetivos por combo), `pareto.png` (coste vs throughput).

## Recomendación

- Servidor con rendimiento: **Go** (verde barato + mayor throughput).
- Web/API media: **TypeScript** (rinde bien, pero con mini falla; usar gpt-4o y vigilar dispersión).
- Scripts y modificar existente: **Python + mini** ($0.002, pass@1).
- Modelo: gpt-4o para greenfield; mini solo para modificar/simple. Ninguno se autocorrige (pass@k≈pass@1).

## Limitaciones

- n=1 en varios combos (sin dispersión).
- Eje B solo `/health`; falta CPU/RAM, arranque e imagen.
- Sin Docker; versiones no fijadas por implementación.
- T2/T5/T6 sin ejecutar; resto de lenguajes pendiente.
