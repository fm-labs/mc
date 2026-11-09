from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from mc.server.auth import authenticate_user_with_api_key, authenticate_user_with_jwt_token, AuthUser
from mc.server.auth_helper import verify_jwt_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
api_key_scheme = APIKeyHeader(name="x-api-key", auto_error=False)


def dep_auth_user(token: str | None = Security(oauth2_scheme),
                  api_key: str | None = Security(api_key_scheme)) -> AuthUser:

    err_headers = {"WWW-Authenticate": "Bearer"}
    if token is not None:
        try:
            return authenticate_user_with_jwt_token(token)
        except Exception as e:
            print("Token is invalid")
            raise HTTPException(status_code=401, detail="Invalid token", headers=err_headers) from e

    if api_key is not None and api_key != "":
        try:
            return authenticate_user_with_api_key(api_key)
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid key", headers=err_headers) from e

    raise HTTPException(status_code=401, detail="Unauthenticated", headers=err_headers)
