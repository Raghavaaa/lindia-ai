# AI Engine Service - Admin Runbook

Quick reference guide for common administrative operations.

---

## Service Information

**Service Name**: AI Engine  
**Type**: Internal/Private Railway Service  
**URL**: `http://ai-engine.railway.internal`  
**Owner**: Platform Team  
**Version**: 1.0.0  

---

## Quick Operations

### 🔄 Rotate Model Keys

**When**: Security incident, key leak, or regular rotation (quarterly)

**How**:
```bash
1. Railway Dashboard → AI Engine → Variables
2. Update PRIMARY_MODEL_KEY → Paste new key → Mark as Secret → Save
3. Service auto-restarts (downtime: ~10 seconds)
4. Verify: curl http://ai-engine.railway.internal/health
```

**One-liner**: Update `PRIMARY_MODEL_KEY` or `SECONDARY_MODEL_KEY` in Railway variables, service restarts automatically.

---

### 🔀 Change Provider Priority

**When**: Primary provider is slow, expensive, or down

**How**:
```bash
1. Railway Dashboard → AI Engine → Variables
2. Update PRIMARY_PROVIDER=DeepSeek (or INLEGALBERT, Grok)
3. Update FALLBACK_PROVIDERS=INLEGALBERT,Grok (comma-separated)
4. Save (NO restart needed - takes effect immediately)
```

**One-liner**: Change `PRIMARY_PROVIDER` and `FALLBACK_PROVIDERS` env vars, no redeploy required.

---

### 📈 Scale Service Manually

**When**: Expected traffic spike, maintenance window, or cost reduction

**How**:
```bash
# Scale UP (for traffic spike)
1. Railway Dashboard → AI Engine → Settings → Resources
2. Set Min=2, Max=5
3. Save

# Scale DOWN (for cost saving)
1. Set Min=1, Max=1
2. Save

# Reset to AUTO
1. Set Min=1, Max=3
2. Save
```

**One-liner**: Adjust instance count in Railway Settings → Resources (min/max instances).

---

### ⏮️ Rollback Deployment

**When**: New deployment causes errors or performance issues

**How**:
```bash
# Option 1: Railway Dashboard
1. Railway → AI Engine → Deployments
2. Find last good deployment (green checkmark)
3. Click "..." → "Redeploy"

# Option 2: Railway CLI
railway rollback
```

**One-liner**: Railway Dashboard → Deployments → Select previous deployment → Redeploy.

---

### 📊 View Logs

**When**: Debugging errors, monitoring performance, investigating incidents

**How**:
```bash
# Via Dashboard
Railway → AI Engine → Logs

# Filter examples:
- [Search: ERROR] - Show only errors
- [Search: tenant_id=tenant_123] - Filter by tenant
- [Search: request_id=abc-xyz] - Track specific request
- [Search: rate_limit_exceeded] - Find rate limit issues

# Via CLI
railway logs
railway logs --filter ERROR
```

**One-liner**: Railway Dashboard → AI Engine → Logs, use search box to filter.

---

### 🚨 Emergency Stop

**When**: Service is causing cascading failures, billing spike, or security incident

**How**:
```bash
1. Railway Dashboard → AI Engine → Settings
2. Scroll to bottom → "Pause Service" → Confirm
3. Investigate issue
4. Resume when ready: "Resume Service"
```

**One-liner**: Railway Settings → Pause Service (stops all instances immediately).

---

### 🔍 Check Service Health

**When**: After any change, deployment, or incident

**How**:
```bash
# From another Railway service:
curl http://ai-engine.railway.internal/health

# Expected response:
{"status":"ok","uptime":3600.45,"version":"1.0.0"}

# Check metrics:
Railway Dashboard → AI Engine → Metrics
- CPU usage (target: <60% avg)
- Memory usage (target: <80%)
- Request rate
- Error rate (target: <1%)
```

**One-liner**: `curl http://ai-engine.railway.internal/health` returns `{"status":"ok"}`.

---

### ⚙️ Update Configuration

**When**: Adjust rate limits, quotas, timeouts, or other settings

**How**:
```bash
1. Railway Dashboard → AI Engine → Variables
2. Update any of these (NO restart needed):
   - RATE_LIMIT_PER_MINUTE (default: 100)
   - DAILY_QUOTA_LIMIT (default: 10000)
   - PRIMARY_PROVIDER (default: INLEGALBERT)
   - FALLBACK_PROVIDERS (default: DeepSeek,Grok)
   - LOG_LEVEL (default: INFO)
3. Save

# Restart required for these:
   - REQUEST_TIMEOUT_SECONDS
   - MAX_PAYLOAD_SIZE_BYTES
   - CONCURRENCY_LIMIT_PER_WORKER
```

**One-liner**: Update environment variables in Railway Dashboard → Variables tab.

---

### 📉 Reduce Rate Limits (Emergency)

**When**: Sudden traffic spike, potential abuse, or cost containment

**How**:
```bash
1. Railway Variables → RATE_LIMIT_PER_MINUTE=50 (from 100)
2. Railway Variables → DAILY_QUOTA_LIMIT=5000 (from 10000)
3. Save (takes effect immediately, no restart)
4. Monitor logs for 429 errors
5. Restore when safe
```

**One-liner**: Lower `RATE_LIMIT_PER_MINUTE` and `DAILY_QUOTA_LIMIT` via Railway Variables.

---

### 🔒 Regenerate JWT Secret

