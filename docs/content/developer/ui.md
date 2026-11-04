# UI

React 19, TypeScript, Vite, Tailwind 4 and shadcn/ui (`ui/src/components/ui`, don't edit these; wrap them).
Forms from JSON schema use `@rjsf/shadcn`. Tables use TanStack Table.

```bash
cd ui && pnpm install && pnpm run dev   # http://localhost:3081
pnpm run build                         # tsc + vite build -> ui/dist
```

The backend serves `ui/dist` (`MC_UI_HTML_DIR`) at `/`, so after a build the UI is also on port 3080.

## Layout

| Path | Contents |
|---|---|
| `src/main.tsx`, `App.tsx` | Providers: theme, API, auth, app context |
| `src/app-router.tsx` | All routes |
| `src/app/<area>/` | Pages per area, with their own `components/` |
| `src/components/` | Shared components, layouts (`layout/`), data table, forms |
| `src/context/` | `api-context` (API client), `auth-context` (token), `theme-provider` |
| `src/features/` | Types and helpers per domain (docker, inventory, tasks, ...) |
| `src/lib/api-client.ts` | Typed API calls, built on an axios client (`api-http-client.ts`) |
| `src/constants.ts` | API base URL, template URLs |

## Routing

`createHashRouter`, so URLs look like `/#/containers/localhost`. Pages are imported with top-level `await import()`.

| Route | Page |
|---|---|
| `/auth/login` | Login |
| `/dashboard` | Dashboard |
| `/containers` | All container hosts |
| `/containers/:hostId/:view?` | One host: `container` (default), `images`, `volumes`, `networks`, `engine`, `events` |
| `/containers/:hostId/container/:containerId` | Container detail (inspect, logs, exec, env, mounts, ...) |
| `/containers/stats`, `/containers/network` | Stats and network graph across connected hosts |
| `/stacks`, `/stacks/details/:stackId` | App stacks (obsolete) |
| `/stacks/portainer` | Browse Portainer template lists |
| `/settings` | Edit `mc.conf.json` and `ssh_config` |
| `/admin/apps`, `/admin/apps/new`, `/admin/apps/:appId` | Apps: list, create, edit and run (see [Apps](apps.md#ui)) |
| `/admin/rpc` | Run RPC methods |
| `/admin/inventory/:itemType[/:itemId]` | Generated inventory pages (see [Inventory UI](inventory-ui.md)) |

Everything except `/` and `/auth/*` is wrapped in `AuthenticatedRoute` (`AuthBoundary`), which requires a login.

## Data and state

- `api-context` builds the API client for `MC_API_BASE_URL`. `auth-context` keeps the JWT in `localStorage`
  and adds it to requests. A `401` response logs out (interceptor in `api-http-client.ts`).
- Container pages use providers (`container-hosts-provider`, `container-host-provider`,
  `docker-container-provider`) that load data for the selected host and expose it through hooks.
- Whether a host is connected is a per-browser setting (`localStorage` key `container_host_<alias>_enabled`).

## Known gaps

- The Portainer templates page lists templates, but **Deploy** doesn't create a stack yet.
- The `kitchensink` page and `findings` nav entries are dev/demo content.
