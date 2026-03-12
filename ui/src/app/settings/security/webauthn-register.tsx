import React, {useState} from "react";
import {base64urlToBuffer, bufferToBase64url} from "./webauthn-helpers";
import {useApi} from "@/context/api-context.tsx";

export function WebauthnRegister() {
    const {api} = useApi()
    const [username, setUsername] = useState("foo");
    const [status, setStatus] = useState("");

    const handleRegister = async () => {
        setStatus("Requesting options...");

        // 1. Get options from backend
        const options = await api.post("/api/webauthn/register/options", {username});
        console.log("Registration options:", options);

        // Convert challenge & user.id & excludeCredentials[].id to ArrayBuffer
        options.challenge = base64urlToBuffer(options.challenge);
        options.user.id = base64urlToBuffer(options.user.id);
        if (options.excludeCredentials) {
            options.excludeCredentials = options.excludeCredentials.map((cred: any) => ({
                ...cred,
                id: base64urlToBuffer(cred.id),
            }));
        }

        setStatus("Creating credential...");

        // 2. Call WebAuthn API
        const credential: PublicKeyCredential = (await navigator.credentials.create({
            publicKey: options,
        })) as PublicKeyCredential;

        if (!credential) {
            setStatus("User aborted");
            return;
        }

        const response = credential.response as AuthenticatorAttestationResponse;

        // 3. Send credential back to backend
        const credForServer = {
            id: credential.id,
            rawId: bufferToBase64url(credential.rawId),
            type: credential.type,
            response: {
                clientDataJSON: bufferToBase64url(response.clientDataJSON),
                attestationObject: bufferToBase64url(response.attestationObject),
            },
            clientExtensionResults:
                (credential.getClientExtensionResults &&
                    credential.getClientExtensionResults()) ||
                {},
        };

        console.log("Credential to send to server:", credForServer);
        setStatus("Verifying credential...");
        const verifyData = await api.post("/api/webauthn/register/verify", {
            username,
            credential: credForServer,
        }).catch((e: any) => {
            console.log("Verification error:", e);
            return null;
        });

        console.log("Verification response:", verifyData);
        if (!verifyData) {
            setStatus(`Registration failed`);
            return;
        }

        setStatus("Passkey registered 🎉");
    };

    return (
        <div>
            <h2>Register Passkey</h2>
            <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="username"
            />
            <button onClick={handleRegister} disabled={!username}>
                Register
            </button>
            <p>{status}</p>
        </div>
    );
}
