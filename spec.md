# Especificación: Benchmark de lenguajes para desarrollo asistido por LLM y rendimiento en ejecución

**Versión:** 0.3
**Estado:** Borrador
**Ámbito:** Aplicaciones de servidor, web y, ocasionalmente, escritorio

---

## 1. Objetivo

Comparar lenguajes de programación en dos ejes independientes y combinarlos después en una puntuación ponderada:

1. **Eje A: Eficiencia del desarrollo con LLM.** Tokens consumidos, coste, velocidad, tasa de acierto y calidad del código generado.
2. **Eje B: Rendimiento en ejecución.** Throughput, latencia, uso de recursos, arranque y tamaño de artefactos.

**Pregunta que debe responder el benchmark:** ¿qué lenguaje minimiza el coste total (desarrollo con LLM + revisión humana + infraestructura) manteniendo un rendimiento de ejecución adecuado para servidores, web y escritorio?

### 1.1 Objetivos y aspectos a tener en cuenta

| Objetivo | Aspecto a tener en cuenta |
|---|---|
| Reducir tokens de salida | Concisión sintáctica |
| Reducir tokens de contexto | Código modular y sencillo |
| Reducir errores de generación | Sintaxis y patrones bien representados en el entrenamiento |
| Reducir tiempo de ejecución | Compilación, algoritmos y optimización |
| Reducir coste total de IA | Menos iteraciones y menor contexto acumulado |

Cada objetivo tiene métricas asociadas (secciones 5, 6 y 7.3) para poder comprobar si el lenguaje realmente lo cumple.

> **Advertencia:** menos caracteres o menos líneas **no** equivale a menos tokens. Los lenguajes muy densos en símbolos (Perl, Raku, APL/J/K) pueden tokenizar mal y gastar más tokens de los esperados, y los lenguajes con poco material de entrenamiento (Raku, Nim, Crystal) pueden aumentar los errores y las iteraciones. Toda conclusión debe basarse en tokens reales del modelo, nunca en caracteres o líneas.

## 2. Alcance

### 2.1 Lenguajes candidatos

Los candidatos se agrupan en tres grupos para poder separar el efecto de la concisión del efecto del ecosistema.

**Grupo 1: Referencia (mainstream, mucho entrenamiento)**

| Lenguaje | Runtime / Variante | Framework servidor (fijar versión) |
|---|---|---|
| TypeScript | Node.js (y opcionalmente Bun/Deno) | Fastify o Express |
| Python | CPython 3.12+ | FastAPI |
| Go | Go 1.22+ | Gin o Echo (o `net/http`) |
| Rust | Estable | Axum |
| C# | .NET 8+ | ASP.NET Core |
| Java | JDK 21+ | Spring Boot |

**Grupo 1b: Verbosidad media (ecosistema amplio, entrenamiento alto o medio)**

| Lenguaje | Runtime / Variante | Framework servidor (fijar versión) | Nota |
|---|---|---|---|
| PHP | PHP 8.3+ (OPcache + JIT activados) | Laravel, Symfony o Slim (elegir uno y fijarlo) | Muchísimo código en entrenamiento, ecosistema web enorme, rendimiento aceptable con OPcache |
| Dart | Dart 3.x (AOT) | Shelf o Dart Frog; Flutter para web y escritorio | Un único lenguaje para servidor, web y escritorio; entrenamiento medio |
| Swift | Swift 5.10+/6 | Vapor | Servidor y escritorio (macOS); tipado fuerte, rendimiento nativo |
| Scala 3 | JVM 21+ | http4s, Play o Tapir | Más conciso que Java, tipado potente que puede aumentar las iteraciones |
| Groovy | JVM 21+ | Micronaut o Grails | Alternativa dinámica y concisa sobre el ecosistema Java |

**Grupo 2: Baja verbosidad (foco de esta versión)**

