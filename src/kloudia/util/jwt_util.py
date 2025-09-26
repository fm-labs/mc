from datetime import datetime, timedelta
import os
from typing import Union, Any

from jose import jwt

def generate_random_jwt_secret_key(length: int = 32) -> str:
    import secrets
    return secrets.token_urlsafe(length)

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 60 minutes
JWT_REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days
JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', default="mysupersecretkey") # default=generate_random_jwt_secret_key())   # should be kept secret
JWT_REFRESH_SECRET_KEY = os.environ.get('JWT_REFRESH_SECRET_KEY', default="mysupersecretrefreshkey") # default=generate_random_jwt_secret_key())    # should be kept secret



def create_access_token1(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, JWT_ALGORITHM)
    return encoded_jwt