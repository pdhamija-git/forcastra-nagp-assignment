# Demo Script - Show All Requirements Working

## Demo Sequence (10 minutes)

### 1. Show Cluster & Deployment (1 min)

```bash
# Show cluster info
kubectl cluster-info

# Show all resources deployed
kubectl get all -n nagp
```

**Show:** 4 API pods running, 1 database pod, services, ingress, HPA

---

### 2. Show Configuration (1 min)

```bash
# Show ConfigMap (non-sensitive config is visible)
kubectl get configmap api-config -n nagp -o yaml

# Show Secret exists (but values are encrypted)
kubectl get secret db-secret -n nagp
kubectl describe secret db-secret -n nagp
```

**Show:** Database configuration is externalized, passwords are encrypted

---

### 3. Show Persistent Storage (30 sec)

```bash
# Show PVC is bound
kubectl get pvc -n nagp

# Show it's attached to database pod
kubectl describe pvc postgres-pvc -n nagp
```

**Show:** 1Gi persistent volume is bound and ready

---

### 4. Test API - Health Endpoint (30 sec)

```bash
# Start port forward (keep running)
kubectl port-forward svc/nagp-api-service 8000:80 -n nagp
```

In another terminal:

```bash
# Test health endpoint
curl http://localhost:8000/health
```

**Expected:** `{"status": "healthy", "timestamp": "2026-06-19T..."}`  
**Shows:** API is running and database connection works ✓

---

### 5. Test API - Get Data (1 min)

```bash
# Get employee data
curl http://localhost:8000/api/employees
```

**Expected:** JSON response with 8 employee records

```json
{
  "success": true,
  "count": 8,
  "data": [
    {"id": 1, "name": "Alice Johnson", "department": "Engineering", "role": "Senior Developer", "salary": 95000.0, "location": "New York"},
    {"id": 2, "name": "Bob Smith", "department": "Engineering", "role": "DevOps Engineer", "salary": 88000.0, "location": "San Francisco"},
    ...
  ]
}
```

**Shows:** API fetches data from database tier ✓

---

### 6. Show Self-Healing - Delete API Pod (2 min)

```bash
# Get an API pod name
kubectl get pods -n nagp -l app=nagp-api

# Delete one pod
kubectl delete pod nagp-api-8559cf6d8-xxxx -n nagp

# Watch it recover
kubectl get pods -n nagp -l app=nagp-api --watch
```

**Show:** Old pod terminates, new pod appears and becomes ready in ~20 seconds  
**Verify API still works:**

```bash
curl http://localhost:8000/api/employees | jq '.count'
# Output: 8
```

**Shows:** Self-healing works ✓ Rolling updates possible ✓

---

### 7. Show Data Persistence - Delete Database Pod (2 min)

```bash
# Get database pod name
kubectl get pods -n nagp -l app=postgres

# Check data before deletion
kubectl exec -it postgres-74489976f9-qqq -n nagp -- psql -U postgres -d nagpdb -c "SELECT COUNT(*) FROM employees;"
# Output: 8

# Delete database pod
kubectl delete pod postgres-74489976f9-qqq -n nagp

# Watch recovery
kubectl get pods -n nagp -l app=postgres --watch
```

**Show:** New pod is created

```bash
# Verify data survived
NEW_POD=$(kubectl get pod -n nagp -l app=postgres -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $NEW_POD -n nagp -- psql -U postgres -d nagpdb -c "SELECT COUNT(*) FROM employees;"
# Output: 8
```

**Shows:** Data persists after pod deletion ✓

---

### 8. Show HPA Configuration (30 sec)

```bash
# Show HPA details
kubectl get hpa -n nagp

# Show detailed config
kubectl describe hpa nagp-api-hpa -n nagp
```

**Show:**
- Min replicas: 2
- Max replicas: 8
- Current: 4 pods
- CPU threshold: 70%
- Memory threshold: 80%

**Shows:** HPA configured ✓ Auto-scaling ready ✓

---

### 9. Show Rolling Update (optional - 1 min)

```bash
# Show deployment strategy
kubectl get deployment nagp-api -n nagp -o yaml | grep -A 5 "strategy:"
```

**Show:**
```yaml
strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 1
  type: RollingUpdate
```

**Shows:** Rolling updates configured ✓ Zero-downtime deployments ✓

---

### 10. Show Ingress/External Access (30 sec)

```bash
# Show ingress
kubectl get ingress -n nagp

# Show ingress details
kubectl describe ingress nagp-api-ingress -n nagp
```

**Show:** AWS ALB ingress is configured and routing traffic  
**Shows:** Service exposed externally ✓

---

### 11. Show Resource Limits (30 sec)

```bash
# Show resource requests/limits
kubectl get deployment nagp-api -n nagp -o yaml | grep -A 10 "resources:"
```

**Show:**
```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 50m
    memory: 64Mi
```

**Shows:** CPU and memory requests/limits defined ✓ Cost optimized ✓

---

### 12. Show Code Structure (30 sec)

```bash
# Show repository structure
ls -la

# Show Kubernetes files
ls -la k8s/

# Show application files
ls -la app/

# Show buildspec (CI/CD)
cat buildspec.yml | head -20
```

**Shows:** All files organized and present

---

## Requirements Checklist

After demo, confirm:

✓ **4 API Pods** - Shown in `kubectl get pods`  
✓ **1 Database Pod** - Shown in `kubectl get pods`  
✓ **Rolling Updates** - Shown in deployment strategy  
✓ **External Access** - Shown via Ingress/ALB  
✓ **Self-Healing** - Demonstrated by deleting API pod and watching recovery  
✓ **Data Persistence** - Demonstrated by deleting database pod and data surviving  
✓ **HPA** - Shown in HPA configuration (2-8 pods)  
✓ **ConfigMap** - Shown with database configuration  
✓ **Secrets** - Shown with encrypted database password  
✓ **No Hardcoded IPs** - Service DNS used (postgres-service.nagp.svc.cluster.local)  
✓ **Resource Limits** - Shown in deployment (50m/64Mi request, 200m/256Mi limit)  
✓ **Cost Optimized** - Resource limits and HPA shown  
✓ **Database 8 Records** - Shown in API response  
✓ **Internal Database** - ClusterIP service (not exposed)  
✓ **Repository Link** - GitHub URL in README  
✓ **Docker Image** - ECR mentioned in README  
✓ **API Endpoint** - Tested and working  
✓ **Code Structure** - All files present  

---

## Quick Demo Flow (if short on time - 5 minutes)

```bash
# 1. Show deployment
kubectl get all -n nagp

# 2. Test API
kubectl port-forward svc/nagp-api-service 8000:80 -n nagp
# In another terminal:
curl http://localhost:8000/api/employees

# 3. Delete API pod and show recovery
kubectl delete pod <api-pod> -n nagp
kubectl get pods -n nagp -l app=nagp-api --watch

# 4. Delete database pod and show data persists
kubectl delete pod <postgres-pod> -n nagp
kubectl get pods -n nagp -l app=postgres --watch
NEW_POD=$(kubectl get pod -n nagp -l app=postgres -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $NEW_POD -n nagp -- psql -U postgres -d nagpdb -c "SELECT COUNT(*) FROM employees;"

# 5. Show config
kubectl get configmap api-config -n nagp -o yaml
kubectl describe secret db-secret -n nagp

# 6. Show HPA and resources
kubectl get hpa -n nagp
kubectl get deployment nagp-api -n nagp -o yaml | grep -A 10 "resources:"
```

This covers all key requirements in 5 minutes.
