# AI Engine Deployment Guide

## Railway Deployment Steps

### Step 1: Create New Railway Service

1. Log in to [Railway](https://railway.app)
2. Navigate to your **LegalIndia** project
3. Click **"+ New"** → **"Empty Service"**
4. Name it: **AI Engine**

### Step 2: Configure as Internal Service

1. Go to **AI Engine** service → **Settings**
2. Under **Networking**:
   - ✅ Enable "Private Networking"
   - ✅ Disable "Public Networking" (no public domain)
   - Service will be accessible at: `ai-engine.railway.internal`

### Step 3: Connect Repository

1. In service settings → **Source**
2. Click **"Connect Repo"**
3. Select your repository
4. Set **Branch**: `AI-engine` (or your branch name)
5. Set **Root Directory**: `/ai-engine` (if in monorepo)
6. ✅ Enable **"Auto Deploy"** on push

### Step 4: Configure Runtime

1. Service Settings → **Resources**
2. Select **"Light"** dyno (or equivalent)
3. Set **Instance Count**:
   ```
   Minimum: 1
   Maximum: 3
   ```

### Step 5: Configure Autoscaling

1. Settings → **Autoscaling**
2. Set scaling rules:
   ```
   Metric: CPU Usage
   Threshold: 60%
   Scale Up: Add 1 instance
   Scale Down: After 5 minutes below 40%
   ```

### Step 6: Set Environment Variables

Go to **Variables** tab and add:

#### Required Secrets (mark each as 🔒 Secret)

```bash
# Generate JWT secret with:
# openssl rand -base64 32
INTERNAL_JWT_SECRET=your-generated-secret-min-32-chars

# Your AI model API keys
PRIMARY_MODEL_KEY=sk-xxxxxxxxxxxxx
SECONDARY_MODEL_KEY=sk-xxxxxxxxxxxxx

# Vector store connection
VECTOR_STORE_URL=https://your-vector-db.example.com
```

#### Configuration Variables

```bash
# Provider configuration (can be changed without redeploy)
PRIMARY_PROVIDER=INLEGALBERT
FALLBACK_PROVIDERS=DeepSeek,Grok

# Logging
LOG_LEVEL=INFO

# Request constraints
REQUEST_TIMEOUT_SECONDS=30
MAX_PAYLOAD_SIZE_BYTES=5242880
CONCURRENCY_LIMIT_PER_WORKER=10

# Rate limiting
RATE_LIMIT_PER_MINUTE=100
DAILY_QUOTA_LIMIT=10000

# Smoke tests
RUN_SMOKE_TESTS_ON_DEPLOY=true
FAIL_DEPLOY_ON_SMOKE_TEST_FAILURE=true

# Port (Railway will auto-assign)
PORT=${{RAILWAY_PORT}}
```

### Step 7: Deploy

1. Click **"Deploy"** button
2. Watch deployment logs
3. Wait for smoke tests to pass
4. Verify health: Check logs for "✅ All smoke tests passed"

### Step 8: Verify Deployment

```bash
# From another Railway service in the same project:
curl http://ai-engine.railway.internal/health

# Expected response:
{
  "status": "ok",
  "uptime": 12.34,
  "version": "1.0.0"
}
```

---

## Service Configuration Summary

**Service Name**: AI Engine  
**Type**: Internal/Private  
**URL**: `http://ai-engine.railway.internal` (or `https://ai-engine.railway.internal` if Railway provides SSL for internal)  
**Runtime**: Light dyno  
**Instances**: 1-3 (autoscaling)  
**Autoscale Trigger**: CPU > 60%  
**Request Timeout**: 30 seconds  
**Max Payload**: 5 MB  
**Concurrency**: 10 per worker  

---

## Post-Deployment Checklist

- [ ] Service is marked as internal/private
- [ ] Auto-deploy is enabled on AI-engine branch
- [ ] All environment secrets are marked as 🔒 Secret
- [ ] Autoscaling is configured (min=1, max=3, CPU>60%)
- [ ] Health endpoint returns `{"status": "ok"}`
- [ ] Smoke tests pass on deployment
- [ ] Service URL is added to main backend's config
- [ ] JWT secret is shared with services that need to call AI Engine
- [ ] Logs are visible in Railway dashboard
- [ ] Provider order is correct (INLEGALBERT → DeepSeek → Grok)

---

## Connecting from Other Services

### Update Backend Service

In your main backend (app), update the configuration:

```python
# app/core/config.py

class Settings(BaseSettings):
    # ...
    
    # AI Engine internal URL
    AI_ENGINE_URL: str = "http://ai-engine.railway.internal"
    AI_ENGINE_JWT_SECRET: str  # Same as INTERNAL_JWT_SECRET
```

### Generate JWT Token

```python
import jwt
from datetime import datetime, timedelta

def generate_ai_engine_token(tenant_id: str) -> str:
    """Generate JWT token for AI Engine access."""
    payload = {
        "tenant_id": tenant_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=5),
    }
    
    token = jwt.encode(
        payload,
        settings.AI_ENGINE_JWT_SECRET,
        algorithm="HS256"
    )
    
    return token
```

### Call AI Engine

```python
import httpx

async def call_ai_inference(query: str, context: str, tenant_id: str):
    """Call AI Engine inference endpoint."""
    token = generate_ai_engine_token(tenant_id)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.AI_ENGINE_URL}/inference",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "context": context,
                "tenant_id": tenant_id,
            },
            timeout=30.0,
        )
    
    response.raise_for_status()
    return response.json()
```

---

## Monitoring & Maintenance

### View Logs

```bash
# Railway Dashboard
Railway → AI Engine → Logs

# Filter by level
[Filter: ERROR]

# Search by tenant
[Search: tenant_id=tenant_123]
```

### Check Resource Usage

```bash
# Railway Dashboard
Railway → AI Engine → Metrics

# Monitor:
- CPU usage (should trigger scaling at 60%)
- Memory usage
- Request count
- Response times
```

### Common Issues

#### 1. Smoke Tests Failing

**Symptom**: Deployment fails with "Smoke tests failed"

**Solution**:
```bash
# Check logs for specific test failure
# Common causes:
- Health endpoint not responding → Check PORT config
- Invalid JWT → Verify INTERNAL_JWT_SECRET
- Timeout → Increase REQUEST_TIMEOUT_SECONDS
```

#### 2. Rate Limits Hit Too Often

**Symptom**: Many 429 errors in logs

**Solution**:
```bash
# Increase rate limits
RATE_LIMIT_PER_MINUTE=200
DAILY_QUOTA_LIMIT=20000
```

#### 3. High Latency

**Symptom**: `latency_ms` > 1000 in logs

**Solution**:
- Scale up instances (increase max to 5)
- Check provider performance in logs
- Consider changing PRIMARY_PROVIDER

#### 4. Provider Failures

**Symptom**: Logs show "All providers failed"

**Solution**:
- Check PRIMARY_MODEL_KEY and SECONDARY_MODEL_KEY
- Verify provider API status
- Check provider-specific error messages in logs

---

## Rollback Procedure

If deployment causes issues:

### Option 1: Via Railway Dashboard

1. Railway → AI Engine → Deployments
2. Find last working deployment (green checkmark)
3. Click **"..."** → **"Redeploy"**
4. Confirm rollback

### Option 2: Via Railway CLI

```bash
railway rollback
```

### Option 3: Git Revert + Push

```bash
git revert HEAD
git push origin AI-engine
# Auto-deploy will trigger with reverted code
```

---

## Scaling Guidelines

### When to Scale Up

Scale to **max=5** instances if:
- CPU consistently > 70%
- Response times > 500ms
- Rate limit errors increasing
- Traffic expected to increase

### When to Scale Down

Scale to **max=1** instance if:
- CPU consistently < 30%
- Low traffic periods (nights/weekends)
- Cost optimization needed

### Manual Scaling

```bash
# Via Railway dashboard
Settings → Resources → Instance Count

# Set manually for specific events
Min: 3, Max: 5 (during high-traffic)
Min: 1, Max: 1 (during maintenance)
```

---

## Security Checklist

- [x] Service is internal-only (no public access)
- [x] JWT required on all endpoints except /health
- [x] All API keys marked as secrets
- [x] Request timeouts enforced
- [x] Payload size limits enforced
- [x] Rate limiting per tenant
- [x] Daily quotas per tenant
- [x] Structured logging (no sensitive data)
- [x] No hardcoded secrets in code

---

## Cost Optimization

### Estimated Costs

**Railway Infrastructure**:
- Light dyno: ~$5/instance/month
- 1-3 instances: $5-15/month

**AI Provider Costs**:
- INLEGALBERT: $0.20 per 1M tokens
- DeepSeek: $0.14 per 1M tokens
- Grok: $0.50 per 1M tokens

**Total Estimated**: $10-30/month (infrastructure) + variable AI costs

### Cost Reduction Tips

1. Use DeepSeek as primary (cheaper)
2. Implement aggressive caching
3. Reduce daily quotas for testing
4. Scale down during off-hours
5. Monitor and alert on unusual usage

---

## Support

**Issues**: Open ticket in Railway dashboard  
**Logs**: Railway → AI Engine → Logs  
**Status**: Check Railway status page  
**Documentation**: See README.md and this DEPLOYMENT.md

