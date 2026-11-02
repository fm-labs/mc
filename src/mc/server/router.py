from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordRequestForm

from inventorydb.routes import router as objbase_router
from mc.config import API_VERSION
from mc.plugin.containers.routes import router as containers_router
from mc.server.auth_helper import create_jwt_access_token
from mc.server.deps import dep_auth_user
from mc.server.routes_config import router as config_router
from mc.server.routes_rpc import router as rpc_router
from mc.plugin.tools.routes import router as tools_router
from mc.users import authenticate_user

# Enabled plugins and integrations
PLUGINS_ENABLED = ["containers"]
# INVENTORY_ITEMS_ENABLED = ["app_stack", "container_registry", "mc_node"]

app_router = APIRouter()
# app_router.include_router(
#     inventory_router, prefix="/api", tags=["inventory"], dependencies=[Security(get_current_user)]
# )
app_router.include_router(objbase_router, prefix="/api", tags=["inventory"],
                          dependencies=[Security(dep_auth_user)])
app_router.include_router(rpc_router, prefix="/api", tags=["rpc"],
                          dependencies=[Security(dep_auth_user)])
app_router.include_router(containers_router, prefix="/api", tags=["container"],
                          dependencies=[Security(dep_auth_user)])
app_router.include_router(config_router, prefix="/api", tags=["config"],
                          dependencies=[Security(dep_auth_user)])
app_router.include_router(tools_router, prefix="/api", tags=["tools"],
                          dependencies=[Security(dep_auth_user)])

# for plugin_name in PLUGINS_ENABLED:
#     try:
#         module = __import__(f"mc.plugin.{plugin_name}.routes", fromlist=["router"])
#     except ModuleNotFoundError:
#         continue
#
#     router = getattr(module, "router")
#     if router:
#         app_router.include_router(
#             router, prefix="/api", tags=[plugin_name], dependencies=[Security(get_current_user)]
#         )


@app_router.get("/api/info", tags=["system"])
def info() -> dict:
    return {"version": API_VERSION}


@app_router.get("/api/health", tags=["system"])
def health():
    return {"status": "OK"}


@app_router.post("/api/auth/login", tags=["auth"])
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt_access_token(data={"sub": user.username})
    # refresh_token = create_refresh_token(user.username)
    return {"access_token": token, "token_type": "bearer"}


@app_router.post("/api/auth/logout", tags=["auth"], dependencies=[Security(dep_auth_user)])
def logout():
    return {"status": "logged out"}


@app_router.get("/api/auth/user", tags=["auth"], dependencies=[Security(dep_auth_user)])
def me(current_user: Annotated[dict[str, Any], Depends(dep_auth_user)]):
    return current_user
