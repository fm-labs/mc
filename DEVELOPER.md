# mc | mission-control for developers


## Development setup


```bash
# checkout the code
git clone https://github.com/fm-labs/mc.git

# create the virtualenv and install all dependencies, including the dev group
cd mc
uv sync
```

The dev tools (pytest, ruff, mypy) are in the `dev` dependency group, which `uv sync` installs by default.
Run them with `uv run` so they use the project's virtualenv. Their settings are in `pyproject.toml`.


### Run the server

Run the following command to start the server:

```bash
# from the project root directory
cd mc
uv run uvicorn --app-dir ./src --port 3080 server:app

# for development with auto-reload and debug logging
uv run uvicorn --app-dir ./src --reload --port 3080 server:app --log-level debug
```


The API will be available at `http://localhost:3080`.


### Local development stack with Docker

```bash
docker-compose -f compose.dev.yaml up -d
```


## Python dev tools

### Tests (pytest)

Tests are in `tests/`. `src/` is on the import path, and async tests run without a marker (`asyncio_mode = "auto"`).

```bash
uv run pytest                               # all tests
uv run pytest tests/inventorydb             # one directory
uv run pytest tests/inventorydb/test_items.py -k mask   # tests matching a name
uv run pytest -x -q                         # stop at the first failure, short output
```

### Lint and format (ruff)

Rules: pycodestyle, pyflakes, isort, pyupgrade and bugbear. Line length is 120, and the target is Python 3.13.

```bash
uv run ruff check .                 # lint
uv run ruff check --fix .           # lint and apply safe fixes
uv run ruff format .                # format
uv run ruff format --check .        # check formatting only (CI)
uv run ruff rule B008               # explain a rule
```

Review `--fix` and `format` changes before committing.

### Type check (mypy)

mypy runs in strict mode on `src/` and resolves modules from source (`mypy_path = "src"`).

```bash
uv run mypy                         # check src/
uv run mypy src/inventorydb         # check one package
uv run mypy --allow-untyped-defs --allow-incomplete-defs --allow-untyped-calls tests
```

Only `inventorydb` passes strict mode so far. Check the package you changed, and keep new code free of type errors.

### Before committing

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy src/inventorydb && uv run pytest
```

### Dependencies

```bash
uv add <package>                    # runtime dependency
uv add --dev <package>              # dev dependency
uv lock --upgrade-package <package> # upgrade one package
```

Commit `pyproject.toml` and `uv.lock` together.


## UI

The UI is built with React and is located in the `ui` directory. 
To run the UI locally:

```bash
cd ui
pnpm install
pnpm run dev
```

The UI in devmode will be available at `http://localhost:3081`.


## Releasing

### Bump version

Bump version in following files:

- pyproject.toml
- ui/package.json
- Dockerfile