from fastapi import Security, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from jose.exceptions import JWTClaimsError
from passlib.context import CryptContext

from mc.util.jwt_util import JWT_ALGORITHM, JWT_SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

fake_users_db = {
    "johndoe@example.org": {
        "username": "johndoe@example.org",
        "hashed_password": pwd_context.hash("secret"),
    }
}

def lookup_user(username: str) -> dict:
    user = fake_users_db.get(username)
    return user

def verify_password(plain_password, hashed_password):
    if not plain_password or not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, plain_password: str):
    user = lookup_user(username)
    if not user or not verify_password(plain_password, user.get("hashed_password")):
        return False
    return user


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Security(oauth2_scheme)):
    err_headers = {"WWW-Authenticate": "Bearer"}
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM],
                             options={"require_exp": True, "require_sub": True})

        # validate token expiration (the JWT library does this automatically)
        #if payload.get("exp") is None:
        #    raise HTTPException(status_code=401, detail="Token has no expiration", headers=err_headers)
        # validate subject
        #if payload.get("sub") is None:
        #    raise HTTPException(status_code=401, detail="Token has no subject", headers=err_headers)

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired", headers=err_headers)
    except JWTClaimsError:
        raise HTTPException(status_code=401, detail="Invalid token: invalid claims", headers=err_headers)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token", headers=err_headers)
    return {"username": payload.get("sub")}
