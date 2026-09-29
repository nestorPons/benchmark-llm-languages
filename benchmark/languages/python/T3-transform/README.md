# JSON/CSV Transformation Service

This is a simple HTTP service that transforms JSON and CSV data efficiently.

## Endpoints

- `POST /transform`: Accepts a JSON payload with records and returns a summary.
- `POST /transform/csv`: Accepts a CSV file and returns a summary.
- `GET /health`: Returns the health status of the service.

## Running the Service

1. Clone the repository.
2. Run the following command to start the service:

   ```bash
   ./run.sh start
   ```

3. The service will be available at `http://localhost:8005`.

4. To stop the service, run:

   ```bash
   ./run.sh stop
   ```