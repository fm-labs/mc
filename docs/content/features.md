# Features

Mission Control (mc) is a self-hosted web UI for running containers and compose stacks on your own servers.
It runs as one container next to Docker.

## Container hosts

- Manage the local Docker engine, remote Docker engines (over SSH or TCP), Podman, and other mc instances ("nodes")
  from one UI.
- Connect and disconnect hosts per browser. Unreachable hosts don't slow down the rest.
- Overview of all hosts, plus cross-host **Stats** and a **Network** map of networks and containers.

## Containers

- List, start, stop, restart, pause, unpause and remove containers.
- Inspect: state, ports, env, labels, mounts, networks.
- Logs and live log stream.
- Run a command in a container.

## Images, volumes, networks

- List and inspect images, volumes and networks per host. Pull images.
- **Prune** unused containers, images, volumes, networks or build cache.
- Live Docker **events** per host.

## App stacks

- Deploy docker compose projects from a git repository (public or private, HTTPS or SSH).
- Set environment variables per stack; mc writes the `.env` file for you.
- Sync, deploy, redeploy and destroy from the UI.
- Optional Traefik routing: give a stack a domain and mc adds the labels for HTTP/HTTPS.
- Browse Portainer template lists for ideas (deploying from a template is not available yet).

## Inventory

- Store app stacks, container registries, SSH keys, secrets, variables and configurations.
- Forms and tables are generated from each type's schema, so new types appear automatically.

## Admin

- **Settings**: view (and optionally edit) `mc.conf.json` and the SSH config.
- **RPC console**: run admin commands like changing your password, Docker info, prune, and Swarm init/join/leave.
- API with token login or API key, for scripts and node-to-node access.
- HTTPS on port 3443 with a self-signed certificate out of the box, or your own.
