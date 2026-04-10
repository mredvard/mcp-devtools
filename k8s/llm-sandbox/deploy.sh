#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Deploying FUSE device plugin..."
kubectl apply -f "$SCRIPT_DIR/fuse-device-plugin.yaml"

echo "==> Creating namespace..."
kubectl apply -f "$SCRIPT_DIR/namespace.yaml"

echo "==> Creating configmap (entrypoint script)..."
kubectl apply -f "$SCRIPT_DIR/configmap.yaml"

echo "==> Deploying StatefulSet..."
kubectl apply -f "$SCRIPT_DIR/statefulset.yaml"

echo "==> Creating LoadBalancer service..."
kubectl apply -f "$SCRIPT_DIR/service.yaml"

echo "==> Waiting for pod to be ready..."
kubectl -n llm-sandbox rollout status statefulset/llm-sandbox --timeout=300s

echo ""
echo "==> Deployment complete!"
echo "    Get external IP:  kubectl -n llm-sandbox get svc llm-sandbox"
echo "    Connect:          socat - TCP:<EXTERNAL-IP>:1234"
echo "    Pod logs:         kubectl -n llm-sandbox logs llm-sandbox-0"
echo "    Shell into pod:   kubectl -n llm-sandbox exec -it llm-sandbox-0 -- /bin/bash"