| Lenguaje | Runtime / Variante | Framework servidor (fijar versión) | Nota |
|---|---|---|---|
| Perl 5 | Perl 5.36+ | Mojolicious o Dancer2 | Muy conciso, mucho código histórico en entrenamiento, rendimiento medio |
| Raku | Rakudo reciente | Cro | Muy expresivo, poco entrenamiento, rendimiento por validar |
| Ruby | CRuby 3.3+ (YJIT activado) | Sinatra o Rails (API) | Concisión alta y buena representación |
| Lua / LuaJIT | LuaJIT 2.1 | OpenResty o Lapis | Sintaxis mínima y ejecución rápida con JIT |
| Elixir | OTP 26+ | Phoenix o Plug | Conciso, gran concurrencia, entrenamiento moderado |
| Clojure | JVM 21+ | Ring + Reitit | Muy denso (Lisp), pocos tokens por funcionalidad |
| Julia | 1.10+ | Oxygen.jl o HTTP.jl | Conciso y rápido en cómputo, ecosistema web limitado |
| Nim | 2.x | Jester o Prologue | Sintaxis tipo Python, compila a nativo, poco entrenamiento |
| Crystal | 1.x | Kemal o Amber | Sintaxis tipo Ruby, compila a nativo, poco entrenamiento |
| Kotlin | JVM 21+ | Ktor | Más conciso que Java con el mismo runtime |
| F# / OCaml | .NET 8+ / OCaml 5 | Giraffe / Dream | Inferencia de tipos y código funcional compacto |

**Grupo 3: Extremos de densidad (solo tareas específicas, opcionales)**

| Lenguaje | Uso propuesto | Nota |
|---|---|---|
| AWK / `jq` | T3 (transformación de datos), scripts de servidor | Concisión extrema en su nicho |
| APL / J / K | T4 (algoritmos numéricos) | Mínimo en caracteres, pero probablemente alto en tokens y errores; sirve para comprobar la advertencia de la sección 1.1 |

> Se pueden añadir o retirar candidatos, pero deben mantenerse frameworks equivalentes en complejidad y madurez. Si un lenguaje no tiene framework adecuado para una tarea, se marca como **no aplicable** en esa tarea (no se penaliza con cero, se excluye de esa comparación y se documenta).

### 2.2 Fuera de alcance

- Benchmarks sintéticos sin relación con el trabajo real (por ejemplo, solo *fibonacci*).
- Comparativas de sintaxis o preferencias subjetivas sin medición.

## 3. Principios de diseño del experimento

1. **Especificaciones neutrales.** Cada tarea se describe sin sesgo hacia ningún lenguaje. No se traduce código de un lenguaje a otro; se pide la solución idiomática.
2. **Mismo modelo y parámetros.** Fijar versión del modelo, temperatura (0 o baja), *system prompt* y herramientas disponibles. Idealmente probar 2-3 modelos distintos.
3. **Repeticiones.** Mínimo 5 y recomendado 10 ejecuciones por combinación tarea × lenguaje × modelo. Reportar mediana y dispersión (p25-p75 o desviación estándar).
4. **Criterio de "terminado" automático.** Una batería de tests de aceptación **independiente del lenguaje** (por ejemplo, tests HTTP externos) que debe pasar en verde.
5. **Entorno reproducible.** Misma máquina, mismos recursos, contenedores con versiones fijadas y registro de versiones de lenguaje, framework y dependencias.
6. **Prompts idénticos.** El mismo prompt base para todos los lenguajes, cambiando solo el nombre del lenguaje y del framework.
7. **Equivalencia funcional.** Misma base de datos, mismo esquema y mismas condiciones de red en todas las implementaciones.

## 4. Tareas de prueba

| ID | Tarea | Qué revela |
|---|---|---|
| T1 | API REST CRUD con base de datos, autenticación JWT y validación | Caso típico de servidor |
| T2 | Worker con cola y concurrencia (procesar N trabajos en paralelo) | Modelo de concurrencia |
| T3 | Parseo y transformación de JSON/CSV grandes | CPU y memoria |
| T4 | Algoritmo CPU-intensivo (ordenación, hashing, compresión) | Rendimiento bruto |
| T5 | Web: SSR o SPA con formulario y llamada a la API | Ecosistema web |
| T6 | Aplicación de escritorio o CLI simple (Tauri, Electron, .NET, Qt...) | Empaquetado y arranque |
| T7 | **Modificar un proyecto existente:** añadir una funcionalidad y corregir un bug | Uso más realista del LLM |
| T8 | Refactor con tests existentes | Mantenibilidad asistida |

