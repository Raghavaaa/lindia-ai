#!/usr/bin/env python3
"""
Quick V&V System Test
Tests the Pre-Deployment Verification system without full checks
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pre_deployment_vv import PreDeploymentVV, CheckResult, CheckStatus

async def test_vv_system():
    """Test the V&V system functionality"""
    print("🧪 TESTING V&V SYSTEM")
    print("=" * 50)
    
    vv_system = PreDeploymentVV()
    
    # Test individual checks
    print("\n1. Testing Syntax & Linting Check...")
    result1 = vv_system.check_1_syntax_linting()
    print(f"   Result: {result1.status.value} - {result1.message}")
    
    print("\n2. Testing Environment Validation...")
    result2 = vv_system.check_7_env_validation()
    print(f"   Result: {result2.status.value} - {result2.message}")
    
    print("\n3. Testing Build Integrity...")
    result3 = vv_system.check_4_build_integrity()
    print(f"   Result: {result3.status.value} - {result3.message}")
    
    # Test report generation
    print("\n4. Testing Report Generation...")
    test_results = [result1, result2, result3]
    report = vv_system.generate_vv_report(test_results)
    
    print(f"   Commit: {report.commit_hash}")
    print(f"   Safe to Push: {report.safe_to_push}")
    print(f"   Overall Status: {report.overall_status.value}")
    
    print("\n✅ V&V System Test Complete")
    return True

if __name__ == "__main__":
    asyncio.run(test_vv_system())
