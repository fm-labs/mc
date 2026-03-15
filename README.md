# mc | mission-control

A cloud- and hosting-platform-agnostic tool for managing compute resources and deploying applications.

## Development setup

### Run the server

Run the following command to start the server:

```bash
# from the project root directory
uv run uvicorn --app-dir ./src --port 3080 server:app

# for development with auto-reload
uv run uvicorn --app-dir ./src --reload --port 3080 server:app
```


The API will be available at `http://localhost:3080`.



### Local development stack with Docker

```bash
docker-compose -f compose.dev.yaml up -d
```


## UI

The UI is built with React and is located in the `ui` directory. 
To run the UI locally:

```bash
cd ui
bun install
bun dev
```

The UI will be available at `http://localhost:1420`.