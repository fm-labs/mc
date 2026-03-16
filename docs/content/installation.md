# Installation

## Prerequisites

- Linux Host with Docker installed
- Docker Compose installed


## Install script

```bash
curl -sSL https://raw.githubusercontent.com/fm-labs/mc/main/install.sh | bash
```

or using wget

```bash
wget -qO- https://raw.githubusercontent.com/fm-labs/mc/main/install.sh | bash
```

## Manual installation

```bash
docker container run -d \
  --name mc \
  -p 3080:3080 \
  -p 80:80 \
  -p 443:443 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v mc_data:/app/data \
  --restart unless-stopped \
  fmlabs/mc:latest
```



## Running as a non-root user

If you want to run the container as a non-root user, 
you probably need to add the group ID (GID) of the local docket socket when running the container. 

**Note:** This does **NOT** refer to a rootless-docker setup, but rather to running the container with a 
**local** non-root user on a system where Docker is running as root. 
The non-root user needs to have permissions to access the Docker socket, which is typically owned by the `docker` group.


To find your docker socket's GID, you can run the following command in your terminal:

```bash
stat -c '%g' /var/run/docker.sock
```

Then, you can use that GID in the `--group-add` option when running the container.

```bash
docker container run -d \
  --name mc \
  -p 3080:3080 \
  -p 80:80 \
  -p 443:443 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v mc_data:/app/data \
  --group-add $(stat -c '%g' /var/run/docker.sock) \
  --restart unless-stopped \
  fmlabs/mc:latest
```
