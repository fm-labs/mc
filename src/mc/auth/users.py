from passlib.context import CryptContext

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