**Matriz de aplicabilidad:** no todos los lenguajes son viables en todas las tareas (por ejemplo, escritorio en Raku o SPA en Clojure sin ClojureScript). Antes de ejecutar, se rellena una matriz lenguaje × tarea con `aplica / no aplica / parcial`. Las tareas no aplicables se excluyen de la puntuación de ese lenguaje y se reporta la cobertura (porcentaje de tareas realizables).

Cada tarea debe incluir:

- Enunciado neutral (`tasks/Tn/prompt.md`).
- Tests de aceptación externos (`tasks/Tn/acceptance/`).
- Datos de entrada y esquema de base de datos comunes.
- Para T7 y T8: un repositorio base equivalente por lenguaje, con el mismo diseño funcional.

## 5. Eje A: Métricas de desarrollo con LLM

### 5.1 Coste y velocidad

| Métrica | Definición |
|---|---|
| Tokens de entrada totales | Suma de tokens enviados hasta tests en verde (incluye iteraciones y contexto) |
| Tokens de salida totales | Suma de tokens generados hasta tests en verde |
| Coste por tarea (€) | Tokens × tarifa del modelo |
| Tiempo hasta verde | Tiempo de reloj total, incluyendo compilación, arranque y latencia del modelo |
| Verbosidad | Tokens o líneas de código por funcionalidad |

### 5.2 Calidad y fiabilidad

| Métrica | Definición |
|---|---|
| pass@1 | Porcentaje de ejecuciones que pasan todos los tests a la primera |
| Iteraciones medias | Número de ciclos de corrección hasta verde |
| Errores de compilación/tipos | Cantidad por intento |
| Alucinaciones | APIs, funciones o paquetes inexistentes, o versiones obsoletas |
| Intervención humana | Veces que hay que corregir a mano (y minutos empleados) |
| Análisis estático | Avisos de linter, resultados de SAST (vulnerabilidades comunes) |
| Calidad de tests generados | Cobertura y mutación, si aplica |

### 5.3 Contexto

| Métrica | Definición |
|---|---|
| Tokens para comprender el proyecto | Tamaño del contexto necesario en T7 y T8 |
| Efecto del tipado | Mejora de autocorrección gracias al feedback del compilador (medir, no asumir) |

### 5.4 Límite de iteraciones

Fijar un máximo de intentos por ejecución (por ejemplo, 10). Si no se alcanza verde, se registra como **fallo** y cuenta en pass@k, con el coste consumido incluido.

### 5.5 Métricas derivadas por objetivo

**Objetivo: reducir tokens de salida (concisión sintáctica)**

| Métrica | Definición |
|---|---|
| Tokens de salida por funcionalidad | Tokens de código final ÷ nº de requisitos cumplidos |
| Densidad de tokens | Tokens ÷ líneas y tokens ÷ caracteres (detecta lenguajes que "ahorran" caracteres pero no tokens) |
| Ratio de boilerplate | % de tokens que no aportan lógica (imports, declaraciones, configuración) |
| Tokens de salida totales hasta verde | Incluye todas las iteraciones, no solo la solución final |

**Objetivo: reducir tokens de contexto (código modular y sencillo)**

| Métrica | Definición |
|---|---|
| Tokens del proyecto completo | Tamaño del repositorio final medido con el tokenizador del modelo |
| Tokens de contexto por iteración | Tokens de entrada medios en cada ciclo de corrección |
| Contexto mínimo necesario | Tokens mínimos que hay que dar al modelo para completar T7 (cambio en proyecto existente) |
| Modularidad | Tamaño medio y máximo de ficheros/funciones (en tokens) y nº de dependencias entre módulos |
| Complejidad ciclomática media | Como indicador de sencillez del código generado |

**Objetivo: reducir errores de generación (patrones bien representados en el entrenamiento)**

| Métrica | Definición |
|---|---|
| Errores por 1000 tokens generados | Compilación, tipos, sintaxis y ejecución |
| Tasa de alucinación | Paquetes, funciones o APIs inexistentes u obsoletos |
| pass@1 y pass@k | Acierto a la primera y en k intentos |
| Estabilidad entre ejecuciones | Varianza de pass@1 y de tokens entre repeticiones |
| Uso de idioms del lenguaje | Revisión por linter y revisión manual de muestra (¿código idiomático o traducido de otro lenguaje?) |
| Indicador de representación en entrenamiento | *Proxy* indirecto: perplejidad/logprobs del modelo sobre código del lenguaje (si el modelo los expone) y rendimiento en un conjunto de tareas triviales del lenguaje |

