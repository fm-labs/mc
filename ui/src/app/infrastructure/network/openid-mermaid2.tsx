import Mermaid from "@/components/mermaid.tsx";

export default function OpenidMermaid2() {
    const dia = `
sequenceDiagram
    autonumber
    actor User as End-User
    participant Browser as User-Agent (Browser)
    participant Client as Client / Relying Party
    participant AS as OpenID Provider (Authorization Server)
    participant RS as Resource Server (optional)

    note over Client: Client prepares<br/>nonce + state + code_challenge

    User->>Browser: Visit "Login with OpenID Connect"
    Browser->>AS: GET /authorize?<br/>response_type=code<br/>client_id=...<br/>redirect_uri=...<br/>scope=openid email profile<br/>state=xyz<br/>nonce=abc
    AS->>User: Authenticate (password, SSO, etc.)
    User-->>AS: Approve access
    AS-->>Browser: 302 redirect to redirect_uri?<br/>code=AUTH_CODE&state=xyz
    Browser->>Client: Deliver code via redirect

    Client->>AS: POST /token<br/>grant_type=authorization_code<br/>code=AUTH_CODE<br/>redirect_uri=...<br/>client_id=...<br/>code_verifier=...
    AS-->>Client: 200 {<br/>"access_token": "...",<br/>"id_token": "JWT",<br/>"token_type": "Bearer",<br/>"expires_in": 3600,<br/>"refresh_token": "..."<br/>}

    note over Client: Verify ID Token (JWT)<br/>signature, iss, aud, exp, nonce

    Client->>Client: Decode ID Token<br/>extract claims (sub, name, email)
    opt Additional profile info
        Client->>AS: GET /userinfo<br/>Authorization: Bearer access_token
        AS-->>Client: { "sub": "...", "name": "Alice", "email": "alice@example.com" }
    end

    Client-->>Browser: Create user session<br/>Display "Welcome Alice!"

    rect rgba(200,200,200,0.15)
    note over Client,AS: Security checks<br/>✔ Verify state (anti-CSRF)<br/>✔ Verify nonce (anti-replay)<br/>✔ Verify token signature & claims
    end

`;
    return <Mermaid chart={dia} />
}
