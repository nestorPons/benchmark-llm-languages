# T1 — API REST CRUD con BD, JWT y validación

Implementa en **{language}** con **{framework}** (runtime: `{runtime}`) una API REST
que cumpla lo siguiente:

- CRUD completo sobre el recurso `item` (campos: `id`, `name`, `description`,
  `price`, `created_at`). Persistencia en **SQLite embebida** (fichero local, sin
  servidor externo; esquema en `data/schema.sql`).
- Autenticación JWT: endpoint `POST /auth/login` que acepta un cuerpo JSON
  `{"username": "...", "password": "..."}` y devuelve el token en el campo
  `token`; el resto de rutas protegidas lo exigen (401 sin token válido).
  Debe existir un usuario semilla `admin`/`secret` que pueda autenticarse.
- Validación de entrada: `price` negativo se rechaza con 400.
- Códigos de estado: creación 201, borrado 200/204, recurso inexistente 404.
- `GET /health` sin autenticación devolviendo 200.
- `POST /items`, `GET /items`, `GET /items/{id}`, `PUT /items/{id}`,
  `DELETE /items/{id}`.

Incluye un `README.md` con instrucciones exactas para construir y ejecutar el
servicio en el puerto 8005. Escribe cada fichero en un bloque de código con su
ruta.
