# mc | mission-control

A cloud- and hosting-platform-agnostic tool for managing compute resources and deploying applications.

## Development setup

### Run the server

Run the following command to start the server:

```bash
# from the project root directory
uv run uvicorn --app-dir ./src --port 13080 server:app

# for development with auto-reload
uv run uvicorn --app-dir ./src --reload --port 13080 server:app
```


### Run Orchestra

Orchestra is a lightweight task queue built on top of Celery. 

It is used to run background tasks and track their status.


#### Run celery worker

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
export DATA_DIR="/path/to/data"
celery -A celery_worker.celery worker --loglevel=INFO
```


### Local development stack with Docker

```bash
docker-compose -f docker-compose.dev.yml up -d
```


## UI

The UI is built with React and is located in the `ui` directory. 
To run the UI locally:

```bash
cd ui
bun install
bun dev
```

The UI will be available at `http://localhost:1420` by default.