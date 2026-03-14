#!/bin/bash

mkdir -p ./build
rm -rf ./build/
#mkdir -p ./dist/bin
#rm -rf ./dist/bin

BUILD_DIST_DIR=${BUILD_DIST_DIR:-./dist/bin}
mkdir -p "$BUILD_DIST_DIR"

TARGET_TRIPLE=$(rustc --print host-tuple)

uv sync --frozen

uv run pyinstaller --clean --onefile --distpath $BUILD_DIST_DIR --workpath ./build --specpath ./build \
  --name mc-cli \
  ./src/cli.py

uv run pyinstaller --clean --onefile --distpath $BUILD_DIST_DIR --workpath ./build --specpath ./build \
  --name mc-srv \
  --copy-metadata fastmcp \
  ./src/server.py

uv run pyinstaller --clean --onefile --distpath $BUILD_DIST_DIR --workpath ./build --specpath ./build \
  --name mc-mcp \
  --copy-metadata fastmcp \
  ./src/mcp_server.py
