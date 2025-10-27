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
import logging
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from mc.db.redis import get_redis_client
from mc.mcp.app import mcp as mcp_app
from mc.mcp.helper import init_mcp_http_app
from mc.plugin.containers.manager import bootstrap_container_connection_manager, get_container_connection_manager
from mc.server.models import Problem
from mc.server.router import app_router

# Load MCP server app with specified transport
mcp_transport = os.getenv("MCP_TRANSPORT", "streamable-http")
mcp_http_app = init_mcp_http_app(mcp_app, transport=mcp_transport)

@asynccontextmanager
async def lifespan(main_app: FastAPI):
    print("Setting up resources for main app lifespan...")

    async with AsyncExitStack() as stack:
        # init resources for the main app
        main_app.state.redis = get_redis_client()

        await bootstrap_container_connection_manager()

        # if you want to be explicit, also enter the mounted app's lifespan:
        # (This guarantees startup/shutdown even if you run the sub-app standalone elsewhere.)
        await stack.enter_async_context(
            mcp_http_app.router.lifespan_context(mcp_http_app)
        )

        try:
            yield
        finally:
            # teardown in reverse order is handled by ExitStack, but if your redis
            # client needs explicit closing, do it here (or register with stack)
            await main_app.state.redis.aclose()
            await get_container_connection_manager().close_all()


logging.basicConfig(level=logging.INFO)


# FastAPI app with lifespan context
#app = FastAPI(title="MissionControl API", version="0.1.0", lifespan=mcp_http_app.lifespan)
app = FastAPI(title="MissionControl API", version="0.1.0", lifespan=lifespan)

#app.mount("/mcp", mcp_http_app)

# Middleware configuration
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

