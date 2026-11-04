# Secure your install

A short checklist after the first login.

## Change the default password

**RPC → `user.change_password`**. See [Getting started](getting-started.md#4-change-the-password).

## Keep logins across restarts

Login tokens are signed with a key that's random per start unless you set one, so restarting mc logs everyone out.
Set a fixed key:

```bash
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" | sudo tee -a /etc/mc/docker.env
```

Re-run `install.sh` to apply.

## Use your own TLS certificate

mc serves HTTPS on port 3443 with a self-signed certificate. To use your own, mount it in `/etc/mc/install.env`:

```bash
MC_DOCKER_EXTRA_VOLUMES="-v /etc/mc/tls/fullchain.pem:/etc/nginx/ssl/cert.pem:ro -v /etc/mc/tls/privkey.pem:/etc/nginx/ssl/key.pem:ro"
```

Re-run `install.sh`. Then close port 3080 in your firewall or put mc behind your own reverse proxy.

## Keep config read-only

Only set `MC_API_CONF_MC_WRITABLE=1` / `MC_API_CONF_SSH_WRITABLE=1` while you edit config in the UI, then remove
them again.

## Protect API keys

`MC_API_KEY` gives full API access to a node. Use a long random value and only reach nodes over HTTPS.

## Back up

Everything mc stores is in the `mc-data` volume (`/mc`): config, users, inventory and stack working dirs.
Back it up like any Docker volume.
