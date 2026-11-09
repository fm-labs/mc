from typing import Annotated, Any

from fastapi import Depends, HTTPException, Security, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from mc.server.auth import AuthUser
from mc.server.auth_helper import create_jwt_access_token
from mc.server.deps import dep_auth_user
from mc.users import validate_login_form_credentials

router = APIRouter()

@router.post("/auth/login", tags=["auth"])
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> AuthUser:
    user = validate_login_form_credentials(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt_access_token(data={"sub": user.username})
    # todo refresh_token = create_refresh_token(user.username)
    return AuthUser(**{"username": user.username, "access_token": token, "token_type": "bearer"})



@router.post("/auth/logout", tags=["auth"], dependencies=[Security(dep_auth_user)])
def logout():
    raise HTTPException(status_code=401, detail="Logged out") # frontend resets auth session on 401


@router.get("/auth/user", tags=["auth"], dependencies=[Security(dep_auth_user)])
def me(current_user: Annotated[AuthUser, Depends(dep_auth_user)]) -> AuthUser:
    return current_user
