# Fastify API

Este proyecto implementa una API REST utilizando Fastify con autenticación JWT y persistencia en SQLite.

## Requisitos

- Node.js 20 o superior

## Instalación

1. Clona el repositorio.
2. Ejecuta `./run.sh start` para instalar las dependencias, construir el proyecto y arrancar el servidor.

## Uso

- El servidor se ejecutará en `http://localhost:8005`.
- Endpoints disponibles:
  - `POST /auth/login`: Autenticación de usuario.
  - `GET /health`: Verificación de estado del servidor.
  - CRUD para `items`:
    - `POST /items`
    - `GET /items`
    - `GET /items/{id}`
    - `PUT /items/{id}`
    - `DELETE /items/{id}`

## Detener el servidor

Ejecuta `./run.sh stop` para detener el servidor.