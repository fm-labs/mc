################################################################
# MISSION CONTROL SERVER
# MAIN SERVER FILE
#
# Run the server with:
#   uvicorn server:app
################################################################
import logging
import os
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

#from mc.db.redis import get_aioredis_client
from mc.mcp.app import mcp as mcp_app
from mc.mcp.fastmcp_helper import init_mcp_http_app
from mc.plugin.containers.manager import bootstrap_container_connection_manager
from mc.server.models import Problem
from mc.server.router import app_router
from mc.setup import setup_admin_auth

logging.basicConfig(level=logging.DEBUG)

# Load MCP server app with specified transport
mcp_enabled = os.getenv("MCP_ENABLED", "false").lower() == "true"
if mcp_enabled:
    mcp_transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    mcp_http_app = init_mcp_http_app(mcp_app, transport=mcp_transport)


@asynccontextmanager
async def lifespan(main_app: FastAPI):
    print("Setting up resources for main app lifespan...")
    setup_admin_auth()

    async with AsyncExitStack() as stack:
        #main_app.state.redis = get_aioredis_client()
        main_app.state.ccm = bootstrap_container_connection_manager()

        if mcp_enabled:
            # also enter the mounted app's lifespan:
            # this guarantees startup/shutdown even if the sub-app runs standalone elsewhere.
            await stack.enter_async_context(
                mcp_http_app.router.lifespan_context(mcp_http_app)
            )

        try:
            yield
        finally:
            main_app.state.ccm.close_all()
            #await main_app.state.redis.aclose()


app = FastAPI(title="MissionControl API", version="0.1.0", lifespan=lifespan)
#if mcp_enabled:
#app.mount("/mcp", mcp_http_app)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Global exception handlers that emit Problem JSON responses
@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    problem = Problem(error=exc.detail or exc.status_code,
                      status=exc.status_code,
                      detail=str(exc.detail))
    return JSONResponse(status_code=exc.status_code,
                        content=problem.model_dump(),
                        media_type="application/json")


# class NotFoundError(Exception):
#     def __init__(self, detail: str):
#         self.detail = detail

# @app.exception_handler(NotFoundError)
# async def not_found_handler(_: Request, exc: NotFoundError):
#     problem = Problem(title="Not Found", status=404, detail=exc.detail)
#     return JSONResponse(status_code=404, content=problem.model_dump(),
#                         media_type="application/problem+json")

# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(_: Request, exc: RequestValidationError):
#     problem = Problem(
#         error="Request validation error",
#         status=422,
#         detail="Request validation failed.",
#         #errors={"details": exc.errors()}
#     )
#     return JSONResponse(status_code=422, content=problem.model_dump(),
#                         media_type="application/problem+json")

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
