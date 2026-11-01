# Getting started

Install mc, log in, and change the default password. Takes about five minutes.

You need a Linux server with Docker.

## 1. Install

```bash
curl -fsSL https://raw.githubusercontent.com/fm-labs/mc/refs/heads/main/install.sh | bash
```

This pulls `fmlabs/mc:latest` and starts a container named `mc` with your Docker socket and a `mc-data` volume.
Running it again updates mc to the latest image; your data stays in the volume.

## 2. Get the admin password

On the first start, mc creates the user `operator` with a random password and writes it to the log once:

```bash
docker logs mc 2>&1 | grep "Admin user"
```

Save it. It's not shown again.

## 3. Log in

Open `http://<your-server>:3080` (or `https://<your-server>:3443`, which uses a self-signed certificate,
so your browser will warn once). Log in as `operator`.

## 4. Change the password

1. Open **RPC** in the sidebar.
2. Pick `user.change_password`.
3. Enter `operator`, the old password, and the new one twice. Run it.

## 5. Look around

- **Containers** shows your local Docker host as `localhost`. Click **Connect** to load it.
- Next: [Connect more hosts](connect-hosts.md) or [deploy an app stack](deploy-app-stack.md).

## Custom install options

`install.sh` reads these env vars (or `/etc/mc/install.env`, if it exists):

| Variable | Default |
|---|---|
| `MC_PORT` / `MC_PORT_SSL` | `3080` / `3443` |
| `MC_CONTAINER_NAME` | `mc` |
| `MC_DATA_VOLUME` | `mc-data` |
| `MC_IMAGE` | `fmlabs/mc:latest` |
| `MC_EXTRA_VOLUMES` | extra `-v` options (set in `install.env`) |

Env vars for mc itself go in `/etc/mc/docker.env`; the script passes it with `--env-file`.
