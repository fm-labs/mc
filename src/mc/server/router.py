import secrets
from typing import Annotated
from urllib.parse import urlencode
import requests
from fastapi import APIRouter, Security, Body
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette.requests import Request

from mc.config import PLUGINS_ENABLED, GITHUB_CLIENT_ID, GITHUB_AUTHORIZE_URL, GITHUB_CALLBACK_URL, \
    GITHUB_CLIENT_SECRET, GITHUB_ACCESS_TOKEN_URL
from mc.server.auth import get_current_user
from mc.auth.users import authenticate_user
from mc.server.webauthn import router as webauthn_router
from mc.inventory.routes import router as inventory_router
from mc.findings.routes import router as findings_router
from mc.integrations.routes import router as integrations_router
from mc.plugin.orchestra.routes_sse import router as sse_router
from mc.plugin.orchestra.routes_infra import router as infra_router
from mc.util.jwt_util import create_access_token1

app_router = APIRouter()
app_router.include_router(sse_router, prefix="/sse", tags=["sse"])
app_router.include_router(infra_router, prefix="/api", tags=["infrastructure"]) #, dependencies=[Security(get_current_user)])
app_router.include_router(inventory_router, prefix="/api", tags=["inventory"], dependencies=[Security(get_current_user)])
app_router.include_router(findings_router, prefix="/api", tags=["findings"], dependencies=[Security(get_current_user)])
app_router.include_router(integrations_router, prefix="/api", tags=["integrations"], dependencies=[Security(get_current_user)])
app_router.include_router(webauthn_router, prefix="/api", tags=["webauthn"]) #, dependencies=[Security(get_current_user)])


for plugin_name in PLUGINS_ENABLED:
    try:
        module = __import__(f"mc.plugin.{plugin_name}.routes", fromlist=["router"])
    except ModuleNotFoundError:
        continue

    router = getattr(module, "router")
    if router:
        app_router.include_router(router, prefix="/api", tags=['plugin ' + plugin_name]) #, dependencies=[Security(get_current_user)])


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


@app_router.get("/api/auth/login/github", tags=["auth"])
def github_login(request: Request):
    state = secrets.token_urlsafe(16)
    #request.session["oauth_state"] = state

    # build authorize URL
    redirect_url = f"{GITHUB_CALLBACK_URL}"
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": redirect_url,
        "scope": "read:user user:email",
        "state": state
    }
    query_string_from_params = urlencode(params)
    full_url = f"{GITHUB_AUTHORIZE_URL}?{query_string_from_params}"
    return {"location": full_url}


@app_router.post("/api/auth/login/github", tags=["auth"])
def github_callback(request: Request, code: Annotated[str, Body()], state: Annotated[str, Body()]):
    """
    Exchange GitHub OAuth code for access token.
    https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps

    Accept: application/json
    {
      "access_token":"gho...",
      "scope":"repo,gist",
      "token_type":"bearer"
    }
    """
    # validate state
    #saved_state = request.session.get("oauth_state")
    #if not saved_state or saved_state != state:
    #    raise HTTPException(status_code=400, detail="Invalid state parameter")

    # exchange code for access token
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
        "state": state
    }
    endpoint_url = GITHUB_ACCESS_TOKEN_URL
    headers = {
        "Accept": "application/json"
    }
    print("GITHUB_ACCESS_TOKEN_REQUEST", params)
    raw_res = requests.post(endpoint_url, headers=headers, data=params)
    res = raw_res.json()
    print("GITHUB_ACCESS_TOKEN_RESPONSE", res)
    #GITHUB_ACCESS_TOKEN_RESPONSE {'access_token': '', 'token_type': 'bearer', 'scope': 'read:user,user:email'}
    if "error" in res:
        raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {res.get('error_description', 'unknown error')}")
    access_token = res["access_token"]
    token_type = res["token_type"]

    # fetch user info
    github_user = fetch_github_user_info(access_token)
    print("GITHUB_USER_INFO", github_user)
    # todo : register user if not exists
    if not github_user:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from GitHub")

    #github_user_email = fetch_github_user_primary_verified_email(access_token)
    #if github_user_email:
    #    github_user["email"] = github_user_email

    # create our own access token
    user = {
        "username": github_user.get("login"),
        #"email": github_user.get("email")
    }
    print("USER_INFO", user)
    if not user["username"]:
        raise HTTPException(status_code=400, detail="GitHub user has no username")

    token = create_access_token1(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}


def fetch_github_user_info(access_token: str) -> dict:
    """
    Fetch GitHub user info using the access token.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    user_info_url = "https://api.github.com/user"
    res = requests.get(user_info_url, headers=headers)
    if res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from GitHub")
    return res.json()


def fetch_github_user_primary_verified_email(access_token: str) -> str | None:
    r = requests.get(
        "https://api.github.com/user/emails",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        timeout=15,
    )
    if r.status_code != 200:
        return None

    emails = r.json() or []
    print("EMAILS", emails)
    # Prefer primary+verified; fall back to any verified; else None
    for e in emails:
        if e.get("primary") and e.get("verified"):
            return e.get("email")
    for e in emails:
        if e.get("verified"):
            return e.get("email")
    return None

@app_router.post("/api/auth/logout", tags=["auth"], dependencies=[Security(get_current_user)])
def logout():
    return {"status": "logged out"}


@app_router.get("/api/auth/user", tags=["auth"], dependencies=[Security(get_current_user)])
def me(current_user: dict = Depends(get_current_user)):
    return current_user
