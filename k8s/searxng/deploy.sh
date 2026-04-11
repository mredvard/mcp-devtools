#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Creating namespace..."
kubectl apply -f "$SCRIPT_DIR/namespace.yaml"

echo "==> Creating configmap (SearXNG settings)..."
kubectl apply -f "$SCRIPT_DIR/configmap.yaml"

echo "==> Deploying SearXNG..."
kubectl apply -f "$SCRIPT_DIR/deployment.yaml"

echo "==> Creating ClusterIP service..."
kubectl apply -f "$SCRIPT_DIR/service.yaml"

echo "==> Waiting for pod to be ready..."
kubectl -n searxng rollout status deployment/searxng --timeout=120s

echo ""
echo "==> Deployment complete!"
echo "    Service DNS:      searxng.searxng.svc.cluster.local:8080"
echo "    Test JSON search: kubectl -n searxng exec -it deploy/searxng -- curl 'http://localhost:8080/search?q=test&format=json'"
echo "    Pod logs:         kubectl -n searxng logs -l app=searxng"
