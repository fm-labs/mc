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
- **Back up, restore and clone** volumes (RPC console or Tools).

## Apps

- Write a docker compose app in the browser (**Admin → Apps**) or with the CLI.
- Replace volumes with named volumes or host folders, and join extra networks, without editing the compose file.
- Set environment variables for `${VAR}` in the compose file. They're never written to the compose files.
- Route services to domains through Traefik, over HTTP and/or HTTPS.
- Start, restart, stop and remove the app with live `docker compose` output.
- See the generated compose files and the merged config before you run it.

## App stacks (obsolete)

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
- **Tools**: run built-in and your own commands (volume backup, Traefik start/stop, secret generator) with a form.
- API with token login or API key, for scripts and node-to-node access.
- **MCP server** (experimental) at `/mcp` for AI assistants, with a bearer token.
- HTTPS on port 3443 with a self-signed certificate out of the box, or your own.
