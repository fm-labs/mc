import secrets
from typing import Annotated
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Body
from fastapi import HTTPException
from starlette.requests import Request

from mc.config import GITHUB_CLIENT_ID, GITHUB_AUTHORIZE_URL, GITHUB_CALLBACK_URL, \
    GITHUB_CLIENT_SECRET, GITHUB_ACCESS_TOKEN_URL
from mc.util.jwt_util import create_access_token1

gh_router = APIRouter()

@gh_router.get("/api/auth/login/github", tags=["auth"])
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


@gh_router.post("/api/auth/login/github", tags=["auth"])
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