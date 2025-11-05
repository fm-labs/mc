from fastapi import Security, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from jose.exceptions import JWTClaimsError

from mc.util.jwt_util import JWT_ALGORITHM, JWT_SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Security(oauth2_scheme)):
    err_headers = {"WWW-Authenticate": "Bearer"}
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM],
                             options={"require_exp": True, "require_sub": True})

        print("Token payload:", payload)
        # validate token expiration (the JWT library does this automatically)
        #if payload.get("exp") is None:
        #    raise HTTPException(status_code=401, detail="Token has no expiration", headers=err_headers)
        # validate subject
        #if payload.get("sub") is None:
        #    raise HTTPException(status_code=401, detail="Token has no subject", headers=err_headers)

    except ExpiredSignatureError:
        print("Token expired")
        raise HTTPException(status_code=401, detail="Token has expired", headers=err_headers)
    except JWTClaimsError:
        print("Token has invalid claims")
        raise HTTPException(status_code=401, detail="Invalid token: invalid claims", headers=err_headers)
    except JWTError:
        print("Token is invalid")
        raise HTTPException(status_code=401, detail="Invalid token", headers=err_headers)
    return {"username": payload.get("sub")}
