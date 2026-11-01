from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from mc.config import MC_API_KEY
from mc.server.auth import get_user_from_api_key, get_user_from_jwt
from mc.server.auth_helper import verify_jwt_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
api_key_scheme = APIKeyHeader(name="x-api-key", auto_error=False)


def dep_auth_user(token: str | None = Security(oauth2_scheme),
                  api_key: str | None = Security(api_key_scheme)):

    err_headers = {"WWW-Authenticate": "Bearer"}
    if token is not None:
        try:
            payload = verify_jwt_access_token(token)
            return get_user_from_jwt(payload)
        except Exception as e:
            print("Token is invalid")
            raise HTTPException(status_code=401, detail="Invalid token", headers=err_headers) from e

    if api_key is not None:
        try:
            if MC_API_KEY is not None and len(MC_API_KEY) > 8 and api_key == MC_API_KEY:
                return get_user_from_api_key(api_key)
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid key", headers=err_headers) from e

    raise HTTPException(status_code=401, detail="Unauthenticated", headers=err_headers)
