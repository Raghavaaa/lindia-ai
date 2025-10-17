# AI Engine - Quick Start Guide

## 🚀 Deploy to Railway in 10 Minutes

### Prerequisites
- Railway account
- LegalIndia project in Railway
- Repository access

---

## Step-by-Step Deployment

### 1. Create Service (2 minutes)

```bash
# Log in to Railway
railway login

# Create new service
railway init
# Name: AI Engine
# Type: Empty Service
```

**OR** via Dashboard:
- Railway → LegalIndia Project → "+ New" → "Empty Service" → Name: "AI Engine"

---

### 2. Configure as Internal (1 minute)

Railway Dashboard → AI Engine → Settings → Networking:
- ✅ **Enable** Private Networking
- ❌ **Disable** Public Networking

**Internal URL**: `http://ai-engine.railway.internal`

---

### 3. Connect Repository (1 minute)

Settings → Source:
- **Repository**: Your repo
- **Branch**: `AI-engine`
- **Root Directory**: `/ai-engine` (if monorepo)
- ✅ **Auto Deploy**: Enabled

---

### 4. Set Environment Variables (3 minutes)

**Copy & paste these** into Railway Variables tab:

```bash
# ⚠️ Generate this first: openssl rand -base64 32
INTERNAL_JWT_SECRET=<paste-generated-secret>  # 🔒 Mark as Secret

PRIMARY_MODEL_KEY=<your-api-key>  # 🔒 Mark as Secret
SECONDARY_MODEL_KEY=<your-api-key>  # 🔒 Mark as Secret
VECTOR_STORE_URL=<your-vector-db-url>

# Configuration (use defaults)
PRIMARY_PROVIDER=INLEGALBERT
FALLBACK_PROVIDERS=DeepSeek,Grok
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=100
DAILY_QUOTA_LIMIT=10000
RUN_SMOKE_TESTS_ON_DEPLOY=true
```

---

### 5. Configure Autoscaling (2 minutes)

Settings → Resources:
- **Runtime**: Light dyno
- **Min Instances**: 1
- **Max Instances**: 3

Settings → Autoscaling:
- **Metric**: CPU Usage
- **Threshold**: 60%

---

### 6. Deploy (1 minute)

Click **"Deploy"** button or push to branch.

Watch logs for:
```
✅ All smoke tests passed
Starting AI Engine Service v1.0.0
```

---

### 7. Verify (30 seconds)

From another Railway service:
```bash
curl http://ai-engine.railway.internal/health
```

Expected:
```json
{"status":"ok","uptime":10.5,"version":"1.0.0"}
```

---

## ✅ You're Done!

**Service URL**: `http://ai-engine.railway.internal`

**Next Steps**:
1. Update main backend with AI Engine URL
2. Share JWT secret with services that need access
3. Test endpoints (see [TESTING.md](./TESTING.md))
4. Monitor logs in Railway Dashboard

---

## 📚 Full Documentation

- [README.md](./README.md) - Complete documentation
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Detailed deployment guide
- [RUNBOOK.md](./RUNBOOK.md) - Admin operations
- [TESTING.md](./TESTING.md) - Testing guide

---

## 🆘 Quick Troubleshooting

| Issue | Fix |
|-------|-----|
| Deployment fails | Check all env vars are set, especially secrets |
| Health check fails | Verify PORT is set to ${{RAILWAY_PORT}} |
| 401 errors | Verify INTERNAL_JWT_SECRET matches in calling services |
| Smoke tests fail | Check logs for specific error, may need to set secrets |

---

## 🔑 Generate JWT Secret

```bash
openssl rand -base64 32
```

Copy the output to `INTERNAL_JWT_SECRET` variable.

---

## 📞 Need Help?

- Check logs: Railway Dashboard → AI Engine → Logs
- Read docs: [README.md](./README.md)
- Contact: Platform Team

---

**Estimated Total Time**: 10 minutes  
**Difficulty**: Easy ⭐⭐☆☆☆

