from dataclasses import dataclass

from mc.config import MC_API_KEY
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
    if MC_API_KEY is not None and len(MC_API_KEY) > 32 and api_key == MC_API_KEY:
        return AuthUser(username="api-key-user", token_type="api-key")
    raise ValueError("Invalid API key")