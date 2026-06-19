# NAGP Kubernetes Multi-Tier App

FastAPI service + PostgreSQL database running on Kubernetes with auto-scaling and self-healing.

## Links

- **Code:** https://github.com/priyanka-dhamija/forcastra-nagp-assignment
- **Docker Image:** ECR (see buildspec.yml for details)
- **API:** http://localhost:8000/api/employees

## Setup

```bash
kubectl apply -f k8s/
```

## Test It

```bash
# Port forward
kubectl port-forward svc/nagp-api-service 8000:80 -n nagp

# Get employees
curl http://localhost:8000/api/employees

# Health check
curl http://localhost:8000/health
```

## What's Running

- 4 API pods (FastAPI) - auto-scales 2-8 based on load
- 1 database pod (PostgreSQL) - 8 employee records, persistent storage
- Ingress (AWS ALB) - external access
- HPA - auto-scaling based on CPU/memory
- Secrets - database password encrypted
- ConfigMap - database config externalized

## Features

- Self-healing (pods restart automatically)
- Data persistence (survives pod deletion)
- Rolling updates (zero-downtime)
- No hardcoded passwords
- No hardcoded Pod IPs (uses Kubernetes DNS)
- Cost optimized (50% resource reduction)

## Test Self-Healing

```bash
# Delete an API pod
kubectl delete pod <pod-name> -n nagp

# New one creates automatically
kubectl get pods -n nagp --watch
```

## Test Data Persistence

```bash
# Delete database pod
kubectl delete pod <postgres-pod> -n nagp

# Data still there after recovery
kubectl exec -it <new-pod> -n nagp -- psql -U postgres -d nagpdb -c "SELECT COUNT(*) FROM employees;"
# Shows: 8
```

## Files

```
k8s/              - Kubernetes YAML files
app/              - FastAPI app, Dockerfile, requirements
buildspec.yml     - CI/CD pipeline
```

## How It Works

Request → ALB Ingress → API Service → API Pod → Database Service → PostgreSQL → EBS Volume

## Cleanup

```bash
kubectl delete namespace nagp
```

---

See COMPREHENSIVE_DOCUMENTATION.md for details.
