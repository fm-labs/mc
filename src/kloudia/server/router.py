from fastapi import APIRouter

from kloudia.server.routes.route_api import router as api_router
from kloudia.server.routes.route_repos import router as repos_router
from kloudia.server.routes.route_clouds import router as clouds_router
from kloudia.server.routes.route_findings import router as findings_router
from kloudia.server.routes.route_scans import router as scans_router
from orchestra.server.routes import router as orchestra_router


app_router = APIRouter()
app_router.include_router(api_router, prefix="/api/info", tags=["info"])
app_router.include_router(repos_router, prefix="/api/repos", tags=["repos"])
app_router.include_router(clouds_router, prefix="/api/clouds", tags=["clouds"])
app_router.include_router(findings_router, prefix="/api/findings", tags=["findings"])
app_router.include_router(scans_router, prefix="/api/scans", tags=["scans"])
app_router.include_router(orchestra_router, prefix="/api", tags=["orchestra"])
