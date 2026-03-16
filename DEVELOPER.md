# mc | mission-control for developers


## Development setup


```bash
# checkout the code
git clone https://github.com/fm-labs/missioncontrol.git
```


### Run the server

Run the following command to start the server:

```bash
# from the project root directory
cd missioncontrol
uv run uvicorn --app-dir ./src --port 3080 server:app

# for development with auto-reload and debug logging
uv run uvicorn --app-dir ./src --reload --port 3080 server:app --log-level debug
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
pnpm install
pnpm run dev
```

The UI will be available at `http://localhost:1420`.