from joserfc import jwe, jwt
from joserfc._rfc7519.claims import JWTClaimsRegistry
from joserfc.jwk import OctKey

if __name__ == "__main__":

    # generate 128-bit symmetric key with secrets
    import secrets
    key_bytes = secrets.token_bytes(16)  # 16 bytes = 128 bits
    print("Key Bytes:", key_bytes)
    # as hex
    key_hex = key_bytes.hex()
    print("Key Bytes (hex):", key_hex)
    # hex to bytes
    key_bytes = bytes.fromhex(key_hex)
    print("Key Bytes (from hex):", key_bytes)


    # restore an
    key = OctKey.import_key(key_bytes)

    header = {"alg": "A128KW", "enc": "A128GCM"}
    #key = OctKey.generate_key(128)  # algorithm requires key of big size 128
    print("Key:", key)
    print("Key (JWK):", key.as_dict())

    data = jwe.encrypt_compact(header, "hello", key)
    print("JWE Compact:", data)

    obj = jwe.decrypt_compact(data, key)
    # obj.protected => {"alg": "A128KW", "enc": "A128GCM"}
    # obj.plaintext => b"hello"

    print("JWE Decrypt:", obj)
    print("Protected Header:", obj.protected)
    print("Plaintext:", obj.plaintext.decode())


    ###
    # encode a JWT using JWE
    claims = {
        "sub": "1234567890",
        "name": "John Doe",
        "admin": True
    }
    registry = jwe.JWERegistry()  # YOU MUST USE A JWERegistry
    jwe_token = jwt.encode(header, claims, key, registry=registry)
    print("JWE Token:", jwe_token)

    # decode the JWE JWT
    #claims_requests = JWTClaimsRegistry(aud={"essential": True})
    decoded_jwt = jwt.decode(jwe_token, key, registry=registry)
    print("Decoded JWE JWT Claims:", decoded_jwt.claims)