**Objetivo: reducir coste total de IA (menos iteraciones y menor contexto acumulado)**

| Métrica | Definición |
|---|---|
| Iteraciones hasta verde | Media y percentil 90 |
| Contexto acumulado | Suma de tokens de entrada de todas las iteraciones (crece con cada ciclo) |
| Coste por tarea completada | Coste total de tokens ÷ tareas superadas (los fallos suman coste, no aportan resultado) |
| Coste de reintentos | Coste consumido en iteraciones posteriores a la primera |

> Los tokens de contexto acumulado suelen dominar el coste real: un lenguaje con pocos tokens de salida pero muchas iteraciones puede acabar siendo más caro que uno más verboso que acierta a la primera.

## 6. Eje B: Métricas de ejecución

### 6.1 Servidor

| Métrica | Herramienta sugerida |
|---|---|
| Throughput (req/s) | `k6`, `wrk`, `oha` |
| Latencia p50 / p95 / p99 | `k6`, `oha` |
| CPU y memoria (RSS) en reposo y bajo carga | `docker stats`, `/usr/bin/time -v` |
| Arranque en frío | `hyperfine` |
| Pausas de GC (si aplica) | Herramientas del runtime |
| Tamaño de imagen Docker y tiempo de build | `docker images`, cronómetro |

### 6.2 Web

| Métrica | Herramienta sugerida |
|---|---|
| Tamaño del bundle | Análisis del build |
| TTFB | Lighthouse, WebPageTest |
| Core Web Vitals / puntuación Lighthouse | Lighthouse |

### 6.3 Escritorio / CLI

| Métrica | Herramienta sugerida |
|---|---|
| Tiempo de arranque | `hyperfine` |
| RAM en reposo | Monitor del sistema |
| Tamaño del instalador o binario | Inspección del artefacto |

### 6.4 Compilación, algoritmos y optimización

Para el objetivo de **reducir tiempo de ejecución**, se mide qué parte del rendimiento depende del lenguaje y qué parte de la calidad del código generado:

| Métrica | Definición |
|---|---|
| Tiempo de compilación / build | Completo y incremental |
| Rendimiento "tal cual" | Resultado con el código generado a la primera, sin optimizar |
| Rendimiento tras optimización guiada | Resultado tras pedir al LLM una ronda de optimización (con perfil de `perf`/flamegraph como contexto) |
| Ganancia y coste de optimizar | Mejora obtenida frente a tokens/iteraciones invertidos |
| Elección de algoritmos y estructuras | Revisión de si el LLM eligió algoritmos y estructuras de datos adecuados (complejidad) |
| Modo de ejecución | Interpretado, JIT, AOT o nativo; se registra y se prueban las opciones de optimización habituales (por ejemplo, YJIT en Ruby, LuaJIT, `--release` en Rust/Nim/Crystal, PGO si aplica) |
| Extensiones nativas | Si el lenguaje necesita módulos en C/XS para ser competitivo (habitual en Perl), se documenta y se mide con y sin ellas |

### 6.5 Protocolo de medición

- **Warm-up** obligatorio antes de medir (por ejemplo, 30-60 s de carga).
- Carga sostenida (mínimo 60 s por escenario) y varios niveles de concurrencia.
- Misma máquina, sin otras cargas, con recursos del contenedor limitados y fijos.
- Repetir cada medición al menos 5 veces y reportar mediana y dispersión.
- Si el resultado es anómalo, analizar con `perf` y *flamegraphs* antes de aceptarlo.

## 7. Puntuación combinada

### 7.1 Coste total por tarea

```
Coste total = coste de tokens
            + tiempo humano de revisión/corrección × tarifa horaria
            + coste de infraestructura estimado (según rendimiento medido)
```

### 7.2 Puntuación ponderada

1. Normalizar cada métrica al rango 0-1 (mejor valor = 1).
2. Aplicar pesos configurables. Propuesta inicial:

| Dimensión | Peso |
|---|---|
| Productividad con LLM (Eje A) | 40 % |
| Rendimiento en ejecución (Eje B) | 40 % |
| Mantenibilidad y despliegue | 20 % |

3. Realizar un **análisis de sensibilidad** variando los pesos (por ejemplo, 60/30/10 y 20/60/20) para comprobar si el ranking es estable.

