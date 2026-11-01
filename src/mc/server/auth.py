
def get_user_from_jwt(claims: dict):
    return {"username": claims.get("sub")}

def get_user_from_api_key(api_key: str):
    return {"username": "api-key-user"}


