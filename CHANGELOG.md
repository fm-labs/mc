# CHANGELOG

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

