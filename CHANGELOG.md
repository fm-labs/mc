# CHANGELOG

## Unreleased

- **Breaking:** data dir moved from `/var/lib/mc` to `/mc`; remount the data volume
- Added `MC_HOST_HOME`, `MC_DATA_VOLUME`, `DOCKER_HOME` to resolve the data dir on the host
- `install.sh` passes `MC_DATA_VOLUME` and `MC_HOST_HOME` to the container
- `mc-traefik-start.sh` uses the generated config files from `$MC_HOME/etc/traefik`
- Helper scripts moved to `/app/bin` (outside the data volume)
- UI uses a monospace font
- Added experimental node proxy: requests with an `x-mc-node` header are forwarded to that node (`MC_NODE_PROXY_ENABLED`)
- UI: tools, RPC, apps and settings moved under `/manage/:hostId` and run on that host (via the node proxy for nodes);
  open them from a host's `...` menu in the sidebar. Replaces `/admin/apps`, `/admin/rpc`, `/admin/tools` and `/settings`
- UI: tools and RPC pages use a two-column layout: searchable list on the left, details and form on the right

## v2.3.1

- Added volume backup/restore helpers and RPC methods
- Added network tree diagram
- Added host color-coding in the sidebar and a node icon
- Added cache store protocol with default TTL; caches are cleared after prune
- Added `app-builder` stage to the Dockerfile;
- Removed prune buttons from the host header

## v2.3.0

- Added container `top` endpoint and Top tab in the container view
- Switched JWT implementation from python-jose to PyJWT (iss/aud/nbf/jti claims, `kid` header)
- Upgraded to Python 3.14
- Added developer docs, user feature overview and quick-start guides
- Fixes, lint fixes and cleanup

## v2.2.1

- Added docker prune RPC/API endpoints and maintenance section
- Added network page and formatted docker resource views

## v2.2.0

- Added local config viewer/editor
- Added deep config merge, config escape hatches and pre-install hook
- Added host info summary and composite stats
- Updated dependencies; upgraded `actions/checkout` to v7

## v2.1.1

- Added ssh-agent helper scripts and SSH RPC methods
- Moved docker entrypoint to `/usr/local/bin`

