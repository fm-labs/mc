# Connect more hosts

mc can manage Docker on other servers. Hosts are listed in the `docker_hosts` section of `mc.conf.json`.

## Edit the config

The easiest way is the **Settings** page. It's read-only until you allow edits:

```bash
echo "MC_API_CONF_MC_WRITABLE=1" | sudo tee -a /etc/mc/docker.env
curl -fsSL https://raw.githubusercontent.com/fm-labs/mc/refs/heads/main/install.sh | bash   # restart with the new env
```

Then open **Settings → Mission Control**, edit, and save. Restart mc after saving (`docker restart mc`), since
the config is read at startup.

## Option A: Docker over SSH

Good for a few servers you can SSH into.

```json
{
  "docker_hosts": {
    "web1": { "url": "ssh://deploy@web1.example.com" }
  }
}
```

mc needs an SSH key that can log in to `web1`, and the user needs access to Docker there. Keys are loaded from
`/home/app/.ssh` inside the container at startup, so mount a folder with your key there, e.g. in
`/etc/mc/install.env`:

```bash
MC_EXTRA_VOLUMES="-v /etc/mc/ssh:/home/app/.ssh"
```

Make the key file readable by uid 33333 (the container user), then re-run `install.sh`.

## Option B: Another mc instance (node)

Good when the other server should run its own mc. The primary talks to the node's API with an API key.

**On the node:**

```bash
echo "MC_API_KEY=$(openssl rand -hex 24)" | sudo tee -a /etc/mc/docker.env
curl -fsSL https://raw.githubusercontent.com/fm-labs/mc/refs/heads/main/install.sh | bash
sudo cat /etc/mc/docker.env   # copy the key
```

**On the primary**, add the node:

```json
{
  "docker_hosts": {
    "node1": { "url": "node+https://node1.example.com:3443", "api_key": "<the key>" }
  }
}
```

## Other host types

| URL | Host |
|---|---|
| `unix:///var/run/docker.sock` | Local Docker (the default `localhost`) |
| `tcp://10.0.0.5:2375` | Docker over TCP |
| `podman+unix:///run/podman/podman.sock` | Podman |

Add `"autoconnect": true` to a host to connect it in the UI by default.

## Use it

Restart mc, open **Containers**, and click **Connect** on the new host. If it shows **Disconnected**, check that
the host is reachable from the mc container and the key or API key is right.
