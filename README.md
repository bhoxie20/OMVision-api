# Vector Deal Flow API

This is a FastAPI backend that serves the DealFlow user-facing client.

### Dev Setup

1. Clone the repo
2. Install dependencies: `poetry install`
3. Create a `.env` file in the root of the project with the following contents:

   ```shell
   DATABASE_HOSTNAME=
   DATABASE_PORT=
   DATABASE_PASSWORD=
   DATABASE_NAME=
   DATABASE_USERNAME=
   ```

   Replace the values with the appropriate values for your database.

4. Run the server: `python main.py`

### Formatting

This project uses `black` for code formatting. To format the code, run `poetry run black .` in the root of the project.
