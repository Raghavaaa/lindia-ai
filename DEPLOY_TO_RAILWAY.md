# Deploy AI Engine to Railway

## Quick Deploy Guide

### Step 1: Push to GitHub

```bash
# Create a new repository on GitHub (e.g., ai-law-engine)
# Then run:

cd /Users/raghavankarthik/ai-law-junior/ai-engine

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/ai-law-engine.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Railway

1. **Go to Railway**: https://railway.app/
2. **Click "New Project"**
3. **Select "Deploy from GitHub repo"**
4. **Choose your repository**: `ai-law-engine`
5. **Railway will auto-detect** the Procfile and deploy

### Step 3: Configure Environment Variables

In Railway dashboard, add these environment variables:

```
MODEL_PROVIDER=InLegalBERT
BACKEND_URL=https://api.legalindia.ai
ENVIRONMENT=production
PORT=8080
```

**Note**: `API_KEYS` will be added later when integrating actual ML models.

### Step 4: Get Your Service URL

After deployment, Railway will provide a URL like:
- `https://ai-law-engine-production.up.railway.app`
- Or configure custom domain: `https://ai.legalindia.ai`

### Step 5: Verify Deployment

Test the health endpoint:

```bash
# Replace with your actual Railway URL
curl https://your-service.railway.app/health

# Expected response:
# {
#   "status": "ok",
#   "uptime_seconds": 123.45,
#   "model_provider": "InLegalBERT",
#   "service": "ai-engine",
#   "timestamp": "2025-10-17T..."
# }
```

Or simply visit in browser:
```
https://your-service.railway.app/health
```

### Step 6: Update CORS Settings

Once you have the Railway URL, update `main.py` to include it in ALLOWED_ORIGINS:

```python
ALLOWED_ORIGINS = [
    "https://legalindia.ai",
    "https://api.legalindia.ai",
    "https://backend.legalindia.ai",
    "https://your-service.railway.app",  # Add your Railway URL
    os.getenv("BACKEND_URL", "http://localhost:8000"),
]
```

Then commit and push:
```bash
git add main.py
git commit -m "Update CORS with Railway URL"
git push origin main
```

Railway will automatically redeploy.

## Testing All Endpoints

### 1. Health Check
```bash
curl https://your-service.railway.app/health
```

### 2. Inference
```bash
curl -X POST https://your-service.railway.app/inference \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the requirements for a valid contract?",
    "context": "Indian Contract Act, 1872"
  }'
```

### 3. Embeddings
```bash
curl -X POST https://your-service.railway.app/embed \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Legal document 1", "Legal document 2"],
    "model": "InLegalBERT"
  }'
```

### 4. Search
```bash
curl -X POST https://your-service.railway.app/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "contract law precedents",
    "top_k": 5
  }'
```

## Connecting to Backend

Once deployed, update your backend to call the AI Engine:

```python
# In your backend code
AI_ENGINE_URL = "https://ai.legalindia.ai"

# Example: Call inference endpoint
import requests

response = requests.post(
    f"{AI_ENGINE_URL}/inference",
    json={
        "query": user_query,
        "context": case_context
    }
)
answer = response.json()["answer"]
```

## Railway Configuration Files

The following files are configured for Railway:

- ✅ **Procfile** - Tells Railway how to run the app
- ✅ **requirements.txt** - Python dependencies
- ✅ **runtime.txt** - Python version (3.11.6)
- ✅ **.gitignore** - Excludes .env and cache files
- ✅ **railway.json** - Railway-specific configuration

## Monitoring

Railway provides:
- **Logs**: View application logs in real-time
- **Metrics**: CPU, memory, network usage
- **Health Checks**: Automatic monitoring of `/health` endpoint
- **Deployments**: History of all deployments

## Troubleshooting

### Service won't start
- Check Railway logs for errors
- Verify all dependencies in requirements.txt
- Ensure PORT environment variable is set

### CORS errors
- Add your frontend/backend domains to ALLOWED_ORIGINS
- Check environment variable BACKEND_URL is correct

### Health check fails
- Ensure service is running on correct PORT
- Check Railway logs for startup errors

## Next Steps

1. ✅ Service deployed and running
2. ⏳ Integrate actual ML models (InLegalBERT)
3. ⏳ Add vector database (Pinecone/Weaviate)
4. ⏳ Connect to backend service
5. ⏳ Add authentication/API keys
6. ⏳ Set up monitoring and alerting

## Resources

- Railway Docs: https://docs.railway.app/
- FastAPI Docs: https://fastapi.tiangolo.com/
- Service Repository: https://github.com/YOUR_USERNAME/ai-law-engine

---

**Service Status**: Ready for deployment ✅  
**Last Updated**: October 2025