### 7.3 Puntuación por objetivo

Además de la puntuación global, se calcula una puntuación (0-1) por cada objetivo de la sección 1.1, de modo que se vea en qué destaca cada lenguaje:

| Objetivo | Métricas principales | Peso sugerido |
|---|---|---|
| Reducir tokens de salida | Tokens de salida por funcionalidad, densidad de tokens | 15 % |
| Reducir tokens de contexto | Tokens del proyecto, contexto mínimo para T7, modularidad | 15 % |
| Reducir errores de generación | pass@1, errores por 1000 tokens, alucinaciones | 20 % |
| Reducir tiempo de ejecución | Throughput, latencia p99, CPU/memoria, arranque | 30 % |
| Reducir coste total de IA | Iteraciones, contexto acumulado, coste por tarea completada | 20 % |

Los pesos son configurables. Se recomienda presentar un **gráfico de radar** por lenguaje (5 ejes = 5 objetivos) y un **frente de Pareto** entre *coste total de IA* y *tiempo de ejecución* para identificar los lenguajes no dominados.

## 8. Entregables

1. **Harness de automatización** que, para cada lenguaje, tarea y repetición:
   - Lanza el prompt al modelo y gestiona el bucle de corrección.
   - Cuenta tokens de entrada y salida y calcula el coste.
   - Ejecuta los tests de aceptación y registra el resultado.
   - Compila, arranca la aplicación y lanza las pruebas de carga.
   - Guarda todos los resultados en formato estructurado (JSON/CSV).
2. **Dataset de resultados** con metadatos de reproducibilidad (versiones, modelo, semilla, fecha).
3. **Informe final** con tablas, gráficos, ranking ponderado y análisis de sensibilidad.
4. **Recomendación** por tipo de proyecto: servidor, web y escritorio.

## 9. Estructura de repositorio propuesta

```
benchmark/
├── spec.md
├── tasks/
│   ├── T1-rest-crud/
│   │   ├── prompt.md
│   │   ├── acceptance/
│   │   └── data/
│   └── ...
├── languages/
│   ├── typescript/
│   ├── python/
│   ├── go/
│   ├── rust/
│   ├── csharp/
│   ├── java/
│   ├── php/
│   ├── dart/
│   ├── swift/
│   ├── scala/
│   ├── groovy/
│   ├── perl/
│   ├── raku/
│   ├── ruby/
│   ├── lua/
│   ├── elixir/
│   ├── clojure/
│   ├── julia/
│   ├── nim/
│   ├── crystal/
│   ├── kotlin/
│   └── fsharp-ocaml/
├── harness/
│   ├── run_llm.py
│   ├── count_tokens.py
│   ├── run_acceptance.sh
│   └── run_load.sh
├── results/
│   ├── raw/
│   └── summary/
└── report/
```

## 10. Riesgos y errores frecuentes a evitar

| Riesgo | Mitigación |
|---|---|
| Prompts distintos o ejemplos más pulidos en un lenguaje | Plantilla única de prompt |
| Medir solo la primera respuesta | Medir el ciclo completo hasta tests en verde |
| Tokenizadores distintos entre modelos | Comparar tokens **dentro** de cada modelo, no entre modelos |
| Benchmarks sin equivalencia real (BD en memoria vs. externa) | Misma infraestructura para todas las implementaciones |
| Solo tareas nuevas, sin código existente | Incluir siempre T7 y T8 |
| Varianza alta del LLM | Repeticiones y reporte de dispersión |
| Sesgo por conocimiento previo del evaluador | Tests automáticos y criterios objetivos |
| Resultados que dependen del modelo | Probar varios modelos y reportar por separado |
| Confundir concisión de caracteres con concisión de tokens | Medir siempre con el tokenizador real del modelo |
| Lenguajes con poco entrenamiento (Raku, Nim, Crystal) penalizados por el modelo, no por el lenguaje | Reportar aparte y repetir con modelos distintos y con ejemplos en contexto (few-shot) como variante controlada |
| Código "golfizado" difícil de mantener (Perl, APL/J/K) | Incluir T7 y T8 y medir legibilidad y mantenibilidad, no solo tamaño |
| Rendimiento distorsionado por extensiones nativas o JIT no activado | Documentar modo de ejecución y flags; medir con y sin optimizaciones |
| Ecosistema insuficiente (sin framework web o de escritorio maduro) | Matriz de aplicabilidad y reporte de cobertura por lenguaje |
| Frameworks con distinto peso (Laravel/Spring/Rails frente a microframeworks) | Comparar en la misma categoría (micro con micro, full-stack con full-stack) o reportar ambas variantes por separado |
| Modo de ejecución que cambia el resultado (PHP-FPM frente a workers persistentes) | Fijar y documentar el modo; opcionalmente medir ambos |

