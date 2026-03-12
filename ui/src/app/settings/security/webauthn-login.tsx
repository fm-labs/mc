import React, {useState} from "react";
import {base64urlToBuffer, bufferToBase64url} from "./webauthn-helpers";
import {useApi} from "@/context/api-context.tsx";

export function WebauthnLogin() {
    const {api} = useApi()
    const [username, setUsername] = useState("foo");
    const [status, setStatus] = useState("");

    const handleLogin = async () => {
        setStatus("Requesting auth options...");

        const options = await api.post("/api/webauthn/auth/options", {
            username
        }).catch((err: any) => {
            setStatus(`Failed to get options: ${err.message}`);
        });

        // Convert challenge & allowCredentials[].id
        options.challenge = base64urlToBuffer(options.challenge);
        if (options.allowCredentials) {
            options.allowCredentials = options.allowCredentials.map((cred: any) => ({
                ...cred,
                id: base64urlToBuffer(cred.id),
            }));
        }

        setStatus("Requesting auth assertion...");

        const assertion: PublicKeyCredential = (await navigator.credentials.get({
            publicKey: options,
        })) as PublicKeyCredential;

        if (!assertion) {
            setStatus("Auth aborted by user");
            return;
        }

        const response = assertion.response as AuthenticatorAssertionResponse;

        const credForServer = {
            id: assertion.id,
            rawId: bufferToBase64url(assertion.rawId),
            type: assertion.type,
            response: {
                clientDataJSON: bufferToBase64url(response.clientDataJSON),
                authenticatorData: bufferToBase64url(response.authenticatorData),
                signature: bufferToBase64url(response.signature),
                userHandle: response.userHandle
                    ? bufferToBase64url(response.userHandle)
                    : null,
            },
            clientExtensionResults:
                (assertion.getClientExtensionResults &&
                    assertion.getClientExtensionResults()) ||
                {},
        };

        const data = await api.post("/api/webauthn/auth/verify", {
            username, credential: credForServer
        }).catch((err: any) => {
            setStatus(`Auth verification failed: ${err.message}`);
        });

        if (data) {
            setStatus(`Logged in as ${data.user_id} ✅`);
        } else {
            setStatus("Auth failed ❌");
        }
    };

    return (
        <div>
            <h2>Login with Passkey</h2>
            <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="username"
            />
            <button onClick={handleLogin} disabled={!username}>
                Login
            </button>
            <p>{status}</p>
        </div>
    );
}
