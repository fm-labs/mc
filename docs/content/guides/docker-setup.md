# Docker setup

Get Docker onto a fresh Ubuntu or Debian server so you can [install mc](getting-started.md). Skip this if `docker version`
already shows a client and a server.

## 1. Run the install-docker script

```bash
curl -fsSL https://raw.githubusercontent.com/fm-labs/mc/refs/heads/main/install-docker.sh | sudo bash
```

The script:

- only runs on Ubuntu and Debian (it checks `/etc/os-release` and stops on anything else)
- adds Docker's apt repository for your distribution and its signing key (`/etc/apt/keyrings/docker.asc`)
- installs the Docker engine (`docker-ce`, `containerd.io`), the CLI, and the Buildx and Compose plugins
- starts Docker and enables it on boot
- prints the Docker and Compose versions and checks that the engine is running

It needs root, so pipe it to `sudo bash`. It's safe to run again.

## 2. Check it works

```bash
sudo docker run --rm hello-world
```

## 3. Add a user for Docker

Run Docker, and the mc install script, as a normal user instead of root. Create one (here `mc`) and add it
to the `docker` group, so it can use `docker` without `sudo`:

```bash
sudo adduser --disabled-password --gecos "" mc
sudo usermod -aG docker mc
```

Switch to the new user and check it can reach Docker:

```bash
sudo -iu mc
docker run --rm hello-world
```

To use an existing account instead, run `sudo usermod -aG docker <user>`, then log out and back in so the group
change applies.

Members of the `docker` group effectively have root on the host, because they can start containers that mount
the host's filesystem. Only add users you trust, and don't give this user `sudo`.

## 4. Set up SSH keys for the user

The `mc` user has no password, so it logs in with an SSH key. You need this to log in as the user, and for
another mc to manage this server's Docker over SSH (see [Connect more hosts](connect-hosts.md)).

On the machine you connect **from** (your laptop, or the server running the other mc), create a key pair:

```bash
ssh-keygen -t ed25519 -C "mc@<this-server>" -f ~/.ssh/mc_ed25519
```

Leave the passphrase empty if mc will use the key, since it can't type one. This writes the private key
`~/.ssh/mc_ed25519` (keep it there, never copy it to the server) and the public key `~/.ssh/mc_ed25519.pub`.

On the Docker server, add the public key to the user's `authorized_keys`, logged in with your admin account:

```bash
sudo install -d -m 700 -o mc -g mc /home/mc/.ssh
echo "<contents of mc_ed25519.pub>" | sudo tee -a /home/mc/.ssh/authorized_keys
sudo chown mc:mc /home/mc/.ssh/authorized_keys
sudo chmod 600 /home/mc/.ssh/authorized_keys
```

SSH ignores the file if `.ssh` or `authorized_keys` can be written by other users, so keep those permissions.
`ssh-copy-id` won't work here, because it needs to log in as `mc` first.

Back on the machine you connect from, check the key works and the user can reach Docker:

```bash
ssh -i ~/.ssh/mc_ed25519 mc@<this-server> docker version
```

## Other distributions

For Fedora, RHEL and others, follow Docker's [install guide](https://docs.docker.com/engine/install/).

## Next

[Getting started](getting-started.md): install mc as this user and log in.
