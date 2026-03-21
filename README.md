# mc | mission-control

Deploy your docker containers, compose stacks or swarm services with ease.

**Self-hosted, open-source, container orchestration PaaS built for maximum flexibility and control.**


## Quick start

### Prerequisites

- A Linux server with Docker installed (Ubuntu, Debian, CentOS, etc.).
- A domain name (optional but recommended for SSL and subdomain routing).


### Installation

Simply use the `install.sh` script to get started. 
It will start the `missioncontrol` container for you.

```bash
curl -fsSL https://raw.githubusercontent.com/fm-labs/mc/refs/heads/main/install.sh | bash
```

or using wget

```bash
wget -qO- https://raw.githubusercontent.com/fm-labs/mc/refs/heads/main/install.sh | bash
```

The initial admin credentials are printed in the terminal after you run the script, **for the first time**. 
Make sure to save them for your first login.

You can now access the web interface at `http://localhost:3080`.
(Replace `localhost` with your server's IP or domain if you're running it remotely.)

_Note: The installation script is designed to be run on a Linux server with Docker installed.
It is safe to run multiple times, but the initial credentials will only be printed the first time you run it._

## Next steps

1. Configure your root domain (required for SSL and subdomain routing).
2. Enable SSL (optional but recommended).
3. **Change the default password.** (Important for security!)
4. Start deploying your applications and services using the web interface.
5. Explore the documentation for advanced features and configuration options.
6. Join the community for support, tips, and sharing your projects.
7. Contribute to the project if you have ideas or improvements to share!
8. Enjoy the ease and power of managing your containers with Mission Control! 🚀




## Features

- [ ] Containers
  - [x] List containers
  - [x] Start container
  - [x] Pause container
  - [x] Unpause container (Start)
  - [x] Stop container
  - [x] Restart container
  - [x] Remove container
  - [x] Inspect container
  - [x] View logs
  - [x] View logstream (sse,jsonl)
  - [x] Execute command
  - [ ] Execute command in interactive shell (websocket)
- [ ] Images
  - [x] List images
  - [ ] Pull image
  - [x] Remove image
  - [ ] Inspect image
  - [ ] Remove image
- [ ] Networks
  - [x] List networks
  - [ ] Inspect network
- [x] Volumes
  - [x] List volumes
  - [ ] Inspect volume
- [ ] Compose Stacks
  - [ ] List compose stacks
    - [x] List compose stacks from local filesystem
    - [x] List compose stacks from container labels
  - [ ] Inspect compose stack
  - [x] Start compose stack (compose up)
  - [x] Stop compose stack (compose stop)
  - [x] Teardown compose stack (compose down)
  - [x] Add compose stack
    - [x] Add stack from compose file
    - [x] Add stack from github repository
- [ ] Secrets
  - [ ] List secrets
  - [ ] Inspect secret
  - [ ] Add secret
- [ ] Swarm
  - [ ] List nodes
  - [ ] Inspect node
  - [ ] Join swarm
  - [ ] Leave swarm
- [ ] Docker Engine
  - [x] Info
  - [x] Version
  - [x] Disk usage
  - [x] Events
  - [ ] Prune unused resources

- [ ] Low-level docker command invocation
  - [ ] docker top
  - [ ] docker ps
  - [ ] docker run
  - [ ] docker logs
  - [ ] docker compose
  - [ ] docker system prune

- [ ] Launch Templates / Launch Packs
  - [ ] Container 
    - [x] Launch container from template
  - [ ] Compose
    - [x] MissionControl launch packs (github-hosted stack folders)
    - [ ] List user-defined compose templates
    - [x] Add compose template
      - [x] Compose file upload
      - [x] Compose file url
      - [x] GitHub repository with compose file
  - [ ] 3rd-party Blueprints
    - [Z] Support for Portainer templates (github-hosted portainer template json files)

## Useful links

- [Docker Reference](https://docs.docker.com/reference/)
- [Docker SDK for Python](https://docker-py.readthedocs.io/en/stable/)
- [Docker SDK for Python API Reference](https://docker-py.readthedocs.io/en/stable/api.html)


## For developers

Please refer to the [DEVELOPER.md](DEVELOPER.md) file for guidelines on how to set up a development environment, 
contribute to the project, and run tests.