## 11. Hipótesis iniciales (a contrastar, no a asumir)

- Python y TypeScript: menor coste en tokens y mejor pass@1, con menor rendimiento bruto.
- Go: buen equilibrio entre productividad con LLM y rendimiento.
- Rust: mejor rendimiento y menor consumo de recursos, pero más iteraciones por el compilador.
- PHP: muy alta representación en el entrenamiento y buen pass@1 en web y APIs; rendimiento razonable con OPcache/JIT, pero inferior a Go/Rust/.NET en concurrencia y CPU. Su modelo de ejecución (por petición o con workers como Swoole/FrankenPHP) debe fijarse y documentarse porque cambia mucho los resultados.
- Dart: buen equilibrio y una única base de código para servidor, web y escritorio (Flutter); menos entrenamiento que los mainstream y ecosistema de servidor más pequeño.
- Swift: rendimiento nativo y tipado fuerte, pero servidor menos maduro y más iteraciones probables por el compilador; escritorio limitado principalmente a Apple.
- Scala 3 y Groovy: menos verbosos que Java sobre la misma JVM; Scala puede requerir más iteraciones por la complejidad de su sistema de tipos, y Groovy tiene poco entrenamiento reciente.
- C# y Java: buen rendimiento en servidor, mayor verbosidad y arranque más lento (salvo compilación AOT/nativa). Kotlin reduce la verbosidad manteniendo el runtime.
- Perl: pocos tokens de salida en scripts y procesamiento de texto, buen entrenamiento histórico, pero rendimiento de servidor medio y riesgo de código difícil de mantener.
- Raku: gran expresividad, pero probablemente más errores e iteraciones por menor representación en el entrenamiento, y rendimiento inferior en servidor.
- Ruby y Elixir: buena concisión y buena representación en el entrenamiento; Elixir destaca en concurrencia, Ruby en productividad.
- Lua/LuaJIT: sintaxis mínima y muy buen rendimiento para su categoría.
- Nim y Crystal: podrían combinar sintaxis concisa con rendimiento nativo, con el riesgo de más errores por falta de entrenamiento.
- Clojure y F#/OCaml: pocos tokens por funcionalidad, pero paradigma funcional y sintaxis (paréntesis, inferencia) que pueden generar errores sutiles.
- APL/J/K: mínimo en caracteres, probablemente no en tokens; sirve como control de la hipótesis "menos caracteres = menos tokens".
- Hipótesis global: el mejor lenguaje para coste total de IA no será necesariamente el más conciso, sino el que combine concisión razonable con alta representación en el entrenamiento y pocas iteraciones.

## 12. Criterios de aceptación del benchmark

- [ ] Todas las tareas tienen enunciado neutral y tests de aceptación externos.
- [ ] Todas las implementaciones usan versiones fijadas y documentadas.
- [ ] Cada combinación tarea × lenguaje × modelo tiene al menos 5 repeticiones.
- [ ] Las mediciones de rendimiento incluyen warm-up y repeticiones.
- [ ] El informe incluye análisis de sensibilidad de los pesos.
- [ ] Los resultados son reproducibles con el harness y los metadatos entregados.
- [ ] Todas las métricas de tokens se calculan con el tokenizador real de cada modelo (nunca con caracteres o líneas).
- [ ] Existe una matriz de aplicabilidad lenguaje × tarea y se reporta la cobertura de cada lenguaje.
- [ ] Cada uno de los 5 objetivos de la sección 1.1 tiene su puntuación por lenguaje y su gráfico de radar.
- [ ] Se incluye el frente de Pareto entre coste total de IA y tiempo de ejecución.
- [ ] Se documenta el modo de ejecución (interpretado/JIT/AOT) y los flags de optimización de cada lenguaje.
