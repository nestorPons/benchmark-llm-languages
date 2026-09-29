# FastAPI CRUD API

## Description
This is a FastAPI application that provides a RESTful API for managing items with JWT authentication.

## Requirements
- Python 3.14
- SQLite

## Setup
1. Clone the repository.
2. Navigate to the project directory.
3. Run the following command to start the server:
   ```bash
   ./run.sh start
   ```
4. The API will be available at `http://localhost:8005`.

## Endpoints
- `POST /auth/login`: Authenticate and receive a JWT token.
- `GET /health`: Check the health of the service.
- `POST /items`: Create a new item.
- `GET /items`: Retrieve all items.
- `GET /items/{id}`: Retrieve a specific item by ID.
- `PUT /items/{id}`: Update a specific item by ID.
- `DELETE /items/{id}`: Delete a specific item by ID.

## Stopping the Server
To stop the server, run: