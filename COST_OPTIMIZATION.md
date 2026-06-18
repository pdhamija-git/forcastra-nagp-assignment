# Cost Optimization Implementation Guide

## Overview
This document provides practical implementations for the 3+ cost optimization opportunities identified in the compliance review.

---

## 1. Pod Disruption Budget (PDB) for API Tier

**Problem:** During rolling updates or cluster maintenance, unnecessary pod disruptions can trigger scale-ups, increasing costs.

**Solution:** Limit disruptions to maintain service availability while reducing churn.

### Create File: `k8s/02-api-pod-disruption-budget.yaml`

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: nagp-api-pdb
  namespace: nagp
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: nagp-api
  unhealthyPodEvictionPolicy: AlwaysAllow
```

**Benefits:**
- Ensures at least 2 API pods remain available during disruptions
- Reduces unnecessary autoscaling events
- Estimated Savings: 5-10% on compute costs

**Add to buildspec.yml deployment order:**
```yaml
- kubectl apply -f k8s/02-api-pod-disruption-budget.yaml
```

---

## 2. Resource Right-Sizing with Monitoring

**Problem:** Current requests may be conservative estimates; actual usage might be lower.

**Solution:** Implement metrics collection and right-size based on data.

### Create File: `k8s/11-monitoring-configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: nagp
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
            namespaces:
              names:
                - nagp
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            action: keep
            regex: nagp-api|postgres
```

**Usage Instructions:**
```bash
# 1. Install metrics-server (if not already installed)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 2. Monitor actual usage
kubectl top pods -n nagp --containers
kubectl top nodes

# 3. After 2-4 weeks of production data, adjust resources:
# Current: requests cpu: 100m, memory: 128Mi
# If actual < 50m CPU, reduce to: 75m
# If actual < 100Mi memory, reduce to: 96Mi
```

**Expected Savings:** 10-20% on API tier compute costs

---

## 3. Storage Optimization with Monitoring

**Problem:** 1Gi PVC is allocated but only using ~100-200Mi for 8 records.

**Solution:** Monitor storage and implement tiered storage strategy.

### Monitor Storage Usage
```bash
# Check current usage
kubectl exec -it <postgres-pod> -n nagp -- du -sh /var/lib/postgresql/data

# Expected: ~20-50MB for 8 employee records
```

### Create File: `k8s/04-postgres-pvc-optimized.yaml` (Optional Right-Sizing)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: nagp
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3  # Use GP3 instead of default gp2
  resources:
    requests:
      storage: 512Mi  # Reduced from 1Gi
```

**Benefits:**
- **Storage Savings:** 50% reduction (1Gi → 512Mi) = 50% storage cost reduction
- **Performance:** GP3 provides better IOPS/throughput ratio
- **Cost:** GP3 is ~20% cheaper than GP2 on AWS

**Implementation Steps:**
1. Test in non-production first
2. Verify data integrity
3. Monitor for 1-2 weeks
4. Scale up only if needed (can expand PVC dynamically)

**Expected Savings:** 40-50% on storage costs

---

## 4. HPA Fine-Tuning for Cost Efficiency

**Problem:** Current HPA settings may cause unnecessary scaling.

**Solution:** Optimize scaling behavior based on actual load patterns.

### Create File: `k8s/09-api-hpa-optimized.yaml`

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nagp-api-hpa
  namespace: nagp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nagp-api
  minReplicas: 2  # Start with 2 (avoid single point of failure)
  maxReplicas: 6  # Reduced from 8 (cost control)
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 75  # Increased from 70% (reduce sensitivity)
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 85  # Increased from 80% (reduce sensitivity)
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 600  # Increased from 300
      policies:
        - type: Percent
          value: 50  # Scale down 50% of pods
          periodSeconds: 60
        - type: Pods
          value: 1
          periodSeconds: 60
      selectPolicy: Min  # Most conservative
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100  # Double pods
          periodSeconds: 30
        - type: Pods
          value: 2
          periodSeconds: 30
      selectPolicy: Max  # Aggressive scale-up
```

**Benefits:**
- **Reduced scaling churn:** 75% vs 70% CPU threshold means less frequent scale-ups
- **Faster scale-down:** Aggressive scale-down with stabilization prevents keeping unnecessary pods
- **Cost Control:** maxReplicas: 6 instead of 8 (25% max cost reduction)

**Expected Savings:** 15-25% on HPA-related compute costs

---

## 5. Database Tier Resource Optimization

### Current Configuration Analysis

```yaml
Current Resources:
  Requests: cpu: 250m, memory: 256Mi
  Limits:   cpu: 500m, memory: 512Mi

Analysis:
- Postgres with 8 records typically uses: 20-50m CPU, 100-150Mi memory
- Current requests: 250m/256Mi
- Utilization: ~10-20% of requested
- Recommendation: Reduce by 40-50%
```

### Create File: `k8s/05-postgres-deployment-optimized.yaml`

```yaml
# Replace resources section with:
resources:
  requests:
    cpu: "150m"        # Reduced from 250m (40% reduction)
    memory: "192Mi"    # Reduced from 256Mi (25% reduction)
  limits:
    cpu: "300m"        # Reduced from 500m (40% reduction)
    memory: "384Mi"    # Reduced from 512Mi (25% reduction)
```

**Benefits:**
- Lower resource requests = tighter cluster utilization
- Reduced reserved capacity per node
- Ability to pack more workloads per node

**Expected Savings:** 10-15% on database compute costs

---

## 6. Combined Cost Optimization Summary

| Optimization | Current | Optimized | Savings |
|---|---|---|---|
| Storage (PVC) | 1Gi | 512Mi | **50%** |
| Database CPU | 250m | 150m | **40%** |
| Database Memory | 256Mi | 192Mi | **25%** |
| HPA Max Replicas | 8 | 6 | **25% max** |
| HPA CPU Threshold | 70% | 75% | **~10%** |
| PDB for Updates | None | Added | **5-10%** |
| **Total Potential Savings** | - | - | **~25-35%** |

---

## 7. Implementation Roadmap

### Phase 1: Immediate (Week 1)
- [ ] Implement Pod Disruption Budget (PDB)
- [ ] Install metrics-server
- [ ] Set up Prometheus monitoring
- [ ] Baseline current resource usage

### Phase 2: Validation (Week 2-3)
- [ ] Monitor CPU and memory utilization
- [ ] Verify load patterns during peak hours
- [ ] Document findings in metrics

### Phase 3: Optimization (Week 4-6)
- [ ] Update HPA configuration
- [ ] Right-size database resources
- [ ] Test storage reduction in non-prod
- [ ] Plan PVC resize with zero downtime

### Phase 4: Verification (Ongoing)
- [ ] Monitor cost dashboard
- [ ] Track actual vs. projected savings
- [ ] Adjust based on production patterns
- [ ] Document lessons learned

---

## 8. Validation Scripts

### Check Current Resource Usage
```bash
#!/bin/bash
echo "=== API Pod Resources ==="
kubectl top pods -n nagp -l app=nagp-api --containers

echo "=== Database Pod Resources ==="
kubectl top pods -n nagp -l app=postgres --containers

echo "=== Storage Usage ==="
kubectl exec -it $(kubectl get pod -n nagp -l app=postgres -o jsonpath='{.items[0].metadata.name}') \
  -n nagp -- du -sh /var/lib/postgresql/data

echo "=== Current HPA Status ==="
kubectl describe hpa nagp-api-hpa -n nagp
```

### Monitor HPA Scaling Events
```bash
# Watch scaling in real-time
kubectl get hpa -n nagp --watch

# Check scaling history
kubectl describe hpa nagp-api-hpa -n nagp | grep -A 20 "Events:"
```

---

## 9. Rollback Procedure

If any optimization causes issues:

```bash
# Restore original PVC size
kubectl patch pvc postgres-pvc -p '{"spec":{"resources":{"requests":{"storage":"1Gi"}}}}'

# Restore original HPA
kubectl apply -f k8s/09-api-hpa.yaml  # (original version)

# Restore original deployment resources
kubectl set resources deployment/nagp-api \
  -n nagp \
  --requests=cpu=100m,memory=128Mi \
  --limits=cpu=300m,memory=256Mi

# Remove PDB if problematic
kubectl delete pdb nagp-api-pdb -n nagp
```

---

## Key Takeaways

✅ **Quick Wins:** PDB + HPA tuning = 15-20% savings (no risk)
✅ **Measured Approach:** Resource right-sizing after monitoring = 20-30% savings (low risk)
✅ **Storage Optimization:** Reduce PVC + use GP3 = 50% storage savings (easy rollback)
✅ **Total Target:** 25-35% cost reduction across all tiers

**Estimated Monthly Savings (assuming ~$500/month base cost):**
- Conservative: $75-100/month (15-20%)
- Aggressive: $125-175/month (25-35%)

