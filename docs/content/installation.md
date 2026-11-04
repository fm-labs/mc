# Installation

## Prerequisites

- Linux Host with Docker installed
- Docker Compose installed

On Ubuntu and Debian, the `install-docker.sh` script installs Docker and Docker Compose. See [Docker setup](guides/docker-setup.md).


## Install script

```bash
curl -sSL https://raw.githubusercontent.com/fm-labs/mc/main/install.sh | bash
```

or using wget

```bash
wget -qO- https://raw.githubusercontent.com/fm-labs/mc/main/install.sh | bash
```

## Upgrading from v2.3.x and older

The data directory moved from `/var/lib/mc` to `/mc`. Remount your existing volume at the new path,
e.g. `-v mc-data:/mc` instead of `-v mc-data:/var/lib/mc`.

If the volume isn't named `mc_data`, set `MC_DATA_VOLUME=<name>` (named volume) or
`MC_HOST_HOME=<host path>` (bind mount), so mc can find its data on the host.

## Manual installation

```bash
docker container run -d \
  --name mc \
  -p 3080:3080 \
  -p 3443:3443 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v mc_data:/mc \
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
  -p 3443:3443 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v mc_data:/mc \
  --restart unless-stopped \
  --group-add $(stat -c '%g' /var/run/docker.sock) \
  fmlabs/mc:latest
```

## Using a local bind mount volume

```bash
docker container run -d \
  --name mc \
  -p 3080:3080 \
  -p 3443:3443 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /srv/custom/path/to/mc:/mc \
  -e "MC_HOST_HOME=/srv/custom/path/to/mc" \
  --restart unless-stopped \
  --group-add $(stat -c '%g' /var/run/docker.sock) \
  fmlabs/mc:latest
```


### Data directory permission issues

The container user/group IDs are set to `33333:33333` by default.

If you encounter permission issues with the data directory, you can change the ownership of the directory to match the container's user/group IDs.

```bash
sudo chown -R 33333:33333 /srv/custom/path/to/mc
```


## Using custom SSL certificates

SSL certificates can be customized by mounting your own certificate and key files to the container.

This is how nginx is configured:
```text
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
```

### Mount cert and key

```bash
docker container run -d \
  --name mc \
  -p 3080:3080 \
  -p 3443:3443 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v mc_data:/mc \
  -v /path/to/my/certs/mycert.pem:/etc/nginx/ssl/cert.pem:ro \
  -v /path/to/my/keys/mykey.pem:/etc/nginx/ssl/key.pem:ro \
  --restart unless-stopped \
  --group-add $(stat -c '%g' /var/run/docker.sock) \
  fmlabs/mc:latest
```

### Custom SSL cert location

```bash
docker container run -d \
  --name mc \
  -p 3080:3080 \
  -p 3443:3443 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v mc_data:/mc \
  -v /path/to/my/ssl:/etc/my/ssl:ro \
  -e MC_SSL_CERT_FILE=/etc/my/ssl/server.crt \
  -e MC_SSL_KEY_FILE=/etc/my/ssl/server.key \
  --restart unless-stopped \
  --group-add $(stat -c '%g' /var/run/docker.sock) \
  fmlabs/mc:latest
```