from fastapi import APIRouter, Security

from inventorydb.routes import router as objbase_router
from mc.config import API_VERSION
from mc.plugin.containers.routes import router as containers_router
from mc.server.deps import dep_auth_user
from mc.server.routes_auth import router as auth_router
from mc.server.routes_config import router as config_router
from mc.server.routes_rpc import router as rpc_router
from mc.plugin.tools.routes import router as tools_router

# Enabled plugins and integrations
# PLUGINS_ENABLED = ["containers"]
# INVENTORY_ITEMS_ENABLED = ["app_stack", "container_registry", "mc_node"]

app_router = APIRouter()
# app_router.include_router(
#     inventory_router, prefix="/api", tags=["inventory"], dependencies=[Security(get_current_user)]
# )
app_router.include_router(auth_router, prefix="/api", tags=["auth"],
                          dependencies=[])
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


