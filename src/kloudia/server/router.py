from fastapi import APIRouter

from kloudia.server.routes.route_api import router as api_router
from kloudia.server.routes.route_repos import router as repos_router
from kloudia.server.routes.route_clouds import router as clouds_router
from kloudia.server.routes.route_findings import router as findings_router
from kloudia.server.routes.route_integrations import router as integrations_router


app_router = APIRouter()
app_router.include_router(api_router, prefix="/api/info", tags=["info"])
app_router.include_router(repos_router, prefix="/api/repos", tags=["repos"])
app_router.include_router(clouds_router, prefix="/api/clouds", tags=["clouds"])
app_router.include_router(findings_router, prefix="/api/findings", tags=["findings"])
app_router.include_router(integrations_router, prefix="/api/integrations", tags=["integrations"])

integrations = ["tools", "xscan", "orchestra", "cloudscan", "demo"]
for integration in integrations:
    try:
        module = __import__(f"kloudia.integrations.{integration}.routes", fromlist=["router"])
    except ModuleNotFoundError:
        continue

    router = getattr(module, "router")
    if router:
        app_router.include_router(router, prefix="/api", tags=['plugin ' + integration])