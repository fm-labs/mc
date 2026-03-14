from fastapi import APIRouter, Security
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from mc.users import authenticate_user
from mc.config import PLUGINS_ENABLED
from mc.inventory.routes import router as inventory_router
from mc.server.routes_rpc import router as rpc_router
from mc.server.auth import get_current_user
from mc.util.jwt_util import create_access_token1

app_router = APIRouter()
app_router.include_router(inventory_router, prefix="/api", tags=["inventory"], dependencies=[Security(get_current_user)])
app_router.include_router(rpc_router, prefix="/api", tags=["rpc"], dependencies=[Security(get_current_user)])

#app_router.include_router(findings_router, prefix="/api", tags=["findings"], dependencies=[Security(get_current_user)])
#app_router.include_router(sse_router, prefix="/sse", tags=["sse"])
#app_router.include_router(infra_router, prefix="/api", tags=["infrastructure"]) #, dependencies=[Security(get_current_user)])


for plugin_name in PLUGINS_ENABLED:
    try:
        module = __import__(f"mc.plugin.{plugin_name}.routes", fromlist=["router"])
    except ModuleNotFoundError:
        continue

    router = getattr(module, "router")
    if router:
        app_router.include_router(router, prefix="/api", tags=[plugin_name], dependencies=[Security(get_current_user)])


@app_router.get("/api/info", tags=["info"])
async def info() -> dict:
    return {"version": "0.1.0"}


@app_router.get("/api/health", tags=["info"])
async def health():
    return {"status": "OK"}


@app_router.post("/api/auth/login", tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token1(data={"sub": user["username"]})
    #refresh_token = create_refresh_token(user["username"])
    return {"access_token": token, "token_type": "bearer"}


@app_router.post("/api/auth/logout", tags=["auth"], dependencies=[Security(get_current_user)])
def logout():
    return {"status": "logged out"}


@app_router.get("/api/auth/user", tags=["auth"], dependencies=[Security(get_current_user)])
def me(current_user: dict = Depends(get_current_user)):
    return current_user
