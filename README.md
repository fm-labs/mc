# kloudia-orchestra

Run the following command to start the server:

```bash
cd src
uvicorn server:app

# or
# from the project root directory
#export PYTHONPATH=$PYTHONPATH:$(pwd)/src
uv run uvicorn --app-dir ./src server:app --reload
```

## Run celery worker

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
export DATA_DIR="/path/to/data"
celery -A celery_worker.celery worker --loglevel=INFO
```


## Run server in dev mode

```bash
uvicorn server:app --reload
```


## Run the docker dev stack

```bash
docker-compose -f docker-compose.dev.yml up -d
```