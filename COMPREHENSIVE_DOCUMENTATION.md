# NAGP Kubernetes Multi-Tier Architecture - Documentation

## 1. Requirement Understanding

The assignment required building a multi-tier Kubernetes application with:

- **Service API Tier:** 4 pods, externally accessible, support rolling updates and self-healing
- **Database Tier:** 1 pod, internal-only, persistent storage, auto-recovery
- **Configuration:** ConfigMap for non-sensitive config, Secrets for passwords
- **Kubernetes Features:** HPA (2-8 pods), Ingress for external access, Service DNS for pod communication
- **FinOps:** CPU/memory requests and limits, 3 cost optimization opportunities

**All requirements met and verified.**

---

## 2. Assumptions

**Environment:**
- AWS EKS cluster available and running
- Default storage class (EBS gp2) configured
- kubectl configured for cluster access
- Container registry available (ECR)

**Technology Stack:**
- FastAPI for microservice (Python 3.12)
- PostgreSQL 15 for database (Alpine)
- Docker for containerization
- Kubernetes 1.24+ for orchestration
- AWS ALB for ingress controller

**Architecture:**
- API pods are stateless (scale horizontally)
- Database uses single pod with PVC for persistence
- Service DNS used for pod communication (not hardcoded IPs)
- Configuration externalized via ConfigMap/Secrets

---

## 3. Solution Overview

### Architecture

```
Internet Users
    ↓
AWS ALB/Ingress
    ↓
nagp-api-service (ClusterIP)
    ├─ nagp-api pod 1 (10.0.1.55:3000)
    ├─ nagp-api pod 2 (10.0.2.34:3000)
    ├─ nagp-api pod 3
    └─ nagp-api pod 4
         ↓ (connects via postgres-service.nagp.svc.cluster.local)
postgres-service (ClusterIP)
    └─ postgres pod (10.0.2.xx:5432)
         ↓
    PVC (/var/lib/postgresql/data)
         ↓
    EBS Volume (1Gi persistent storage)
```

### Components Deployed

**Service API Tier:**
- 4 FastAPI pods on port 3000
- Requests: 50m CPU, 64Mi Memory
- Limits: 200m CPU, 256Mi Memory
- RollingUpdate strategy (maxSurge: 1, maxUnavailable: 1)
- Connection pooling: min=1, max=10 connections
- Health probes: Liveness and Readiness configured

**Database Tier:**
- 1 PostgreSQL pod on port 5432
- Requests: 50m CPU, 64Mi Memory
- Limits: 200m CPU, 256Mi Memory
- Recreate strategy (appropriate for stateful workload)
- 8 employee records pre-loaded
- Persistent storage: 1Gi EBS volume

**Kubernetes Resources:**
- Namespace: nagp (isolated)
- Services: nagp-api-service, postgres-service (ClusterIP)
- Ingress: nagp-api-ingress (AWS ALB, internet-facing)
- ConfigMap: api-config (database configuration)
- Secret: db-secret (encrypted password)
- HPA: Scales 2-8 pods based on CPU (70%) and Memory (80%)
- PDB: Minimum 2 pods always available

---

## 4. Justification for the Resources Utilized

### Why 4 API Pods?

**Requirement:** Assignment specified 4 pods

**Justification:**
- High availability: If one pod fails, 3 continue running
- Load distribution: Spreads incoming requests across pods
- Rolling updates: Can replace pods gradually without downtime
- HPA baseline: Provides starting point for autoscaling (2-8 pods)

### Why 50m CPU / 64Mi Memory (Requests)?

**Original:** 100m CPU / 128Mi Memory  
**Optimized:** 50m CPU / 64Mi Memory (50% savings)

**Justification:**
- Actual usage observed: 5-10m CPU, 30-35Mi Memory
- Provides 5-10x safety buffer for spikes
- Cluster capacity constraint required optimization
- Limits set to 200m/256Mi (4x buffer) for emergency bursts

### Why 1 Database Pod?

**Justification:**
- Stateful workload requires single source of truth
- Replication adds complexity (not needed for assignment)
- PVC provides reliability and data persistence
- Auto-restart on failure maintains availability

### Why Recreate Strategy for Database?

**Justification:**
- Stateful workloads should not use RollingUpdate
- Ensures clean shutdown before new pod starts
- Prevents data consistency issues
- Appropriate for single-pod database

### Why Service DNS (Not Pod IPs)?

**Justification:**
- Pod IPs change on restart (unstable)
- Service DNS is stable and Kubernetes-native
- Enables service discovery without hardcoding
- Best practice for microservice communication

### Why ConfigMap + Secrets?

**ConfigMap (api-config):**
- Stores non-sensitive: DB_HOST, DB_PORT, DB_NAME, PORT
- Externalized from code and YAML deployment
- Can be updated without pod restart

**Secrets (db-secret):**
- Stores sensitive: DB_PASSWORD, DB_USER, POSTGRES_DB
- Encrypted at rest by Kubernetes
- Not visible in YAML files or application logs

### Why HPA (2-8 pods)?

**Min 2 pods:**
- Ensures high availability (at least 2 always running)

**Max 8 pods:**
- Cost control (prevents runaway scaling)

**CPU 70% threshold:**
- Scales up before resource exhaustion

**Memory 80% threshold:**
- Memory is more critical than CPU

### Why PVC (1Gi)?

**Justification:**
- Data survives pod restarts and deletions
- 1Gi provides 1000x capacity for 8 records
- EBS gp2 is cost-effective for POC
- Meets data persistence requirement

### Cost Optimization Strategies

**1. Resource Right-Sizing**
- Reduced from 100m/128Mi to 50m/64Mi per pod
- Savings: 50% reduction = ~4 pods worth of capacity freed

**2. Pod Disruption Budget**
- Prevents unnecessary pod churn during maintenance
- Reduces restart overhead and costs

**3. HPA Tuning**
- Scales down when load drops (saves resources)
- Max 8 pods prevents over-scaling
- Conservative scale-down (-1 pod) prevents thrashing
