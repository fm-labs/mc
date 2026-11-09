from fastapi import APIRouter, Security

from mc.plugin.apps.routes import router as apps_router
from mc.plugin.containers.routes import router as containers_router
from mc.plugin.tools.routes import router as tools_router
from mc.server.deps import dep_auth_user
from mc.server.routes_auth import router as auth_router
from mc.server.routes_config import router as config_router
from mc.server.routes_rpc import router as rpc_router
from mc.server.routes_system import router as system_router
from inventorydb.routes import router as objbase_router

API_PREFIX = "/api"

app_router = APIRouter()
app_router.include_router(system_router, prefix=API_PREFIX, tags=["system"],
                          dependencies=[])
app_router.include_router(auth_router, prefix=API_PREFIX, tags=["auth"],
                          dependencies=[])
app_router.include_router(rpc_router, prefix=API_PREFIX, tags=["rpc"],
                          dependencies=[Security(dep_auth_user)])
app_router.include_router(containers_router, prefix=API_PREFIX, tags=["container"],
                          dependencies=[Security(dep_auth_user)])
app_router.include_router(config_router, prefix=API_PREFIX, tags=["config"],
                          dependencies=[Security(dep_auth_user)])
app_router.include_router(tools_router, prefix=API_PREFIX, tags=["tools"],
                          dependencies=[Security(dep_auth_user)])
app_router.include_router(apps_router, prefix=API_PREFIX, tags=["apps"],
                          dependencies=[Security(dep_auth_user)])

app_router.include_router(objbase_router, prefix=API_PREFIX, tags=["inventory"],
                          dependencies=[Security(dep_auth_user)])

# Enabled plugins and integrations
# PLUGINS_ENABLED = ["containers"]
# INVENTORY_ITEMS_ENABLED = ["app_stack", "container_registry", "mc_node"]
#
# for plugin_name in PLUGINS_ENABLED:
#     try:
#         module = __import__(f"mc.plugin.{plugin_name}.routes", fromlist=["router"])
#     except ModuleNotFoundError:
#         continue
#
#     router = getattr(module, "router")
#     if router:
#         app_router.include_router(
#             router, prefix=API_PREFIX, tags=[plugin_name], dependencies=[Security(get_current_user)]
#         )


