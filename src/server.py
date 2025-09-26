################################################################
# KLOUDIA - AI-DRIVEN CLOUD MANAGEMENT PLATFORM
# MAIN SERVER FILE
# This file sets up the FastAPI application, including middleware and routing.
# Note: Middlewares are executed in reverse order of addition (LIFO)
#
# Run the server with:
#   uvicorn server:app
################################################################
import os
from typing import Optional, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter, Security
from fastapi import Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from kloudia.server.models import Problem
from kloudia.server.router import app_router

os.environ["DOCKER_HOST_1"] = os.environ.get("DOCKER_HOST_1", "tcp://localhost:30003")

app = FastAPI(title="Kloudia API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# class NotFoundError(Exception):
#     def __init__(self, detail: str):
#         self.detail = detail

# Global exception handlers that emit Problem JSON responses
@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    problem = Problem(title=exc.detail or exc.status_code, status=exc.status_code)
    return JSONResponse(status_code=exc.status_code, content=problem.model_dump(),
                        media_type="application/json")

# @app.exception_handler(NotFoundError)
# async def not_found_handler(_: Request, exc: NotFoundError):
#     problem = Problem(title="Not Found", status=404, detail=exc.detail)
#     return JSONResponse(status_code=404, content=problem.model_dump(),
#                         media_type="application/problem+json")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    problem = Problem(
        title="Validation Error",
        status=422,
        detail="Request validation failed.",
        errors={"details": exc.errors()}
    )
    return JSONResponse(status_code=422, content=problem.model_dump(),
                        media_type="application/problem+json")

# Reusable OpenAPI error responses (show up on every route that includes them)
problem_response_ref = {"model": Problem, "description": "Problem Details (RFC 7807)",
                        "content": {"application/json": {"schema": Problem.model_json_schema()}}}

default_error_responses = {
    400: problem_response_ref,
    #401: problem_response_ref,
    #403: problem_response_ref,
    #404: problem_response_ref,
    #409: problem_response_ref,
    #422: problem_response_ref,
    500: problem_response_ref,
}

app.include_router(app_router, responses=default_error_responses)

