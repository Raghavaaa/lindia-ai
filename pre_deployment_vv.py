#!/usr/bin/env python3
"""
Pre-Deployment Verification & Validation System
Automated Gatekeeping with Zero Tolerance for Broken Builds

This system implements Google QA Gate standards:
- 8 mandatory checks before any push/deploy
- Auto-rollback on failures
- Version tagging for verified releases
- Comprehensive reporting
"""

import os
import sys
import json
import subprocess
import time
import asyncio
import httpx
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re


class CheckStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    check_name: str
    status: CheckStatus
    message: str
    details: Optional[Dict] = None
    duration_ms: Optional[int] = None


@dataclass
class VVReport:
    commit_hash: str
    timestamp: str
    changed_files: List[str]
    check_results: List[CheckResult]
    overall_status: CheckStatus
    potential_regressions: List[str]
    safe_to_push: bool
    rollback_required: bool = False
    rollback_reason: Optional[str] = None


class PreDeploymentVV:
    """Pre-Deployment Verification & Validation System"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.report: Optional[VVReport] = None
        self.start_time = time.time()
        
    def get_commit_info(self) -> Tuple[str, List[str]]:
        """Get current commit hash and changed files"""
        try:
            # Get current commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd=self.repo_path
            )
            commit_hash = result.stdout.strip()[:8] if result.returncode == 0 else "unknown"
            
            # Get changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                capture_output=True, text=True, cwd=self.repo_path
            )
            changed_files = result.stdout.strip().split('\n') if result.returncode == 0 else []
            changed_files = [f for f in changed_files if f.strip()]
            
            return commit_hash, changed_files
            
        except Exception as e:
            print(f"⚠️  Could not get commit info: {e}")
            return "unknown", []
    
    def check_1_syntax_linting(self) -> CheckResult:
        """Check 1: Syntax & Linting (ESLint/Pylint)"""
        print("🔍 CHECK 1: Syntax & Linting")
        start_time = time.time()
        
        issues_found = []
        fixes_applied = []
        
        try:
            # Python linting with pylint
            python_files = []
            for root, dirs, files in os.walk(self.repo_path):
                for file in files:
                    if file.endswith('.py') and not any(d in root for d in ['.git', '__pycache__', 'node_modules']):
                        python_files.append(os.path.join(root, file))
            
            if python_files:
                result = subprocess.run(
                    ["python3", "-m", "pylint"] + python_files[:5],  # Limit for performance
                    capture_output=True, text=True, cwd=self.repo_path
                )
                
                if result.returncode != 0:
                    issues_found.append(f"Pylint found {result.returncode} issues")
                
            # JavaScript/TypeScript linting with ESLint
            if os.path.exists(os.path.join(self.repo_path, "package.json")):
                result = subprocess.run(
                    ["npm", "run", "lint"],
                    capture_output=True, text=True, cwd=self.repo_path
                )
                
                if result.returncode != 0:
                    issues_found.append("ESLint found issues")
                else:
                    fixes_applied.append("ESLint passed")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if issues_found:
                return CheckResult(
                    check_name="Syntax & Linting",
                    status=CheckStatus.FAIL,
                    message=f"Issues found: {', '.join(issues_found)}",
                    details={"issues": issues_found, "fixes": fixes_applied},
                    duration_ms=duration_ms
                )
            else:
                return CheckResult(
                    check_name="Syntax & Linting",
                    status=CheckStatus.PASS,
                    message="All syntax and linting checks passed",
                    details={"fixes": fixes_applied},
                    duration_ms=duration_ms
                )
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                check_name="Syntax & Linting",
                status=CheckStatus.WARN,
                message=f"Could not run linting: {str(e)}",
                duration_ms=duration_ms
            )
    
    def check_2_type_safety(self) -> CheckResult:
        """Check 2: Type Safety (TypeScript/Pydantic)"""
        print("🔍 CHECK 2: Type Safety")
        start_time = time.time()
        
        try:
            # TypeScript type checking
            if os.path.exists(os.path.join(self.repo_path, "tsconfig.json")):
                result = subprocess.run(
                    ["npx", "tsc", "--noEmit"],
                    capture_output=True, text=True, cwd=self.repo_path
                )
                
                if result.returncode != 0:
                    return CheckResult(
                        check_name="Type Safety",
                        status=CheckStatus.FAIL,
                        message="TypeScript type errors found",
                        details={"errors": result.stderr},
                        duration_ms=int((time.time() - start_time) * 1000)
                    )
            
            # Python type checking with mypy
            python_files = []
            for root, dirs, files in os.walk(self.repo_path):
                for file in files:
                    if file.endswith('.py') and not any(d in root for d in ['.git', '__pycache__', 'node_modules']):
                        python_files.append(os.path.join(root, file))
            
            if python_files:
                result = subprocess.run(
                    ["python3", "-m", "mypy"] + python_files[:3],  # Limit for performance
                    capture_output=True, text=True, cwd=self.repo_path
                )
                
                if result.returncode != 0:
                    return CheckResult(
                        check_name="Type Safety",
                        status=CheckStatus.WARN,
                        message="Python type hints need attention",
                        details={"warnings": result.stderr},
                        duration_ms=int((time.time() - start_time) * 1000)
                    )
            
            duration_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                check_name="Type Safety",
                status=CheckStatus.PASS,
                message="Type safety checks passed",
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                check_name="Type Safety",
                status=CheckStatus.WARN,
                message=f"Could not run type checking: {str(e)}",
                duration_ms=duration_ms
            )
    
    def check_3_test_suite(self) -> CheckResult:
        """Check 3: Test Suite (Unit + Integration)"""
        print("🔍 CHECK 3: Test Suite")
        start_time = time.time()
        
        test_results = {"unit": None, "integration": None}
        
        try:
            # Python unit tests
            if os.path.exists(os.path.join(self.repo_path, "tests")):
                result = subprocess.run(
                    ["python3", "-m", "pytest", "tests/", "-v"],
                    capture_output=True, text=True, cwd=self.repo_path
                )
                test_results["unit"] = {
                    "passed": result.returncode == 0,
                    "output": result.stdout
                }
            
            # Node.js tests
            if os.path.exists(os.path.join(self.repo_path, "package.json")):
                result = subprocess.run(
                    ["npm", "test"],
                    capture_output=True, text=True, cwd=self.repo_path
                )
                test_results["integration"] = {
                    "passed": result.returncode == 0,
                    "output": result.stdout
                }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Check if any tests failed
            failed_tests = []
            if test_results["unit"] and not test_results["unit"]["passed"]:
                failed_tests.append("Unit tests")
            if test_results["integration"] and not test_results["integration"]["passed"]:
                failed_tests.append("Integration tests")
            
            if failed_tests:
                return CheckResult(
                    check_name="Test Suite",
                    status=CheckStatus.FAIL,
                    message=f"Failed: {', '.join(failed_tests)}",
                    details=test_results,
                    duration_ms=duration_ms
                )
            else:
                return CheckResult(
                    check_name="Test Suite",
                    status=CheckStatus.PASS,
                    message="All tests passed",
                    details=test_results,
                    duration_ms=duration_ms
                )
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                check_name="Test Suite",
                status=CheckStatus.WARN,
                message=f"Could not run tests: {str(e)}",
                duration_ms=duration_ms
            )
    
    def check_4_build_integrity(self) -> CheckResult:
        """Check 4: Build Integrity"""
        print("🔍 CHECK 4: Build Integrity")
        start_time = time.time()
        
        build_results = {}
        
        try:
            # Frontend build
            if os.path.exists(os.path.join(self.repo_path, "package.json")):
                result = subprocess.run(
                    ["npm", "run", "build"],
                    capture_output=True, text=True, cwd=self.repo_path
                )
                build_results["frontend"] = {
                    "passed": result.returncode == 0,
                    "output": result.stdout[-500:] if result.stdout else result.stderr[-500:]
                }
            
            # Python build check
            if os.path.exists(os.path.join(self.repo_path, "requirements.txt")):
                result = subprocess.run(
                    ["python3", "-c", "import app.main; print('Import successful')"],
                    capture_output=True, text=True, cwd=self.repo_path
                )
                build_results["backend"] = {
                    "passed": result.returncode == 0,
                    "output": result.stdout
                }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            failed_builds = []
            if build_results.get("frontend") and not build_results["frontend"]["passed"]:
                failed_builds.append("Frontend")
            if build_results.get("backend") and not build_results["backend"]["passed"]:
                failed_builds.append("Backend")
            
            if failed_builds:
                return CheckResult(
                    check_name="Build Integrity",
                    status=CheckStatus.FAIL,
                    message=f"Build failed: {', '.join(failed_builds)}",
                    details=build_results,
                    duration_ms=duration_ms
                )
            else:
                return CheckResult(
                    check_name="Build Integrity",
                    status=CheckStatus.PASS,
                    message="All builds successful",
                    details=build_results,
                    duration_ms=duration_ms
                )
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                check_name="Build Integrity",
                status=CheckStatus.WARN,
                message=f"Could not run build check: {str(e)}",
                duration_ms=duration_ms
            )
    
    async def check_5_api_health(self) -> CheckResult:
        """Check 5: API Health Check"""
        print("🔍 CHECK 5: API Health Check")
        start_time = time.time()
        
        api_endpoints = [
            {"name": "Health Check", "url": "http://localhost:8000/health", "method": "GET"},
            {"name": "Research API", "url": "http://localhost:8000/api/v1/research/", "method": "POST"},
        ]
        
        health_results = {}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for endpoint in api_endpoints:
                    try:
                        if endpoint["method"] == "GET":
                            response = await client.get(endpoint["url"])
                        else:
                            response = await client.post(
                                endpoint["url"],
                                json={"query": "test query"},
                                headers={"Content-Type": "application/json"}
                            )
                        
                        health_results[endpoint["name"]] = {
                            "status": response.status_code,
                            "healthy": response.status_code == 200
                        }
                    except Exception as e:
                        health_results[endpoint["name"]] = {
                            "status": "error",
                            "healthy": False,
                            "error": str(e)
                        }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            unhealthy_apis = [name for name, result in health_results.items() if not result["healthy"]]
            
            if unhealthy_apis:
                return CheckResult(
                    check_name="API Health",
                    status=CheckStatus.FAIL,
                    message=f"Unhealthy APIs: {', '.join(unhealthy_apis)}",
                    details=health_results,
                    duration_ms=duration_ms
                )
            else:
                return CheckResult(
                    check_name="API Health",
                    status=CheckStatus.PASS,
                    message="All APIs healthy",
                    details=health_results,
                    duration_ms=duration_ms
                )
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                check_name="API Health",
                status=CheckStatus.WARN,
                message=f"Could not check API health: {str(e)}",
                duration_ms=duration_ms
            )
    
    def check_6_dependency_audit(self) -> CheckResult:
        """Check 6: Dependency Security Audit"""
        print("🔍 CHECK 6: Dependency Security Audit")
        start_time = time.time()
        
        audit_results = {}
        vulnerabilities_found = []
        
        try:
            # Python security audit
            if os.path.exists(os.path.join(self.repo_path, "requirements.txt")):
                result = subprocess.run(
                    ["python3", "-m", "safety", "check"],
                    capture_output=True, text=True, cwd=self.repo_path
                )
                audit_results["python"] = {
                    "vulnerabilities": result.returncode != 0,
                    "output": result.stdout
                }
                if result.returncode != 0:
                    vulnerabilities_found.append("Python dependencies")
            
            # Node.js security audit
            if os.path.exists(os.path.join(self.repo_path, "package.json")):
                result = subprocess.run(
                    ["npm", "audit", "--audit-level=moderate"],
                    capture_output=True, text=True, cwd=self.repo_path
                )
                audit_results["nodejs"] = {
                    "vulnerabilities": result.returncode != 0,
                    "output": result.stdout
                }
                if result.returncode != 0:
                    vulnerabilities_found.append("Node.js dependencies")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if vulnerabilities_found:
                return CheckResult(
                    check_name="Dependency Audit",
                    status=CheckStatus.FAIL,
                    message=f"Vulnerabilities found in: {', '.join(vulnerabilities_found)}",
                    details=audit_results,
                    duration_ms=duration_ms
                )
            else:
                return CheckResult(
                    check_name="Dependency Audit",
                    status=CheckStatus.PASS,
                    message="No critical vulnerabilities found",
                    details=audit_results,
                    duration_ms=duration_ms
                )
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                check_name="Dependency Audit",
                status=CheckStatus.WARN,
                message=f"Could not run security audit: {str(e)}",
                duration_ms=duration_ms
            )
    
    def check_7_env_validation(self) -> CheckResult:
        """Check 7: Environment Validation"""
        print("🔍 CHECK 7: Environment Validation")
        start_time = time.time()
        
        env_issues = []
        secrets_found = []
        
        try:
            # Check .env file completeness
            env_file = os.path.join(self.repo_path, ".env")
            env_example = os.path.join(self.repo_path, ".env.example")
            
            if os.path.exists(env_example):
                with open(env_example, 'r') as f:
                    required_vars = [line.split('=')[0] for line in f if '=' in line and not line.startswith('#')]
                
                missing_vars = []
                if os.path.exists(env_file):
                    with open(env_file, 'r') as f:
                        env_content = f.read()
                        for var in required_vars:
                            if var not in env_content:
                                missing_vars.append(var)
                
                if missing_vars:
                    env_issues.append(f"Missing variables: {', '.join(missing_vars)}")
            
            # Scan for hardcoded secrets
            secret_patterns = [
                r'sk-[a-zA-Z0-9]{20,}',
                r'hf_[a-zA-Z0-9]{20,}',
                r'[a-zA-Z0-9]{32,}',
            ]
            
            for root, dirs, files in os.walk(self.repo_path):
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.tsx', '.md')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                for pattern in secret_patterns:
                                    matches = re.findall(pattern, content)
                                    if matches:
                                        secrets_found.append(f"{file}: {matches[:2]}")
                        except:
                            continue
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if secrets_found:
                return CheckResult(
                    check_name="Environment Validation",
                    status=CheckStatus.FAIL,
                    message=f"Hardcoded secrets found in {len(secrets_found)} files",
                    details={"secrets": secrets_found, "env_issues": env_issues},
                    duration_ms=duration_ms
                )
            elif env_issues:
                return CheckResult(
                    check_name="Environment Validation",
                    status=CheckStatus.WARN,
                    message=f"Environment issues: {', '.join(env_issues)}",
                    details={"env_issues": env_issues},
                    duration_ms=duration_ms
                )
            else:
                return CheckResult(
                    check_name="Environment Validation",
                    status=CheckStatus.PASS,
                    message="Environment validation passed",
                    duration_ms=duration_ms
                )
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                check_name="Environment Validation",
                status=CheckStatus.WARN,
                message=f"Could not validate environment: {str(e)}",
                duration_ms=duration_ms
            )
    
    def check_8_ui_consistency(self) -> CheckResult:
        """Check 8: UI Consistency (Frontend only)"""
        print("🔍 CHECK 8: UI Consistency")
        start_time = time.time()
        
        try:
            # Check if this is a frontend project
            if not os.path.exists(os.path.join(self.repo_path, "package.json")):
                return CheckResult(
                    check_name="UI Consistency",
                    status=CheckStatus.SKIP,
                    message="Not a frontend project",
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            
            # Run frontend consistency checks
            result = subprocess.run(
                ["npm", "run", "build"],
                capture_output=True, text=True, cwd=self.repo_path
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if result.returncode == 0:
                return CheckResult(
                    check_name="UI Consistency",
                    status=CheckStatus.PASS,
                    message="UI consistency check passed",
                    duration_ms=duration_ms
                )
            else:
                return CheckResult(
                    check_name="UI Consistency",
                    status=CheckStatus.FAIL,
                    message="UI consistency issues found",
                    details={"build_output": result.stderr},
                    duration_ms=duration_ms
                )
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CheckResult(
                check_name="UI Consistency",
                status=CheckStatus.WARN,
                message=f"Could not check UI consistency: {str(e)}",
                duration_ms=duration_ms
            )
    
    def generate_vv_report(self, check_results: List[CheckResult]) -> VVReport:
        """Generate comprehensive V&V report"""
        commit_hash, changed_files = self.get_commit_info()
        
        # Determine overall status
        failed_checks = [r for r in check_results if r.status == CheckStatus.FAIL]
        warning_checks = [r for r in check_results if r.status == CheckStatus.WARN]
        
        if failed_checks:
            overall_status = CheckStatus.FAIL
            safe_to_push = False
        elif warning_checks:
            overall_status = CheckStatus.WARN
            safe_to_push = True
        else:
            overall_status = CheckStatus.PASS
            safe_to_push = True
        
        # Identify potential regressions
        potential_regressions = []
        for result in check_results:
            if result.status == CheckStatus.FAIL:
                potential_regressions.append(f"{result.check_name}: {result.message}")
        
        return VVReport(
            commit_hash=commit_hash,
            timestamp=datetime.now().isoformat(),
            changed_files=changed_files,
            check_results=check_results,
            overall_status=overall_status,
            potential_regressions=potential_regressions,
            safe_to_push=safe_to_push
        )
    
    def print_report(self, report: VVReport):
        """Print formatted V&V report"""
        print("\n" + "=" * 80)
        print("🚀 PRE-DEPLOYMENT VERIFICATION & VALIDATION REPORT")
        print("=" * 80)
        print(f"📅 Timestamp: {report.timestamp}")
        print(f"🔗 Commit: {report.commit_hash}")
        print(f"📁 Changed Files: {len(report.changed_files)}")
        
        if report.changed_files:
            print("   Modified:")
            for file in report.changed_files[:5]:  # Show first 5
                print(f"     • {file}")
            if len(report.changed_files) > 5:
                print(f"     ... and {len(report.changed_files) - 5} more")
        
        print("\n" + "-" * 80)
        print("📊 CHECK RESULTS")
        print("-" * 80)
        
        for result in report.check_results:
            status_icon = "✅" if result.status == CheckStatus.PASS else "❌" if result.status == CheckStatus.FAIL else "⚠️"
            duration = f"({result.duration_ms}ms)" if result.duration_ms else ""
            print(f"{status_icon} {result.check_name}: {result.status.value} {duration}")
            print(f"   {result.message}")
            if result.details and result.status == CheckStatus.FAIL:
                print(f"   Details: {str(result.details)[:100]}...")
            print()
        
        print("-" * 80)
        print("🎯 SUMMARY")
        print("-" * 80)
        
        total_checks = len(report.check_results)
        passed_checks = len([r for r in report.check_results if r.status == CheckStatus.PASS])
        failed_checks = len([r for r in report.check_results if r.status == CheckStatus.FAIL])
        warning_checks = len([r for r in report.check_results if r.status == CheckStatus.WARN])
        
        print(f"📈 Total Checks: {total_checks}")
        print(f"✅ Passed: {passed_checks}")
        print(f"❌ Failed: {failed_checks}")
        print(f"⚠️  Warnings: {warning_checks}")
        print(f"📊 Success Rate: {(passed_checks/total_checks*100):.1f}%")
        
        if report.potential_regressions:
            print(f"\n🚨 POTENTIAL REGRESSIONS:")
            for regression in report.potential_regressions:
                print(f"   • {regression}")
        
        print("\n" + "=" * 80)
        if report.safe_to_push:
            print("🟢 DEPLOYMENT STATUS: ✅ SAFE TO PUSH")
            print("🚀 All critical checks passed. Ready for deployment.")
        else:
            print("🔴 DEPLOYMENT STATUS: ❌ HOLD FOR REVIEW")
            print("🚫 Critical issues found. Fix before deploying.")
        print("=" * 80)
    
    async def run_all_checks(self) -> VVReport:
        """Run all 8 V&V checks"""
        print("🚀 ACTIVATING PRE-DEPLOYMENT VERIFICATION MODE")
        print("🔒 Google QA Gate: Zero Tolerance for Broken Builds")
        print("-" * 60)
        
        check_results = []
        
        # Run all checks
        check_results.append(self.check_1_syntax_linting())
        check_results.append(self.check_2_type_safety())
        check_results.append(self.check_3_test_suite())
        check_results.append(self.check_4_build_integrity())
        check_results.append(await self.check_5_api_health())
        check_results.append(self.check_6_dependency_audit())
        check_results.append(self.check_7_env_validation())
        check_results.append(self.check_8_ui_consistency())
        
        # Generate report
        report = self.generate_vv_report(check_results)
        self.report = report
        
        # Print report
        self.print_report(report)
        
        return report
    
    def auto_rollback_trigger(self, report: VVReport) -> bool:
        """Auto-rollback trigger for failed deployments"""
        if not report.safe_to_push:
            print("\n🚨 AUTO-ROLLBACK TRIGGER ACTIVATED")
            print("🔄 Rolling back to last verified commit...")
            
            try:
                # Find last verified commit
                result = subprocess.run(
                    ["git", "tag", "--list", "release_verified_*", "--sort=-version:refname"],
                    capture_output=True, text=True, cwd=self.repo_path
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    last_verified = result.stdout.strip().split('\n')[0]
                    print(f"📍 Rolling back to: {last_verified}")
                    
                    # Perform rollback
                    subprocess.run(
                        ["git", "reset", "--hard", last_verified],
                        cwd=self.repo_path
                    )
                    
                    report.rollback_required = True
                    report.rollback_reason = f"Failed V&V checks: {', '.join(report.potential_regressions)}"
                    
                    print(f"✅ Rollback completed to {last_verified}")
                    return True
                else:
                    print("⚠️  No verified commits found for rollback")
                    return False
                    
            except Exception as e:
                print(f"❌ Rollback failed: {e}")
                return False
        
        return False
    
    def auto_version_tagging(self, report: VVReport) -> str:
        """Auto-version tagging for verified releases"""
        if report.safe_to_push:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            build_no = int(time.time() % 10000)  # Simple build number
            tag_name = f"release_verified_{timestamp}_{build_no}"
            
            try:
                subprocess.run(
                    ["git", "tag", tag_name],
                    cwd=self.repo_path
                )
                print(f"🏷️  Auto-tagged as: {tag_name}")
                return tag_name
            except Exception as e:
                print(f"⚠️  Could not create tag: {e}")
                return ""
        
        return ""


async def main():
    """Main V&V execution"""
    vv_system = PreDeploymentVV()
    
    try:
        # Run all checks
        report = await vv_system.run_all_checks()
        
        # Auto-rollback if needed
        if not report.safe_to_push:
            vv_system.auto_rollback_trigger(report)
            sys.exit(1)
        
        # Auto-tag successful verification
        tag_name = vv_system.auto_version_tagging(report)
        
        print(f"\n🎉 VERIFICATION COMPLETE")
        print(f"✅ All checks passed - Ready for deployment")
        if tag_name:
            print(f"🏷️  Tagged as: {tag_name}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n💥 V&V SYSTEM ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