**When**: Security incident, suspected leak, or annual rotation

**How**:
```bash
1. Generate new secret:
   openssl rand -base64 32

2. Update in Railway:
   Railway → AI Engine → Variables → INTERNAL_JWT_SECRET → Paste new value → Save

3. Update in consuming services (critical!):
   - Main backend: AI_ENGINE_JWT_SECRET
   - Any other services calling AI Engine

4. Verify:
   curl -H "Authorization: Bearer <new-jwt>" http://ai-engine.railway.internal/inference
```

**One-liner**: Generate new secret with `openssl rand -base64 32`, update `INTERNAL_JWT_SECRET` in Railway + all consuming services.

---

### 📝 Debug Request

**When**: Specific request is failing or slow

**How**:
```bash
1. Get request_id from client logs or error response
2. Railway Logs → Search: request_id=abc-123-xyz
3. Review log sequence:
   - Request received
   - JWT verified
   - Provider attempts (INLEGALBERT → DeepSeek → Grok)
   - Response or error
4. Check latency_ms, model used, estimated_cost
```

**One-liner**: Search logs by `request_id` to trace full request lifecycle.

---

### 📈 Monitor Costs

**When**: Monthly review or unexpected billing spike

**How**:
```bash
1. Railway Logs → Search: estimated_cost
2. Aggregate cost estimates from logs
3. Check provider distribution:
   - Search: "model": "INLEGALBERT"
   - Search: "model": "DeepSeek"
   - Search: "model": "Grok"
4. If Grok usage is high (expensive), change PRIMARY_PROVIDER to DeepSeek
```

**One-liner**: Search logs for `estimated_cost` and `model` to track provider usage and costs.

---

### 🧪 Test Endpoint

**When**: After deployment, configuration change, or debugging

**How**:
```bash
# 1. Generate test JWT (from backend or script)
JWT_TOKEN="your-generated-token-here"

# 2. Test inference
curl -X POST http://ai-engine.railway.internal/inference \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Test query",
    "context": "Test context",
    "tenant_id": "test_tenant"
  }'

# 3. Test health (no JWT needed)
curl http://ai-engine.railway.internal/health
```

**One-liner**: Use curl with valid JWT to test endpoints (see examples above).

---

### 📧 Alert on Issues

**When**: Setting up monitoring (one-time setup)

**How**:
```bash
1. Railway Dashboard → AI Engine → Settings → Notifications
2. Add alert rules:
   - CPU > 80% for 5 minutes → Alert
   - Memory > 90% → Alert
   - Error rate > 5% → Alert
   - Service down → Alert (critical)
3. Configure notification channels (email, Slack, PagerDuty)
```

**One-liner**: Railway Settings → Notifications → Add alert rules for CPU, memory, errors, and downtime.

---

## Troubleshooting Matrix

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| 401 Unauthorized | Invalid/missing JWT | Check INTERNAL_JWT_SECRET matches between services |
| 429 Rate Limit | Too many requests | Increase RATE_LIMIT_PER_MINUTE or check for abuse |
| 429 Quota Exceeded | Daily limit hit | Increase DAILY_QUOTA_LIMIT or wait for reset (midnight) |
| 504 Timeout | Request too slow | Check provider performance, consider scaling up |
| 500 Inference Failed | All providers down | Check model keys, provider status, logs |
| High latency | Under-provisioned | Scale up instances (increase max) |
| High costs | Wrong provider | Switch PRIMARY_PROVIDER to DeepSeek (cheaper) |
| Deployment fails | Smoke test failure | Check /health endpoint, validate env vars |

---

## Emergency Contacts

| Role | Contact | When to Escalate |
|------|---------|------------------|
| On-call Engineer | PagerDuty | Service down >5 min, critical errors |
| Platform Team | Slack #platform | Configuration issues, questions |
| DevOps Lead | Email | Rollback decisions, infrastructure changes |
| Security Team | security@example.com | Key leak, unauthorized access |

---

## Regular Maintenance

### Weekly
- [ ] Check error rate in logs (target: <1%)
- [ ] Verify autoscaling is working (CPU-based)
- [ ] Review cost estimates in logs

### Monthly
- [ ] Review and optimize provider usage
- [ ] Check and adjust rate limits/quotas
- [ ] Verify backup/rollback procedure

### Quarterly
- [ ] Rotate INTERNAL_JWT_SECRET
- [ ] Rotate PRIMARY_MODEL_KEY and SECONDARY_MODEL_KEY
- [ ] Review and update documentation
- [ ] Load testing and performance review

---

## Useful Commands

```bash
# View service status
railway status

# View recent logs
railway logs --limit 100

# Connect to service (for debugging)
railway run bash

# View environment variables
railway variables

# Restart service
railway restart

# View deployment history
railway deployments

# Rollback to previous
railway rollback
```

---

## Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| CPU Usage | <60% avg | >80% for 5 min |
| Memory Usage | <80% | >90% |
| Request Latency | <500ms p95 | >1000ms p95 |
| Error Rate | <1% | >5% |
| Rate Limit Hits | <5% requests | >10% requests |
| Uptime | >99.9% | <99.5% |

---

## Version Information

**Current Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**Maintained By**: Platform Team  
**Runbook Version**: 1.0  

---

## Quick Links

- [Full Documentation](./README.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Railway Dashboard](https://railway.app/project/legalindia/service/ai-engine)
- [Provider Status Pages](#)
- [Incident Playbook](#)

