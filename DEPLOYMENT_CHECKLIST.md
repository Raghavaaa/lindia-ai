# AI Engine - Deployment Checklist

## 🚀 Railway Deployment Guide

Complete checklist for infrastructure team to deploy the AI Engine to Railway.

---

## ✅ Pre-Deployment Checklist

### 1. Repository Ready
- [x] Code pushed to GitHub: https://github.com/Raghavaaa/lindia-ai
- [x] All CI tests passing
- [x] Documentation complete
- [x] `.gitignore` configured (excludes `.env`)

### 2. Railway Project Setup
- [ ] Create new Railway project
- [ ] Connect to GitHub repository: `Raghavaaa/lindia-ai`
- [ ] Select branch: `main`
- [ ] Railway auto-detects: `Procfile` and `railway.json`

---

## 🔧 Required Environment Variables

**Set these in Railway → Environment Variables:**

### Service Configuration
```bash
# Basic service settings
PORT=8080
ENVIRONMENT=production
SERVICE_NAME=ai-service
LOG_LEVEL=INFO
```

### Provider Configuration
```bash
# Provider priority order (comma-separated)
PROVIDER_ORDER=inlegalbert,deepseek,grok
```

### Provider API Keys (⚠️ SECRETS - Use Railway Secret Store)
```bash
# InLegalBERT
INLEGALBERT_API_KEY=<GET-FROM-INLEGALBERT-DASHBOARD>
INLEGALBERT_MODEL=inlegalbert-v1
INLEGALBERT_API_URL=https://api.inlegalbert.ai/v1
INLEGALBERT_TIMEOUT=30

# DeepSeek  
DEEPSEEK_API_KEY=<GET-FROM-DEEPSEEK-DASHBOARD>
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_URL=https://api.deepseek.com/v1
DEEPSEEK_TIMEOUT=30

# Grok (xAI)
GROK_API_KEY=<GET-FROM-XAI-DASHBOARD>
GROK_MODEL=grok-beta
GROK_API_URL=https://api.x.ai/v1
GROK_TIMEOUT=30
```

### CORS Configuration
```bash
# Backend URL for CORS
BACKEND_URL=https://api.legalindia.ai
```

### Optional (Can Use Defaults)
```bash
# RAG Configuration
RAG_MAX_CONTEXT_TOKENS=3000
RAG_DEFAULT_TOP_K=5

# Observability
METRICS_PORT=9090

# Queue (for future)
QUEUE_BACKEND=memory
WORKER_COUNT=4
```

---

## 📋 Railway Configuration Files

**These files are already in the repository:**

### 1. `Procfile`
```
web: gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app
```
✅ Tells Railway how to start the service

### 2. `railway.json`
```json
{
  "build": {...},
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100
  }
}
```
✅ Railway service configuration

### 3. `runtime.txt`
```
python-3.11.6
```
✅ Python version specification

### 4. `requirements.txt`
✅ All dependencies listed

---

## 🎯 Health Check Endpoints

Railway will monitor these endpoints:

### Primary: `/health`
**Expected Response (200 OK):**
```json
{
  "status": "ok",
  "uptime_seconds": 123.45,
  "model_provider": "InLegalBERT, DeepSeek, Grok",
  "service": "ai-engine",
  "timestamp": "2025-10-18T10:30:00Z"
}
```

### Secondary: `/ready`
**(To be implemented)**
Returns 200 if all dependencies healthy, 503 if degraded

---

## 🧪 Post-Deploy Validation

After Railway reports "Deployed Successfully", run these checks:

### 1. Health Check
```bash
curl https://your-service.up.railway.app/health

# Expected: {"status": "ok", ...}
```

### 2. Metrics Endpoint
```bash
curl https://your-service.up.railway.app/metrics

# Expected: Prometheus metrics text
```

### 3. Provider Status
```bash
curl https://your-service.up.railway.app/providers/status

# Expected: Provider health information
```

