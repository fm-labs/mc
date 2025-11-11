#!/bin/bash

mkdir -p ./build/rx
rm -rf ./build/rx
mkdir -p ./dist/rx
rm -rf ./dist/rx

uv run pyinstaller --clean --onefile --distpath ./dist/rx --workpath ./build/rx --specpath ./build/rx --name rx ./src/rx.py
