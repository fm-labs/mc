# Setup Guide

## Prerequisites

- Linux Host with Docker installed
- Docker Compose installed
- On every node you also need docker installed


## Quickstart

### Primary Host Setup

First, we want to setup the primary mission control host.

**If the primary host is on a remote host, SSH into it.**

```bash
# Replace <user> and <primary-mc-host> with your username and the hostname or IP address of the primary mission control host
ssh <user>@<primary-mc-host>
```

**If the primary host is the local machine your are on**

you can skip the SSH step.

**Install mc container using the install script**

```bash
curl -sSL https://raw.githubusercontent.com/fm-labs/mc/main/install.sh | bash
```

See [Installation Guide](./installation.md) for more information


### Node Setup

If you want to connect additional nodes to the primary mission control host, follow these steps:

For each node,
- SSH into the node host
- Run the install script on every node with export MC_MODE=node ; curl ...
- Edit `/etc/mc/mc.conf.json`
  - Add MC_API_KEY env variable (more than 8 characters)

Then, on the primary host:
- Edit `/etc/mc/mc.conf.json`
  - Add each node to `docker_hosts`:
    ```json
    { "docker_hosts": { "node1": { "url": "node+https://node1:3443", "api_key": "<MC_API_KEY of node1>" } } }
    ```
- Restart mc

See [Container hosts](./container-hosts.md) for all options.



## Setup with docker compose

Example docker compose setup for a primary host


```yaml
services:
  
  mc:
    image: fmlabs/mc:latest
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "mc-data:/opt/mc"

volumes:
  mc-data:

```