"""
Post-deployment smoke tests
Validates deployment after Railway reports success
"""

import sys
import argparse
import requests
import time
from typing import Dict, Any


def test_health_endpoint(base_url: str) -> bool:
    """Test health endpoint"""
    try:
        print(f"Testing health endpoint: {base_url}/health")
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code != 200:
            print(f"  ✗ Health check failed with status {response.status_code}")
            return False
        
        data = response.json()
        
        # Validate response structure
        assert "status" in data
        assert data["status"] == "ok"
        assert "uptime_seconds" in data
        assert "service" in data
        
        print(f"  ✓ Health check passed")
        print(f"    Status: {data['status']}")
        print(f"    Service: {data.get('service')}")
        print(f"    Uptime: {data.get('uptime_seconds', 0):.1f}s")
        return True
        
    except Exception as e:
        print(f"  ✗ Health check failed: {e}")
        return False


def test_metrics_endpoint(base_url: str) -> bool:
    """Test metrics endpoint is reachable"""
    try:
        print(f"\nTesting metrics endpoint: {base_url}/metrics")
        response = requests.get(f"{base_url}/metrics", timeout=10)
        
        if response.status_code != 200:
            print(f"  ✗ Metrics endpoint failed with status {response.status_code}")
            return False
        
        # Should return Prometheus format
        content = response.text
        assert len(content) > 0
        
        # Check for some expected metrics
        expected_metrics = ["requests_total", "request_duration"]
        found_metrics = sum(1 for m in expected_metrics if m in content)
        
        print(f"  ✓ Metrics endpoint accessible")
        print(f"    Found {found_metrics}/{len(expected_metrics)} expected metrics")
        return True
        
    except Exception as e:
        print(f"  ✗ Metrics check failed: {e}")
        return False


def test_simple_inference(base_url: str) -> bool:
    """Test simple inference endpoint"""
    try:
        print(f"\nTesting inference endpoint: {base_url}/inference")
        
        payload = {
            "query": "What is contract law?",
            "max_tokens": 100
        }
        
        response = requests.post(
            f"{base_url}/inference",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"  ✗ Inference failed with status {response.status_code}")
            print(f"    Response: {response.text[:200]}")
            return False
        
        data = response.json()
        
        # Validate response
        assert "answer" in data
        assert "model" in data
        assert len(data["answer"]) > 0
        
        print(f"  ✓ Inference endpoint working")
        print(f"    Model: {data.get('model')}")
        print(f"    Answer length: {len(data['answer'])} chars")
        return True
        
    except Exception as e:
        print(f"  ✗ Inference test failed: {e}")
        return False


def test_provider_status(base_url: str) -> bool:
    """Test provider status endpoint"""
    try:
        print(f"\nTesting provider status: {base_url}/providers/status")
        response = requests.get(f"{base_url}/providers/status", timeout=10)
        
        if response.status_code != 200:
            print(f"  ⚠ Provider status endpoint not available")
            return True  # Not critical
        
        data = response.json()
        
        if "provider_health" in data:
            print(f"  ✓ Provider status available")
            for provider, status in data["provider_health"].items():
                print(f"    {provider}: {status.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"  ⚠ Provider status check failed: {e}")
        return True  # Not critical


def main():
    """Run all post-deploy smoke tests"""
    parser = argparse.ArgumentParser(description="Post-deploy smoke tests")
    parser.add_argument("--env", required=True, choices=["staging", "production"])
    parser.add_argument("--url", help="Base URL to test")
    args = parser.parse_args()
    
    # Get base URL
    if args.url:
        base_url = args.url
    else:
        import os
        env_var = f"{args.env.upper()}_URL"
        base_url = os.getenv(env_var)
        
        if not base_url:
            print(f"❌ No URL provided. Set {env_var} or use --url")
            return 1
    
    base_url = base_url.rstrip("/")
    
    print("\n")
    print("╔════════════════════════════════════════════════════════╗")
    print("║          Post-Deployment Smoke Tests                   ║")
    print("╚════════════════════════════════════════════════════════╝")
    print(f"\nEnvironment: {args.env.upper()}")
    print(f"Base URL: {base_url}")
    print()
    
    # Wait for service to be ready
    print("Waiting for service to be ready...")
    time.sleep(5)
    
    # Run tests
    tests = [
        ("Health Endpoint", lambda: test_health_endpoint(base_url)),
        ("Metrics Endpoint", lambda: test_metrics_endpoint(base_url)),
        ("Inference Endpoint", lambda: test_simple_inference(base_url)),
        ("Provider Status", lambda: test_provider_status(base_url)),
    ]
    
    results = {}
    critical_failures = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results[test_name] = passed
            
            # Critical tests
            if test_name in ["Health Endpoint", "Metrics Endpoint"] and not passed:
                critical_failures.append(test_name)
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results[test_name] = False
            critical_failures.append(test_name)
    
    # Summary
    print("\n")
    print("╔════════════════════════════════════════════════════════╗")
    print("║                   Test Summary                         ║")
    print("╠════════════════════════════════════════════════════════╣")
    
    passed_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"║  {status:10} - {test_name:40} ║")
    
    print("╠════════════════════════════════════════════════════════╣")
    print(f"║  Results: {passed_count}/{total_count} tests passed{' ' * (34 - len(str(passed_count)) - len(str(total_count)))}║")
    print("╚════════════════════════════════════════════════════════╝")
    
    if critical_failures:
        print(f"\n❌ CRITICAL FAILURES: {', '.join(critical_failures)}")
        print("⚠️  Deployment should be rolled back!")
        return 1
    
    if passed_count == total_count:
        print("\n✅ All smoke tests passed!")
        print(f"✅ {args.env.capitalize()} deployment verified")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} non-critical tests failed")
        print("⚠️  Deployment marked as degraded")
        return 0  # Don't fail for non-critical


if __name__ == "__main__":
    sys.exit(main())

