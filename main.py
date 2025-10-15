# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LegalIndia Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://legalindia.ai", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "LegalIndia Backend Active"}