### 4. Simple Inference Test
```bash
curl -X POST https://your-service.up.railway.app/inference \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query", "max_tokens": 50}'

# Expected: {"answer": "...", "model": "..."}
```

---

## 🚨 Troubleshooting

### Service Won't Start
**Check:**
1. Railway logs for errors
2. All required env vars are set
3. API keys are valid
4. Python version matches `runtime.txt`

**Common Issues:**
- Missing env vars → Add to Railway
- Invalid API keys → Check provider dashboards
- Port conflict → Railway sets `$PORT` automatically

### Health Check Fails
**Check:**
1. Service is running (`ps aux | grep gunicorn`)
2. Port is correct (Railway injects `$PORT`)
3. Logs show application started

### Provider Errors
**Check:**
1. API keys are correct
2. Provider APIs are reachable
3. Rate limits not exceeded
4. Check `/providers/status` endpoint

---

## 🔐 Security Checklist

- [ ] All API keys in Railway Secret Store (not visible in logs)
- [ ] CORS configured for backend only
- [ ] TLS enabled (Railway default)
- [ ] No secrets in code or git history
- [ ] `.env` file in `.gitignore`

---

## 📊 Expected Service URLs

### Railway Auto-Generated
```
https://ai-engine-production.up.railway.app
```

### Custom Domain (Optional)
```
https://ai.legalindia.ai
```

**To set custom domain:**
1. Railway → Settings → Domains
2. Add custom domain
3. Update DNS CNAME record

---

## 🔗 Backend Integration

Once deployed, update your backend to call the AI Engine:

```python
# In your backend code
AI_ENGINE_URL = "https://ai.legalindia.ai"

import requests

response = requests.post(
    f"{AI_ENGINE_URL}/inference",
    json={
        "query": user_query,
        "context": case_context
    },
    headers={
        "Content-Type": "application/json",
        # Add auth headers when implemented
    }
)

answer = response.json()["answer"]
```

---

## 📈 Monitoring Setup

### Grafana Dashboards
1. Import dashboard from `grafana/ai_engine_dashboard.json`
2. Configure Prometheus data source
3. Point to: `https://your-service.railway.app/metrics`

### Alert Manager
1. Load alerts from `.github/alerts/prometheus_rules.yml`
2. Configure notification channels (Slack/PagerDty)

---

## 🎯 Success Criteria

**Deployment is successful when:**

- ✅ `/health` returns `{"status": "ok"}`
- ✅ `/metrics` returns Prometheus metrics
- ✅ `/inference` processes test query
- ✅ `/providers/status` shows provider health
- ✅ No errors in Railway logs
- ✅ Service restarts automatically on failure
- ✅ Backend can call AI Engine successfully

---

## 📞 Support Contacts

**For deployment issues:**
- DevOps Team: devops@company.com
- On-call: +1-555-0100
- Railway Docs: https://docs.railway.app/

**For application issues:**
- AI Team: ai-team@company.com
- GitHub Issues: https://github.com/Raghavaaa/lindia-ai/issues

---

## 🔄 Rollback Procedure

If deployment fails:

```bash
# Option 1: Railway Dashboard
# Click "Deployments" → Select previous → "Redeploy"

# Option 2: Git revert
git revert HEAD
git push origin main
# Railway auto-deploys previous version
```

---

## ✅ Final Validation

**Before marking deployment complete:**

1. ✅ Health endpoint returns 200
2. ✅ Metrics endpoint accessible
3. ✅ Simple inference test passes
4. ✅ No critical errors in logs (15 min observation)
5. ✅ Backend integration tested
6. ✅ Monitoring dashboards showing data
7. ✅ Alert rules configured

**Mark as:**
- ✅ **SUCCESS** if all checks pass
- ⚠️ **DEGRADED** if non-critical checks fail
- ❌ **FAILED** if critical checks fail (rollback required)

---

**Last Updated:** October 2025  
**Version:** 1.0.0  
**Repository:** https://github.com/Raghavaaa/lindia-ai

