# Manage containers

## Find a container

1. Open **Containers** and **Connect** the host.
2. The host page has tabs: **Containers**, **Images**, **Volumes**, **Networks**, **Engine**, **Events**.
3. Click a container to expand it. It shows tabs: **Logs** (live), **Inspect**, **Labels**, **Mounts**,
   **Environment**, **Networks**, **Paths**, **Exec**.

## Day-to-day tasks

| Task | Where |
|---|---|
| Start, stop, restart, pause | Control buttons on the container |
| Follow logs | **Logs** tab (streams live while open) |
| Run a command | **Exec** tab |
| Check env, mounts, networks | The matching tab |
| Pull an image | Host page → **Images** |
| See what changed on a host | Host page → **Events** |
| Compare hosts | **Containers → Stats** |
| See which containers share a network | **Containers → Network** |

## Free up disk space

On the host page, use **Prune** and pick what to remove: stopped containers, unused images, volumes, networks or
build cache. Pruning volumes deletes their data, so check first.
