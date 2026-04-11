# SearXNG on Kubernetes

Self-hosted [SearXNG](https://docs.searxng.org/) metasearch engine deployed as a ClusterIP service. Aggregates results from Google, DuckDuckGo, Bing, Wikipedia, and others — no API keys required.

## Deploy

```bash
./deploy.sh
```

## Access

### From inside the cluster

The service is available at:

```
http://searxng.searxng.svc.cluster.local:8080
```

JSON search example:

```bash
curl 'http://searxng.searxng.svc.cluster.local:8080/search?q=hello&format=json'
```

### From outside the cluster

The service uses ClusterIP and is not directly exposed. Use `kubectl port-forward` to access it locally:

```bash
kubectl -n searxng port-forward svc/searxng 8080:8080
```

Then query at `http://localhost:8080`:

```bash
curl 'http://localhost:8080/search?q=hello&format=json'
```

## Configuration

Engine settings and search options are in `configmap.yaml`. After editing, reapply and restart:

```bash
kubectl apply -f configmap.yaml
kubectl -n searxng rollout restart deployment/searxng
```
