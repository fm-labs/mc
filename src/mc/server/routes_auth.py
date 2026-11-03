from typing import Annotated, Any

from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordRequestForm

from mc.server.auth_helper import create_jwt_access_token
from mc.server.deps import dep_auth_user
from mc.server.router import app_router
from mc.users import authenticate_user


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
