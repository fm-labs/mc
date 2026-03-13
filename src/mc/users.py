from passlib.context import CryptContext

from mc.config import MC_ADMIN_EMAIL, MC_ADMIN_PASSWORD

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users_db = {
    MC_ADMIN_EMAIL: {
        "username": MC_ADMIN_EMAIL,
        "hashed_password": pwd_context.hash(MC_ADMIN_PASSWORD),
    }
}

def lookup_user(username: str) -> dict:
    user = users_db.get(username)
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
