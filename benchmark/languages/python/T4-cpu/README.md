# CPU-Intensive HTTP Service

Este servicio HTTP realiza operaciones de cómputo intensivo, incluyendo ordenación de números y cálculo de hash SHA-256.

## Endpoints

- `POST /compute`: Recibe un JSON con un array de enteros y devuelve el array ordenado.
- `POST /hash`: Recibe un JSON con un texto y devuelve su hash SHA-256.
- `GET /health`: Devuelve un estado 200 si el servicio está funcionando.

## Ejecución

1. Clona este repositorio.
2. Navega al directorio del proyecto.
3. Ejecuta el siguiente comando para iniciar el servicio:

   ```bash
   ./run.sh start
   ```

4. El servicio estará disponible en `http://localhost:8005`.

5. Para detener el servicio, ejecuta:

   ```bash
   ./run.sh stop
   ```