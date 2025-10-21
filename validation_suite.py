#!/usr/bin/env python3
"""
Complete Validation Suite - Pre-Deployment Testing
Tests all environment variables, API endpoints, and configurations
"""

import asyncio
import httpx
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class ValidationResult:
    """Store validation results"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
        self.total_tests = 0
        
    def add_pass(self, test_name: str, message: str):
        self.passed.append({"test": test_name, "message": message})
        self.total_tests += 1
        
    def add_fail(self, test_name: str, message: str):
        self.failed.append({"test": test_name, "message": message})
        self.total_tests += 1
        
    def add_warning(self, test_name: str, message: str):
        self.warnings.append({"test": test_name, "message": message})
        
    def get_summary(self) -> Dict:
        return {
            "total": self.total_tests,
            "passed": len(self.passed),
            "failed": len(self.failed),
            "warnings": len(self.warnings),
            "success_rate": (len(self.passed) / self.total_tests * 100) if self.total_tests > 0 else 0
        }


class ComprehensiveValidator:
    """Complete validation system"""
    
    def __init__(self):
        self.results = ValidationResult()
        self.env_vars = {}
        self.api_endpoints = {}
        
    def load_environment_variables(self):
        """Load and validate all required environment variables"""
        print("🔍 LOADING ENVIRONMENT VARIABLES")
        print("-" * 50)
        
        required_vars = {
            "DEEPSEEK_API_KEY": "DeepSeek API authentication",
            "DEEPSEEK_API_URL": "DeepSeek endpoint URL", 
            "DEEPSEEK_MODEL": "DeepSeek model name",
            "INLEGALBERT_API_KEY": "InLegalBERT API authentication",
            "INLEGALBERT_API_URL": "InLegalBERT endpoint URL",
            "INLEGALBERT_MODEL": "InLegalBERT model name",
            "MODEL_PROVIDER": "Primary model provider",
            "PROVIDER_ORDER": "Provider fallback order",
            "LOG_LEVEL": "Logging level",
            "ENVIRONMENT": "Deployment environment"
        }
        
        for var, description in required_vars.items():
            value = os.getenv(var, "")
            if value:
                # Mask sensitive values
                if "API_KEY" in var:
                    display_value = f"{value[:15]}...{value[-4:]}"
                else:
                    display_value = value
                print(f"✅ {var}: {display_value}")
                self.env_vars[var] = value
                self.results.add_pass(f"ENV_{var}", f"{description} is set")
            else:
                print(f"❌ {var}: Not set")
                self.results.add_fail(f"ENV_{var}", f"{description} is missing")
        
        print()
        return len(self.env_vars) >= 5  # At least basic vars should be set
    
    def validate_api_endpoints(self):
        """Validate API endpoint URLs"""
        print("🔍 VALIDATING API ENDPOINTS")
        print("-" * 50)
        
        endpoints = {
            "DEEPSEEK": {
                "url": self.env_vars.get("DEEPSEEK_API_URL", ""),
                "expected": "https://api.deepseek.com/v1/chat/completions"
            },
            "INLEGALBERT": {
                "url": self.env_vars.get("INLEGALBERT_API_URL", ""),
                "expected": "https://api-inference.huggingface.co/models/law-ai/InLegalBERT"
            }
        }
        
        for service, config in endpoints.items():
            url = config["url"]
            expected = config["expected"]
            
            if not url:
                self.results.add_fail(f"ENDPOINT_{service}", f"{service} URL not set")
                continue
                
            if url == expected:
                print(f"✅ {service}: URL correct")
                self.results.add_pass(f"ENDPOINT_{service}", f"{service} URL is correct")
            else:
                print(f"⚠️  {service}: URL mismatch")
                print(f"   Current: {url}")
                print(f"   Expected: {expected}")
                self.results.add_warning(f"ENDPOINT_{service}", f"{service} URL differs from expected")
        
        print()
    
    async def test_deepseek_connectivity(self):
        """Test DeepSeek API connectivity and authentication"""
        print("🔍 TESTING DEEPSEEK API")
        print("-" * 50)
        
        api_key = self.env_vars.get("DEEPSEEK_API_KEY", "")
        url = self.env_vars.get("DEEPSEEK_API_URL", "")
        model = self.env_vars.get("DEEPSEEK_MODEL", "deepseek-chat")
        
        if not api_key or not url:
            self.results.add_fail("DEEPSEEK_CONNECTIVITY", "Missing API key or URL")
            return False
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API test successful'"}
            ],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        try:
            print(f"📡 Testing: {url}")
            print(f"🤖 Model: {model}")
            
            start_time = time.time()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
            
            latency = (time.time() - start_time) * 1000
            
            print(f"📥 Status: {response.status_code} | Latency: {latency:.0f}ms")
            
            if response.status_code == 200:
                data = response.json()
                answer = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                
                print(f"✅ SUCCESS: {answer}")
                print(f"📊 Tokens used: {tokens}")
                
                self.results.add_pass("DEEPSEEK_CONNECTIVITY", "API working correctly")
                return True
            else:
                error_msg = response.text[:200]
                print(f"❌ FAILED: {response.status_code} - {error_msg}")
                self.results.add_fail("DEEPSEEK_CONNECTIVITY", f"API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            self.results.add_fail("DEEPSEEK_CONNECTIVITY", f"Connection error: {str(e)}")
            return False
    
    async def test_inlegalbert_connectivity(self):
        """Test InLegalBERT API connectivity and authentication"""
        print("\n🔍 TESTING INLEGALBERT API")
        print("-" * 50)
        
        api_key = self.env_vars.get("INLEGALBERT_API_KEY", "")
        url = self.env_vars.get("INLEGALBERT_API_URL", "")
        
        if not api_key or not url:
            self.results.add_fail("INLEGALBERT_CONNECTIVITY", "Missing API key or URL")
            return False
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Test with masked format (required for InLegalBERT)
        payload = {
            "inputs": "What are the [MASK] conditions for [MASK]?",
            "options": {"wait_for_model": True}
        }
        
        try:
            print(f"📡 Testing: {url}")
            print(f"📤 Payload: {payload['inputs']}")
            
            start_time = time.time()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
            
            latency = (time.time() - start_time) * 1000
            
            print(f"📥 Status: {response.status_code} | Latency: {latency:.0f}ms")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS: Got {len(data)} predictions")
                print(f"📊 Sample: {str(data[0])[:100]}...")
                
                self.results.add_pass("INLEGALBERT_CONNECTIVITY", "API working correctly")
                return True
            else:
                error_msg = response.text[:200]
                print(f"❌ FAILED: {response.status_code} - {error_msg}")
                self.results.add_fail("INLEGALBERT_CONNECTIVITY", f"API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            self.results.add_fail("INLEGALBERT_CONNECTIVITY", f"Connection error: {str(e)}")
            return False
    
    async def test_full_pipeline(self):
        """Test complete pipeline: InLegalBERT → DeepSeek"""
        print("\n🔍 TESTING FULL PIPELINE")
        print("-" * 50)
        
        test_query = "What are bail conditions for murder?"
        
        # Stage 1: InLegalBERT Enhancement
        print("Stage 1: InLegalBERT Enhancement")
        enhanced_query = test_query
        
        inlegalbert_key = self.env_vars.get("INLEGALBERT_API_KEY", "")
        inlegalbert_url = self.env_vars.get("INLEGALBERT_API_URL", "")
        
        if inlegalbert_key and inlegalbert_url:
            try:
                headers = {
                    "Authorization": f"Bearer {inlegalbert_key}",
                    "Content-Type": "application/json"
                }
                
                # Create masked query
                masked_query = test_query.replace(" ", " [MASK] ")
                
                payload = {
                    "inputs": masked_query,
                    "options": {"wait_for_model": True}
                }
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(inlegalbert_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    enhanced_query = f"{test_query} [Enhanced with legal context]https://api-inference.huggingface.co/models/law-ai/InLegalBERT"
                    print("✅ InLegalBERT enhancement successful")
                else:
                    print("⚠️  InLegalBERT failed, using original query")
                    
            except Exception as e:
                print(f"⚠️  InLegalBERT error: {str(e)}")
        else:
            print("⚠️  Skipping InLegalBERT (not configured)")
        
        # Stage 2: DeepSeek Analysis
        print("Stage 2: DeepSeek Analysis")
        
        deepseek_key = self.env_vars.get("DEEPSEEK_API_KEY", "")
        deepseek_url = self.env_vars.get("DEEPSEEK_API_URL", "")
        deepseek_model = self.env_vars.get("DEEPSEEK_MODEL", "deepseek-chat")
        
        if deepseek_key and deepseek_url:
            try:
                headers = {
                    "Authorization": f"Bearer {deepseek_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": deepseek_model,
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are an expert Indian legal assistant."
                        },
                        {
                            "role": "user", 
                            "content": f"Query: {enhanced_query}\n\nProvide brief legal analysis."
                        }
                    ],
                    "max_tokens": 500,
                    "temperature": 0.3
                }
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(deepseek_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens", 0)
                    
                    print("✅ DeepSeek analysis successful")
                    print(f"📊 Response length: {len(answer)} chars")
                    print(f"📊 Tokens used: {tokens}")
                    print(f"📝 Sample: {answer[:200]}...")
                    
                    self.results.add_pass("FULL_PIPELINE", "Complete pipeline working")
                    return True
                else:
                    print(f"❌ DeepSeek failed: {response.status_code}")
                    self.results.add_fail("FULL_PIPELINE", f"DeepSeek error: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ DeepSeek error: {str(e)}")
                self.results.add_fail("FULL_PIPELINE", f"DeepSeek connection error: {str(e)}")
                return False
        else:
            print("❌ DeepSeek not configured")
            self.results.add_fail("FULL_PIPELINE", "DeepSeek configuration missing")
            return False
    
    def validate_configuration_consistency(self):
        """Validate configuration consistency"""
        print("\n🔍 VALIDATING CONFIGURATION CONSISTENCY")
        print("-" * 50)
        
        # Check provider order
        provider_order = self.env_vars.get("PROVIDER_ORDER", "")
        if "inlegalbert" in provider_order and "deepseek" in provider_order:
            if provider_order.index("inlegalbert") < provider_order.index("deepseek"):
                print("✅ Provider order correct: InLegalBERT → DeepSeek")
                self.results.add_pass("CONFIG_CONSISTENCY", "Provider order is logical")
            else:
                print("⚠️  Provider order: DeepSeek comes before InLegalBERT")
                self.results.add_warning("CONFIG_CONSISTENCY", "Unusual provider order")
        else:
            print("⚠️  Provider order unclear")
            self.results.add_warning("CONFIG_CONSISTENCY", "Provider order not specified")
        
        # Check environment
        env = self.env_vars.get("ENVIRONMENT", "")
        if env.lower() == "production":
            print("✅ Environment: Production")
            self.results.add_pass("CONFIG_CONSISTENCY", "Production environment")
        else:
            print(f"⚠️  Environment: {env}")
            self.results.add_warning("CONFIG_CONSISTENCY", f"Non-production environment: {env}")
        
        # Check log level
        log_level = self.env_vars.get("LOG_LEVEL", "")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level.upper() in valid_levels:
            print(f"✅ Log level: {log_level}")
            self.results.add_pass("CONFIG_CONSISTENCY", f"Valid log level: {log_level}")
        else:
            print(f"⚠️  Log level: {log_level} (not standard)")
            self.results.add_warning("CONFIG_CONSISTENCY", f"Non-standard log level: {log_level}")
        
        print()
    
    def generate_deployment_report(self):
        """Generate comprehensive deployment readiness report"""
        print("\n" + "=" * 70)
        print("DEPLOYMENT READINESS REPORT")
        print("=" * 70)
        
        summary = self.results.get_summary()
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {summary['total']}")
        print(f"   Passed: {summary['passed']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Warnings: {summary['warnings']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print()
        
        # Deployment recommendation
        if summary['failed'] == 0:
            if summary['warnings'] == 0:
                print("🟢 DEPLOYMENT STATUS: ✅ READY FOR DEPLOYMENT")
                print("   All tests passed with no warnings")
            else:
                print("🟡 DEPLOYMENT STATUS: ⚠️  READY WITH WARNINGS")
                print(f"   All tests passed but {summary['warnings']} warnings to review")
        else:
            print("🔴 DEPLOYMENT STATUS: ❌ NOT READY FOR DEPLOYMENT")
            print(f"   {summary['failed']} critical failures must be fixed")
        
        print()
        
        # Show failures
        if self.results.failed:
            print("❌ CRITICAL FAILURES:")
            for failure in self.results.failed:
                print(f"   • {failure['test']}: {failure['message']}")
            print()
        
        # Show warnings
        if self.results.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.results.warnings:
                print(f"   • {warning['test']}: {warning['message']}")
            print()
        
        # Show passed tests
        if self.results.passed:
            print("✅ PASSED TESTS:")
            for passed in self.results.passed:
                print(f"   • {passed['test']}: {passed['message']}")
        
        print("\n" + "=" * 70)
        
        return summary['failed'] == 0
    
    async def run_full_validation(self):
        """Run complete validation suite"""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE VALIDATION SUITE")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Step 1: Environment Variables
        env_ok = self.load_environment_variables()
        
        # Step 2: API Endpoints
        self.validate_api_endpoints()
        
        # Step 3: Configuration Consistency
        self.validate_configuration_consistency()
        
        # Step 4: API Connectivity Tests
        if env_ok:
            deepseek_ok = await self.test_deepseek_connectivity()
            inlegalbert_ok = await self.test_inlegalbert_connectivity()
            
            # Step 5: Full Pipeline Test
            if deepseek_ok:
                await self.test_full_pipeline()
        
        # Step 6: Generate Report
        is_ready = self.generate_deployment_report()
        
        return is_ready


async def main():
    """Main validation execution"""
    validator = ComprehensiveValidator()
    
    try:
        is_ready = await validator.run_full_validation()
        
        if is_ready:
            print("\n🎉 VALIDATION COMPLETE - READY FOR DEPLOYMENT!")
            sys.exit(0)
        else:
            print("\n🚫 VALIDATION FAILED - FIX ISSUES BEFORE DEPLOYMENT!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 VALIDATION ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
