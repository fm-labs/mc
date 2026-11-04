# Deploy an app

An app is a docker compose project you write in mc. mc stores it, adds your volumes, networks, routing and
environment variables, and runs it on the local Docker host. Field details are in the
[App specification](../apps.md).

## 1. Create the app

1. Open **Admin → Apps** and click **New app**.
2. Fill in:
   - **Id**: `whoami`. Also the compose project name; it can't be changed later.
   - **Title** (optional): `Who am I`
3. Replace the example in **compose.yaml**:

   ```yaml
   services:
     whoami:
       image: traefik/whoami:${WHOAMI_VERSION:-latest}
       ports:
         - "8081:80"
   ```

4. Click **Create app**.

## 2. Start it

Under **Run**, click **Up**. The output of `docker compose` appears below the buttons.

Open `http://<your-server>:8081` to check, or find the container under **Containers**.

**Restart**, **Stop** and **Down** work the same way. **Down** removes the containers but keeps volumes.
The buttons are disabled while you have unsaved changes.

## 3. Configure

Each section is applied when you click **Save**. Run **Up** again afterwards to apply the change to running
containers.

- **Volumes**: replace a volume of the compose file with a named volume or a folder on the host.
- **Networks**: join every service to extra networks, e.g. an existing `external` network.
- **Environment**: set variables for `${NAME}` in compose.yaml. Try `WHOAMI_VERSION` = `v1.10`. Variables used in
  compose.yaml but not set yet are offered as buttons.
- **Routing**: serve a service on a domain through Traefik (below).

Save shows a warning when part of the spec can't be applied, e.g. a route to a service that doesn't exist.

To see what will actually run, click **Compiled** at the top. The **Merged** tab shows `docker compose config`:
all files combined, with variables filled in.

## Optional: route a domain with Traefik

You need Traefik running on an external Docker network named `traefik-ssl`, with entrypoints `web` and
`websecure` and a certificate resolver named `le`.

1. Under **Routing**, click **Add route**.
2. **Service**: `whoami`, **Port**: `80`, **Protocol**: `HTTPS`, **Domains**: `whoami.example.com`.
3. **Save**, then **Up**.

The `ports:` entry isn't needed for routing; you can remove it.

## From the command line

The same steps with the CLI (see [CLI](../apps.md#cli)):

```bash
mc-cli apps create whoami -f compose.yaml --title "Who am I"
mc-cli apps env set whoami WHOAMI_VERSION=v1.10
mc-cli apps up whoami
```

For volumes, networks and routing, use `mc-cli apps edit whoami`.

## Limits

- Apps run on the local Docker host only.
- Apps can't be deleted from the UI yet. Run **Down**, then remove `$MC_CONFIG_DIR/apps/<id>.yaml` and
  `$MC_HOME/apps/<id>/`.
- Creating an app from a bundle or template isn't available yet.
