from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWTClaimsError

from mc.config import MC_API_KEY
from mc.util.jwt_util import JWT_ALGORITHM, JWT_SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

api_key_scheme = APIKeyHeader(name="x-api-key", auto_error=False)

def get_current_user(token: str | None = Security(oauth2_scheme), api_key: str | None = Security(api_key_scheme)):
    err_headers = {"WWW-Authenticate": "Bearer"}
    if token is not None:
        try:
            payload = jwt.decode(
                token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"require_exp": True, "require_sub": True}
            )

            print("Token payload:", payload)
            # validate token expiration (the JWT library does this automatically)
            # if payload.get("exp") is None:
            #    raise HTTPException(status_code=401, detail="Token has no expiration", headers=err_headers)
            # validate subject
            # if payload.get("sub") is None:
            #    raise HTTPException(status_code=401, detail="Token has no subject", headers=err_headers)

        except ExpiredSignatureError as e:
            print("Token expired")
            raise HTTPException(status_code=401, detail="Token has expired", headers=err_headers) from e
        except JWTClaimsError as e:
            print("Token has invalid claims")
            raise HTTPException(status_code=401, detail="Invalid token: invalid claims", headers=err_headers) from e
        except JWTError as e:
            print("Token is invalid")
            raise HTTPException(status_code=401, detail="Invalid token", headers=err_headers) from e
        return {"username": payload.get("sub")}

    if api_key is not None:
        err_headers = {"WWW-Authenticate": "Bearer"}
        if MC_API_KEY is not None and len(MC_API_KEY) > 8 and api_key == MC_API_KEY:
            return {"username": "api-key-user"}
        raise HTTPException(status_code=401, detail="Invalid key", headers=err_headers)

    raise HTTPException(status_code=401, detail="Unauthenticated", headers=err_headers)