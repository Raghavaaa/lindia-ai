"""
Test script for AI Engine API endpoints
Run this after starting the server locally or point to deployed URL
"""

import requests
import json

# Change this to your deployed URL or keep for local testing
BASE_URL = "http://localhost:8080"

def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("✅ Health check passed!")

def test_inference():
    """Test inference endpoint"""
    print("\n🔍 Testing /inference endpoint...")
    payload = {
        "query": "What are the essential elements of a valid contract under Indian law?",
        "context": "Indian Contract Act, 1872",
        "max_tokens": 512,
        "temperature": 0.7
    }
    response = requests.post(f"{BASE_URL}/inference", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert "answer" in response.json()
    print("✅ Inference endpoint passed!")

def test_embed():
    """Test embedding generation endpoint"""
    print("\n🔍 Testing /embed endpoint...")
    payload = {
        "texts": [
            "Section 10 of Indian Contract Act",
            "Contract requires offer and acceptance"
        ],
        "model": "InLegalBERT"
    }
    response = requests.post(f"{BASE_URL}/embed", json=payload)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Model: {result['model']}")
    print(f"Dimension: {result['dimension']}")
    print(f"Number of embeddings: {len(result['embeddings'])}")
    assert response.status_code == 200
    assert len(result["embeddings"]) == 2
    print("✅ Embed endpoint passed!")

def test_search():
    """Test semantic search endpoint"""
    print("\n🔍 Testing /search endpoint...")
    payload = {
        "query": "contract law precedents",
        "top_k": 3,
        "filter": {"court": "Supreme Court"}
    }
    response = requests.post(f"{BASE_URL}/search", json=payload)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Query: {result['query']}")
    print(f"Total Results: {result['total_results']}")
    print(f"Results: {json.dumps(result['results'][:1], indent=2)}")
    assert response.status_code == 200
    assert len(result["results"]) > 0
    print("✅ Search endpoint passed!")

def test_root():
    """Test root endpoint"""
    print("\n🔍 Testing root / endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✅ Root endpoint passed!")

if __name__ == "__main__":
    print("=" * 50)
    print("AI Engine API Testing")
    print("=" * 50)
    print(f"Testing against: {BASE_URL}")
    
    try:
        test_root()
        test_health()
        test_inference()
        test_embed()
        test_search()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        print("=" * 50)
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server")
        print(f"Make sure the server is running at {BASE_URL}")
        print("Start server with: uvicorn main:app --reload --port 8080")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

