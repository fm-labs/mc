from fastapi import APIRouter

from kloudia.server.route_findings import router as findings_router
from kloudia.server.route_integrations import router as integrations_router
from kloudia.inventory.routes import router as inventory_router


app_router = APIRouter()

#app_router.include_router(repos_router, prefix="/api/inventory/repos", tags=["inventory", "repos"])
#app_router.include_router(clouds_router, prefix="/api/inventory/clouds", tags=["inventory", "clouds"])
app_router.include_router(inventory_router, prefix="/api/inventory", tags=["inventory"])
app_router.include_router(findings_router, prefix="/api/findings", tags=["findings"])
app_router.include_router(integrations_router, prefix="/api/integrations", tags=["integrations"])


# inventories = ["repos", "clouds"]
# for inventory in inventories:
#     try:
#         module = __import__(f"kloudia.inventory.{inventory}.routes", fromlist=["router"])
#     except ModuleNotFoundError:
#         continue
#
#     router = getattr(module, "router")
#     if router:
#         app_router.include_router(router, prefix="/api", tags=['inventory ' + inventory])



plugins = ["tools", "xscan", "orchestra", "cloudscan", "demo"]
for plugin in plugins:
    try:
        module = __import__(f"kloudia.plugin.{plugin}.routes", fromlist=["router"])
    except ModuleNotFoundError:
        continue

    router = getattr(module, "router")
    if router:
        app_router.include_router(router, prefix="/api", tags=['plugin ' + plugin])



@app_router.get("/", tags=["info"])
async def info() -> dict:
    return dict({
        "name": "Kloudia API Service",
        "status": "running",
        "version": "0.1.0",
    })

@app_router.get("/health", tags=["info"])
async def health():
    return {"status": "OK"}