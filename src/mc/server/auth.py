from dataclasses import dataclass

from mc import config
from mc.server.auth_helper import verify_jwt_access_token


@dataclass
class AuthUser:
    username: str
    token_type: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None

def authenticate_user_with_jwt_token(token: str) -> AuthUser:
    claims = verify_jwt_access_token(token) # raises
    if not claims or not claims.get("sub"):
        raise ValueError("Invalid token")
    return AuthUser(username=claims.get("sub"), token_type="bearer")

def authenticate_user_with_api_key(api_key: str) -> AuthUser:
    # read at call time so config changes (and test patches) are picked up
    mc_api_key = config.MC_API_KEY
    if mc_api_key is not None and len(mc_api_key) > 32 and api_key == mc_api_key:
        return AuthUser(username="api-key-user", token_type="api-key")
    raise ValueError("Invalid API key")