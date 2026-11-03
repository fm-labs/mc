# Deploy an app stack

An app stack is a docker compose project from a git repository. mc copies it, adds your settings, and runs it.

## 1. Prepare the repository

Put a compose file in a folder of a git repo:

```
my-stacks/
└── whoami/
    └── compose.yaml
```

```yaml
services:
  whoami:
    image: traefik/whoami
    ports:
      - "8081:80"
```

## 2. Create the stack

1. Open **Admin → Inventory → App Stack** and click **Create**.
2. Fill in:
   - **ID**: `whoami` (also the compose project name)
   - **Type**: `compose`
   - **Repository**: URL `https://github.com/<you>/my-stacks.git`, path `whoami`
   - **Stackfile**: `compose.yaml`
3. Save.

Private repo? Tick **private** and either add a username/password (HTTPS) or an `ssh_key_id` (SSH).
For SSH, the key must be at `/mc/etc/ssh_keys/<ssh_key_id>.pem` inside the mc container.

## 3. Sync, configure, deploy

Open the stack and run its actions in order:

1. **Sync Template**: fetches the repo and copies the folder into the stack's working dir.
2. **Configure Environment** (optional): set variables. mc writes them to the stack's `.env` file.
3. **Deploy Stack**: tick **Confirm** and run. mc runs `docker compose up -d` on the local Docker host.

Open `http://<your-server>:8081` to check, or find the containers under **Containers**.

## Update and remove

- **Redeploy Stack** with **Sync** ticked pulls the latest commit and redeploys.
- **Destroy Stack** runs `docker compose down`.

## Optional: route a domain with Traefik

If you already run Traefik on an external Docker network, set on the stack: **domain_name**,
**proxy_enabled**, **proxy_https_enabled**, **proxy_service_name** (`whoami`), **proxy_container_port** (`80`)
and **proxy_network_name** (your Traefik network). mc adds the Traefik labels on the next deploy.
Traefik needs `web`/`websecure` entrypoints and a cert resolver named `le`.

## Local changes

Put a `mc.override.yaml` in the stack's working dir (`/mc/apps/<id>`) for changes that shouldn't go into git.
It's applied on top of the compose file and survives a sync.

## Limits

- Stacks deploy to the local Docker host only.
- **Create from template** shows Portainer templates, but can't deploy them yet.
