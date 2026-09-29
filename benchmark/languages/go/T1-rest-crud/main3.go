
## API Endpoints

- `GET /health`: Health check endpoint, no authentication required.
- `POST /auth/login`: Login endpoint, returns JWT token.
- `POST /items`: Create a new item.
- `GET /items`: Retrieve all items.
- `GET /items/{id}`: Retrieve a specific item by ID.
- `PUT /items/{id}`: Update a specific item by ID.
- `DELETE /items/{id}`: Delete a specific item by ID.

## Authentication

Use the following credentials to obtain a JWT token:

- Username: `admin`
- Password: `secret`

Include the token in the `Authorization` header for protected routes.