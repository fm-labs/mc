import Mermaid from "@/components/mermaid.tsx";

export default function OpenidMermaid() {
    const dia = `
sequenceDiagram
    autonumber
    actor User as End-User (Resource Owner)
    participant UA as User-Agent (Browser/App)
    participant RP as Relying Party (Client/App)
    participant OP as OpenID Provider (Auth Server)
    participant RS as Resource Server (API, optional)

    note over RP: Generate code_verifier & code_challenge (PKCE)
    note over RP: Prepare <br/>state & nonce for security

    User->>UA: Opens "Login with Example"
    UA->>OP: GET /authorize?<br/>response_type=code<br/>client_id=...<br/>redirect_uri=...<br/>scope=openid email profile<br/>state=xyz<br/>nonce=abc<br/>code_challenge=...
    OP->>User: Authenticate & consent
    User-->>OP: Submits credentials / approves
    OP-->>UA: Redirect to redirect_uri?<br/>code=AUTH_CODE&state=xyz
    UA->>RP: Deliver redirect (front-channel)

    RP->>OP: POST /token<br/>grant_type=authorization_code<br/>code=AUTH_CODE<br/>redirect_uri=...<br/>client_id=...<br/>code_verifier=...
    OP-->>RP: 200 OK<br/>{ "access_token": "...", "id_token": "...", "refresh_token": "..." }

    note over RP,OP: RP validates ID Token:<br/>verify signature (JWKS)<br/>check iss, aud, nonce, exp

    RP->>RP: Parse ID Token claims<br/>(sub, name, email, etc.)
    RP-->>UA: Establish session (user logged in)

    opt Fetch profile data
        RP->>OP: GET /userinfo<br/>Authorization: Bearer access_token
        OP-->>RP: 200 OK<br/>{ "sub": "...", "name": "Alice", "email": "alice@example.com" }
    end

    opt Access API
        RP->>RS: GET /api<br/>Authorization: Bearer access_token
        RS-->>RP: 200 Protected Resource
    end

`;
    return <Mermaid chart={dia} />
}
