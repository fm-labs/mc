import Mermaid from "@/components/mermaid.tsx";

export default function OauthMermaid() {
    const arch = `
sequenceDiagram
    autonumber
    actor User as Resource Owner (User)
    participant UA as User-Agent (Browser/App)
    participant Client as Client (Your App)
    participant AS as Authorization Server
    participant RS as Resource Server (API)

    note over Client: Generate code_verifier & code_challenge (PKCE)

    User->>UA: Open app / click "Login"
    UA->>AS: GET /authorize?<br/>response_type=code<br/>client_id=...<br/>redirect_uri=...<br/>scope=...<br/>state=...<br/>code_challenge=...<br/>code_challenge_method=S256
    AS->>User: Login & Consent UI
    User-->>AS: Authenticate & grant consent
    AS-->>UA: 302 redirect to redirect_uri?<br/>code=AUTH_CODE&state=...
    UA->>Client: Deliver redirect (front/back channel)

    Client->>AS: POST /token<br/>grant_type=authorization_code<br/>code=AUTH_CODE<br/>redirect_uri=...<br/>client_id=...<br/>code_verifier=...
    AS-->>Client: 200 { access_token, token_type, expires_in, [refresh_token], [id_token] }

    Client->>RS: GET /resource<br/>Authorization: Bearer ACCESS_TOKEN
    RS-->>Client: 200 Protected Resource
    Client-->>UA: Show user’s data

    opt Access token expires
        Client->>AS: POST /token<br/>grant_type=refresh_token<br/>refresh_token=...
        AS-->>Client: 200 { new access_token, [new refresh_token] }
    end

    rect rgba(200,200,200,0.15)
    note over Client,AS: Security checks
    Client->>Client: Verify returned state matches request (CSRF)
    AS->>Client: PKCE: validate code_verifier vs code_challenge
    end

`;
    return <Mermaid chart={arch} />
}
