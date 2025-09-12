################################################################
# KLOUDIA - AI-DRIVEN CLOUD MANAGEMENT PLATFORM
# MAIN SERVER FILE
# This file sets up the FastAPI application, including middleware and routing.
# Note: Middlewares are executed in reverse order of addition (LIFO)
#
# Run the server with:
#   uvicorn server:app
################################################################

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kloudia.server.router import app_router

app = FastAPI(title="Kloudia API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(app_router, prefix="")

