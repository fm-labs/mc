import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt  # PyJWT

#from jose import ExpiredSignatureError, JWTError, jwt  # deprecated
#from jose.exceptions import JWTClaimsError  # deprecated
from mc.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_AUDIENCE, JWT_ISSUER, JWT_SECRET_KEY

#######################################
###    PYJWT IMPLEMENTATION         ###
#######################################


def create_jwt_access_token(data: dict) -> str:
    claims = data.copy()
    claims.update({
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "nbf": datetime.now(UTC),
        "jti": str(uuid.uuid4()),
    })

    # kid is the md5 hash of the secret key
    kid = hashlib.md5(str(JWT_SECRET_KEY).encode()).hexdigest()[:16]

    headers = {
        #"alg": JWT_ALGORITHM,
        "kid": kid
    }
    token = pyjwt.encode(claims, key=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM, headers=headers)
    return token


def verify_jwt_access_token(token: str) -> dict:
    try:
        #headers = jwt.get_unverified_header(token)
        #kid = headers.get("kid")
        claims = pyjwt.decode(
            token, JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],  # pins the algorithm, important!
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={"require": ["exp", "iss", "sub", "aud", "iat", "nbf", "jti"]},
        )
        return claims
    except pyjwt.InvalidTokenError as e:  # covers expired, bad sig, wrong iss, etc.
        raise ValueError("Invalid token") from e



#######################################
### JOSE IMPLEMENTATION (DEPRECATED ###
#######################################

# def create_access_token(data: dict):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
#
#
# def verify_access_token(token: str) -> dict:
#     try:
#         payload = jwt.decode(
#             token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"require_exp": True, "require_sub": True}
#         )
#
#         print("Token payload:", payload)
#         # validate token expiration (the JWT library does this automatically)
#         # if payload.get("exp") is None:
#         #    raise HTTPException(status_code=401, detail="Token has no expiration", headers=err_headers)
#         # validate subject
#         # if payload.get("sub") is None:
#         #    raise HTTPException(status_code=401, detail="Token has no subject", headers=err_headers)
#
#     except ExpiredSignatureError as e:
#         print("Token expired")
#         raise
#     except JWTClaimsError as e:
#         print("Token has invalid claims")
#         raise
#     except JWTError as e:
#         print("Token is invalid")
#         raise
#     return payload


# def create_refresh_token(subject: str | Any, expires_delta: int = None) -> str:
#     if expires_delta is not None:
#         expires_delta = datetime.utcnow() + timedelta(minutes=expires_delta)
#     else:
#         expires_delta = datetime.utcnow() + timedelta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
#
#     to_encode = {"exp": expires_delta, "sub": str(subject)}
#     encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, JWT_ALGORITHM)
#     return encoded_jwt
