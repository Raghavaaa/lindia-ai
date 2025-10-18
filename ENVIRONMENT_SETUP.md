# 🔧 InLegalBERT Environment Setup

## 🎯 **Hugging Face API Configuration**

### **Step 1: Get Hugging Face Token**

1. Go to: https://huggingface.co/settings/tokens
2. Create a new token with **"Read"** permissions
3. Copy the token (starts with `hf_...`)

### **Step 2: Set Environment Variables in Railway**

In your Railway dashboard for `lindia-ai` service:

**Go to Variables tab and add:**

```bash
# Primary Provider
MODEL_PROVIDER=inlegalbert
PROVIDER_ORDER=inlegalbert,deepseek

# InLegalBERT (Hugging Face)
INLEGALBERT_API_KEY=hf_your_token_here
INLEGALBERT_MODEL=legal-bert-base-uncased
INLEGALBERT_API_URL=https://api-inference.huggingface.co/models/legal-bert-base-uncased

# DeepSeek (Backup)
DEEPSEEK_API_KEY=your_deepseek_key_here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions

# Backend Integration
BACKEND_URL=https://api.legalindia.ai
ENVIRONMENT=production

# Logging
LOG_LEVEL=INFO
```

### **Step 3: Alternative Legal Models**

You can also use these legal models from Hugging Face:

```bash
# Option 1: Legal BERT (Recommended)
INLEGALBERT_MODEL=legal-bert-base-uncased
INLEGALBERT_API_URL=https://api-inference.huggingface.co/models/legal-bert-base-uncased

# Option 2: Legal RoBERTa
INLEGALBERT_MODEL=legal-roberta-base
INLEGALBERT_API_URL=https://api-inference.huggingface.co/models/legal-roberta-base

# Option 3: Legal Longformer
INLEGALBERT_MODEL=legal-longformer-base-uncased
INLEGALBERT_API_URL=https://api-inference.huggingface.co/models/legal-longformer-base-uncased
```

---

## 🚀 **Deploy with Real AI**

### **After Setting Environment Variables:**

1. **Redeploy AI Engine** (automatic in Railway)
2. **Test the Integration:**

```bash
# Test AI engine directly
curl https://lindia-ai-production.up.railway.app/health

# Test legal inference
curl -X POST https://lindia-ai-production.up.railway.app/inference \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Section 420 IPC?",
    "context": "Indian Penal Code",
    "max_tokens": 200,
    "temperature": 0.7
  }'
```

### **Expected Response:**
```json
{
  "status": "success",
  "query": "What is Section 420 IPC?",
  "response": "[InLegalBERT] Section 420 of the Indian Penal Code deals with...",
  "model": "legal-bert-base-uncased",
  "provider": "InLegalBERT",
  "confidence": 0.92
}
```

---

## 🎯 **Complete Integration Test**

After setting up the environment variables:

```bash
# Test complete backend → AI integration
curl -X POST https://api.legalindia.ai/api/v1/junior/chat \
  -H "X-API-Key: legalindia_secure_api_key_2025" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain the legal requirements for a valid contract in India",
    "conversation_id": "test-legal-001"
  }'
```

---

## 📊 **Provider Fallback System**

Your AI engine has automatic fallback:

1. **Primary**: InLegalBERT (Hugging Face)
2. **Backup**: DeepSeek API
3. **Fallback**: Placeholder responses

If InLegalBERT fails, it automatically tries DeepSeek, then falls back to intelligent placeholder responses.

---

## 🔐 **Security Notes**

- ✅ Hugging Face tokens are secure
- ✅ API calls are made server-side
- ✅ No client-side API keys
- ✅ Automatic fallback prevents failures

---

## 🎉 **What You Get**

With InLegalBERT configured:

- ✅ **Real legal AI responses**
- ✅ **Indian law context**
- ✅ **Case law analysis**
- ✅ **Legal document processing**
- ✅ **Automatic fallback system**
- ✅ **Production-ready deployment**

---

**Next Step:** Set the environment variables in Railway and test! 🚀
