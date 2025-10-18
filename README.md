# Legal India AI Engine

AI/ML service for legal document processing and intelligent querying.

## Model Configuration

### LegalBERT Setup for Railway Deployment

This setup uses LegalBERT remotely to stay within Railway's 4 GB container limit:

- **Model**: `nlpaueb/legal-bert-base-uncased` from Hugging Face Hub
- **Caching**: Models are downloaded to `./cache/` directory on first use
- **Storage**: Cache directory is excluded from git via `.gitignore`
- **Deployment**: Models are downloaded automatically during Railway deployment

### Automatic Model Loading

The system automatically:

1. Checks if `./cache/` directory exists
2. If not, creates the cache directory
3. Downloads LegalBERT model from Hugging Face Hub
4. Caches the model for future use
5. Logs the model source: "Loading LegalBERT from Hugging Face Hub"

### File Structure

```
ai-engine/
├── cache/                    # Model cache (auto-created, git-ignored)
├── providers/
│   └── inlegal_bert_provider.py  # LegalBERT provider with caching
├── .gitignore               # Excludes cache/ and transformers_cache/
└── README.md               # This file
```

### Railway Deployment

- Models are downloaded during deployment startup
- Cache persists between deployments
- Total container size stays under 4 GB limit
- Automatic fallback to API if local model fails

### Usage

The LegalBERT provider automatically handles:
- Model downloading and caching
- Tokenization and inference
- Fallback to Hugging Face API if needed
- Error handling and logging

No manual model setup required - everything is automated for Railway deployment.