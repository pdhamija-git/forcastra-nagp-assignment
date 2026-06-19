# NAGP - Multi-Tier Kubernetes Architecture

A simple multi-tier application running on Kubernetes with an API service tier and PostgreSQL database tier.

## What's Inside

**API Service:** FastAPI application that exposes employee data via REST API  
**Database:** PostgreSQL with 8 employee records  
**Orchestration:** Kubernetes on AWS EKS with auto-scaling and self-healing

## Quick Links

- **Repository:** https://github.com/priyanka-dhamija/forcastra-nagp-assignment
- **Docker Image:** https://hub.docker.com/r/priyankadhamija/nagp-api
- **API Endpoint (Local):** http://localhost:8000/api/employees
- **Documentation:** See COMPREHENSIVE_DOCUMENTATION.md

## Getting Started

### Prerequisites
- kubectl configured for EKS cluster
- AWS EKS cluster running
- 4+ CPU and 512Mi memory available

### Deploy

```bash
# Create namespace and deploy all resources
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/

# Verify deployment
kubectl get all -n nagp
```

### Access the API

**Option 1: Port Forward (for testing)**
```bash
kubectl port-forward svc/nagp-api-service 8000:80 -n nagp
curl http://localhost:8000/api/employees
```

**Option 2: Via ALB (production)**
```bash
# Get ALB DNS
kubectl get ingress -n nagp -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}'

# Access API
curl http://<ALB-HOSTNAME>/api/employees
```

## API Endpoints

- `GET /` - Root endpoint with documentation
- `GET /health` - Health check (verifies DB connection)
- `GET /api/employees` - Get all employees (8 records)

## What's Running

**4 API Pods**
- FastAPI on port 3000
- Load balanced via Kubernetes Service
- Auto-scales from 2-8 pods based on CPU/memory
- Requests: 50m CPU, 64Mi memory
- Limits: 200m CPU, 256Mi memory

**1 Database Pod**
- PostgreSQL 15 on port 5432
- Persistent storage (1Gi EBS volume)
- Internal access only (ClusterIP)
- Data survives pod restarts

## Key Features

✅ **Self-Healing** - Pods automatically restart if they fail  
✅ **Data Persistence** - Database data survives pod deletion  
✅ **Auto-Scaling** - HPA scales pods based on load  
✅ **Rolling Updates** - Zero-downtime deployments  
✅ **Secure Config** - Passwords in encrypted Secrets, config in ConfigMap  
✅ **External Access** - Exposed via AWS ALB Ingress  
✅ **Service DNS** - No hardcoded Pod IPs, uses Kubernetes DNS  
✅ **Cost Optimized** - 50% resource reduction, efficient scaling

## Kubernetes Resources

**Deployments:**
- `nagp-api` - 4 replicas of FastAPI
- `postgres` - 1 replica of PostgreSQL

**Services:**
- `nagp-api-service` - Internal load balancer for API (port 80 → 3000)
- `postgres-service` - Internal database access (port 5432)

**Ingress:**
- `nagp-api-ingress` - AWS ALB for external access

**Storage:**
- `postgres-pvc` - 1Gi persistent volume for database

**Config:**
- `api-config` - ConfigMap with database parameters (DB_HOST, DB_PORT, DB_NAME)
- `db-secret` - Kubernetes Secret with database password (encrypted)
- `postgres-init-sql` - ConfigMap with database initialization script

**Scaling:**
- `nagp-api-hpa` - Auto-scaler (min 2, max 8 pods)

**Resilience:**
- `nagp-api-pdb` - Pod Disruption Budget (min 2 pods always available)

## Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Get Employees
```bash
curl http://localhost:8000/api/employees | jq '.'
```

Expected response: 8 employee records with id, name, department, role, salary, location

### Test Self-Healing
```bash
# Delete an API pod
kubectl delete pod <pod-name> -n nagp

# Watch recovery
kubectl get pods -n nagp --watch
# New pod creates automatically in ~20 seconds
```

### Test Data Persistence
```bash
# Delete database pod
kubectl delete pod <postgres-pod-name> -n nagp

# Verify data survived
kubectl get pods -n nagp -l app=postgres  # New pod created
kubectl exec -it <new-pod> -n nagp -- psql -U postgres -d nagpdb -c "SELECT COUNT(*) FROM employees;"
# Output: 8 records still there
```

## Files Explained

```
k8s/
├── 00-namespace.yaml              - Create nagp namespace
├── 02-api-pod-disruption-budget.yaml
├── 03-postgres-init-configmap.yaml - Database schema + 8 records
├── 04-postgres-pvc.yaml           - Persistent storage (1Gi)
├── 05-postgres-deployment.yaml    - PostgreSQL pod
├── 06-postgres-service.yaml       - Internal database access
├── 07-api-deployment.yaml         - 4 API pods
├── 08-api-service.yaml            - Load balancer for API
├── 09-api-hpa.yaml                - Auto-scaler (2-8 pods)
└── 10-api-ingress.yaml            - AWS ALB for external access

app/
├── main.py                        - FastAPI application
├── Dockerfile                     - Container image
└── requirements.txt               - Python dependencies

buildspec.yml                      - CI/CD pipeline (builds & deploys)
```

## How It Works

1. **Request comes in** → AWS ALB Ingress
2. **Ingress routes to** → nagp-api-service (load balancer)
3. **Service selects** → One of 4 API pods
4. **API pod processes** → Reads config from ConfigMap, password from Secret
5. **API connects to** → postgres-service (Kubernetes DNS)
6. **Service routes to** → PostgreSQL pod
7. **Database queries** → Data stored on persistent volume
8. **Response returns** → JSON with 8 employee records

## Cost Optimization

- **Resource Requests:** 50m CPU / 64Mi memory per API pod (50% reduction)
- **HPA:** Scales down when not busy, scales up on demand
- **Pod Disruption Budget:** Prevents unnecessary pod churn during maintenance
- **Actual savings:** ~50% resource reduction, smart scaling prevents over-provisioning

## Configuration

### ConfigMap (Non-Sensitive)
Located in: `app/main.py` reads from environment

```
DB_HOST=postgres-service.nagp.svc.cluster.local
DB_PORT=5432
DB_NAME=nagpdb
PORT=3000
```

### Secrets (Encrypted)
```
DB_USER=postgres
DB_PASSWORD=[encrypted]
POSTGRES_DB=nagpdb
```

No passwords are hardcoded in YAML files or code. All sensitive data is in encrypted Kubernetes Secrets.

## Troubleshooting

### API pods not starting?
```bash
kubectl describe pod <pod-name> -n nagp
kubectl logs <pod-name> -n nagp
```

### Can't connect to database?
```bash
# Verify database pod is running
kubectl get pods -n nagp -l app=postgres

# Check ConfigMap has correct values
kubectl get configmap api-config -n nagp -o yaml
```

### Data lost after pod restart?
Check PVC is bound and mounted:
```bash
kubectl get pvc -n nagp
kubectl describe pvc postgres-pvc -n nagp
```

### ALB not provisioning?
Verify subnets are tagged with `kubernetes.io/role/elb=1` (AWS requirement for ALB)

## Cleanup

To delete everything:
```bash
kubectl delete namespace nagp
```

This removes all pods, services, and persistent volumes. Data on the EBS volume will be retained unless the PVC is explicitly deleted.

## Notes

- First time setup takes ~2 minutes for all pods to be ready
- ALB provisioning can take 2-5 minutes on first deploy
- Database initializes automatically on first pod start
- Health endpoint confirms database connectivity, not just pod status

---

For more details, see COMPREHENSIVE_DOCUMENTATION.md
