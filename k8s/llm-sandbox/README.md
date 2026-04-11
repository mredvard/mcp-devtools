# LLM Sandbox - Persistent Kali Linux on k3s

## Overview

A StatefulSet running Kali Linux with a fuse-overlayfs filesystem overlay. Any changes made inside the sandbox (apt install, file creation, etc.) persist across pod restarts via a PVC-backed overlay.

## Architecture

```
┌─────────────────────────────┐
│     /merged (chroot)        │  ← what the sandbox user sees
├─────────────────────────────┤
│  upper: /pvc/upper (PVC)    │  ← writable, persists all changes
│  lower: /rootfs (bind of /)  │  ← read-only Kali rolling image
└─────────────────────────────┘
```

- **fuse-overlayfs** mounts the base image as a read-only lower layer and the PVC as the writable upper layer
- The merged view at `/merged` is the union of both — reads fall through to the base image, writes go to the PVC
- The entrypoint chroots into `/merged` and runs socat on port 1234

## Components

| File | Purpose |
|---|---|
| `namespace.yaml` | `llm-sandbox` namespace |
| `fuse-device-plugin.yaml` | DaemonSet that provides `/dev/fuse` to pods without privileged mode |
| `configmap.yaml` | Entrypoint script — installs fuse-overlayfs, mounts overlay, starts socat |
| `statefulset.yaml` | Kali Linux pod pinned to `storage` node with 50Gi PVC |
| `service.yaml` | LoadBalancer exposing port 1234 |
| `deploy.sh` | Applies all manifests in order |

## Deployment

```bash
./k8s/llm-sandbox/deploy.sh
```

Or manually:

```bash
kubectl apply -f fuse-device-plugin.yaml
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f statefulset.yaml
kubectl apply -f service.yaml
```

## Connecting

Via socat (interactive shell through the overlay):

```bash
socat - TCP:192.168.60.4:1234
```

Via kubectl (lands in base container, NOT the overlay):

```bash
# To enter the overlay:
kubectl -n llm-sandbox exec -it llm-sandbox-0 -- chroot /merged /bin/bash

# This does NOT use the overlay (changes won't persist):
kubectl -n llm-sandbox exec -it llm-sandbox-0 -- /bin/bash
```

## Important: Persistence

- Files **only persist** if created inside the overlay (`/merged`)
- Connecting via socat on port 1234 = inside the overlay (persists)
- `kubectl exec` without `chroot /merged` = outside the overlay (ephemeral)
- The PVC at `/pvc/upper` contains all changes as a diff from the base image
- Deleting the pod or restarting the StatefulSet preserves data (PVC survives)
- Deleting the PVC (`workspace-llm-sandbox-0`) destroys all persisted changes

## Resource Limits

- **CPU**: 500m request / 1500m limit
- **Memory**: 512Mi request / 2Gi limit
- **Storage**: 50Gi PVC
- **Node**: pinned to `storage` (2 CPU, ~2Gi RAM, Alpine Linux, k3s agent)

## Security Model

- `SYS_ADMIN` capability is required for the FUSE mount() syscall
- The FUSE device plugin DaemonSet provides `/dev/fuse` without full privileged mode
- The container is not privileged — only `SYS_ADMIN` is added

## Startup Sequence

1. Pod starts with Kali Linux base image
2. Entrypoint runs `apt-get install fuse-overlayfs` (from base image, not persisted)
3. Non-recursive bind mount of `/` to `/rootfs` — strips submounts so `/rootfs/merged` is an empty dir, avoiding a FUSE deadlock (see below)
4. fuse-overlayfs mounts the overlay: lower=`/rootfs`, upper=`/pvc/upper`, merged=`/merged`
5. `/proc`, `/sys`, `/dev`, `/etc/resolv.conf` are bind-mounted into `/merged`
6. Chroot into `/merged`
7. socat starts listening on port 1234, spawning bash shells for each connection

## FUSE Deadlock (why lowerdir != /)

fuse-overlayfs is single-threaded. If `lowerdir=/`, the lower layer includes `/merged` — the FUSE mountpoint itself. When any command (e.g. `ls /`) triggers a `stat` on the `merged` entry, fuse-overlayfs tries to access `/merged` in the lower layer, which routes back through FUSE to itself. Single thread = permanent deadlock.

The fix: `mount --bind / /rootfs` creates a non-recursive bind where `/rootfs/merged` is just an empty mountpoint stub, not the live FUSE mount. Using `/rootfs` as lowerdir breaks the recursion.
