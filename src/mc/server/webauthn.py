from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.requests import Request
from webauthn.authentication.verify_authentication_response import VerifiedAuthentication
from webauthn.registration.verify_registration_response import VerifiedRegistration

from mc.server.webauthn_util import webauthn_get_user, webauthn_get_challenge, webauthn_get_credentials, \
    webauthn_remove_challenge, webauthn_store_challenge, \
    webauthn_add_credential, webauthn_add_user

RP_ID = "localhost"  # must match origin's effective domain
RP_NAME = "Dev"
ORIGIN = "http://localhost:1420"  # must match the origin used in the frontend

from webauthn import generate_registration_options, generate_authentication_options, base64url_to_bytes
from webauthn import verify_registration_response, verify_authentication_response
from webauthn.helpers import options_to_json, options_to_json_dict, bytes_to_base64url
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidRegistrationResponse
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement, PublicKeyCredentialDescriptor, UserVerificationRequirement,
    PublicKeyCredentialCreationOptions, PublicKeyCredentialType, PublicKeyCredentialRequestOptions,
)

router = APIRouter()

class RegisterOptionsRequest(BaseModel):
    username: str

class RegisterVerifyRequest(BaseModel):
    username: str
    credential: Dict[str, Any]  # the whole response from navigator.credentials.create()

class AuthOptionsRequest(BaseModel):
    username: str

class AuthVerifyRequest(BaseModel):
    username: str
    credential: Dict[str, Any]  # from navigator.credentials.get()


@router.post("/webauthn/register/options")
def register_options(req: RegisterOptionsRequest) -> Dict[str, Any]:
    # 1. Look up or create user
    user = webauthn_get_user(req.username)
    if not user:
        user = {
            "id": req.username,  # use stable unique ID
            "username": req.username,
            "display_name": req.username,
        }
        webauthn_add_user(user["id"], user)

    # 2. Existing credentials for exclude list
    existing_creds = webauthn_get_credentials(user["id"])
    exclude_credentials: list[PublicKeyCredentialDescriptor] = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(cred["id"]),
                                      type=PublicKeyCredentialType.PUBLIC_KEY)
        for cred in existing_creds
    ]

    options: PublicKeyCredentialCreationOptions = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=user["id"].encode("utf-8"),
        user_name=user["username"],
        user_display_name=user["display_name"],
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        exclude_credentials=exclude_credentials,
    )

    # Store the challenge temporarily
    webauthn_store_challenge(user["username"], options.challenge)

    return options_to_json_dict(options)


@router.post("/webauthn/register/verify")
def register_verify(req: RegisterVerifyRequest, request: Request):
    # print the raw fastapi request body
    print("Starlette request body:", request)
    print("Register verify request:", req)


    expected_challenge = webauthn_get_challenge(req.username)
    if not expected_challenge:
        raise HTTPException(status_code=400, detail="No challenge for user")

    try:
        verification: VerifiedRegistration = verify_registration_response(
            credential=req.credential,
            expected_challenge=expected_challenge,
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            require_user_verification=False,
        )
        print(verification)
    except InvalidRegistrationResponse as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {e}")

    # Store credential
    user = webauthn_get_user(req.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    webauthn_add_credential(user["id"],{
                                "id": bytes_to_base64url(verification.credential_id),
                                "public_key": bytes_to_base64url(verification.credential_public_key),
                                "sign_count": verification.sign_count,})

    # Remove challenge
    webauthn_remove_challenge(req.username)

    # Return your own session/JWT if you want
    return {"status": "ok"}


@router.post("/webauthn/auth/options")
def auth_options(req: AuthOptionsRequest):
    user = webauthn_get_user(req.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    creds = webauthn_get_credentials(user["id"])
    if not creds:
        raise HTTPException(status_code=400, detail="No credentials for user")

    allow_credentials = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(cred["id"]),
                                      type=PublicKeyCredentialType.PUBLIC_KEY)
        for cred in creds
    ]

    options: PublicKeyCredentialRequestOptions = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    webauthn_store_challenge(user["username"], options.challenge)

    return options_to_json_dict(options)


@router.post("/webauthn/auth/verify")
def auth_verify(req: AuthVerifyRequest):
    print("Auth verify request:", req)

    user = webauthn_get_user(req.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    expected_challenge = webauthn_get_challenge(req.username)
    if not expected_challenge:
        raise HTTPException(status_code=400, detail="No challenge")

    # Find the stored credential by id
    stored_creds = webauthn_get_credentials(user["id"])
    stored_cred = next(
        (c for c in stored_creds if c["id"] == req.credential["id"]), None
    )
    if not stored_cred:
        raise HTTPException(status_code=400, detail="Unknown credential")

    try:
        verification: VerifiedAuthentication = verify_authentication_response(
            credential=req.credential,
            expected_challenge=expected_challenge,
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            credential_public_key=base64url_to_bytes(stored_cred["public_key"]),
            credential_current_sign_count=stored_cred["sign_count"],
            require_user_verification=False,
        )

    except InvalidAuthenticationResponse as e:
        raise HTTPException(status_code=400, detail=f"Auth failed: {e}")

    # Update sign_count
    stored_cred["sign_count"] = verification.new_sign_count

    webauthn_remove_challenge(req.username)

    # Issue your session/JWT
    return {"status": "ok", "user_id": user["id"], "cnt": verification.new_sign_count}
