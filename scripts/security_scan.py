#!/usr/bin/env python3
"""
FWMIS Security Scanner

Comprehensive security scanning for the FWMIS codebase including:
- Dependency vulnerability scanning
- Code security analysis
- Configuration security checks
- Database security assessment
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass
class SecurityScanResult:
    """Security scan result."""

    tool: str
    passed: bool
    issues: List[Dict[str, Any]]
    summary: str


class SecurityScanner:
    """Comprehensive security scanner for FWMIS."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: List[SecurityScanResult] = []

    def run_full_scan(self) -> bool:
        """Run all security scans."""
        print("🔒 FWMIS Security Scanner")
        print("=" * 50)

        scans = [
            self._scan_dependencies,
            self._scan_code_security,
            self._scan_configuration,
            self._scan_database_security,
            self._scan_file_permissions,
        ]

        all_passed = True
        for scan in scans:
            try:
                result = scan()
                self.results.append(result)
                status = "✅ PASS" if result.passed else "❌ FAIL"
                print(f"{status} {result.tool}: {result.summary}")
                all_passed &= result.passed
            except Exception as e:
                print(f"❌ ERROR {scan.__name__}: {e}")
                all_passed = False

        self._print_summary()
        return all_passed

    def _scan_dependencies(self) -> SecurityScanResult:
        """Scan dependencies for vulnerabilities."""
        print("\n🔍 Scanning dependencies...")

        try:
            # Run safety check
            result = subprocess.run(
                [sys.executable, "-m", "safety", "check", "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                return SecurityScanResult(
                    tool="Dependency Scanner",
                    passed=True,
                    issues=[],
                    summary="No dependency vulnerabilities found",
                )
            else:
                # Parse safety JSON output
                try:
                    safety_data = json.loads(result.stdout)
                    issues = safety_data.get("vulnerabilities", [])
                    return SecurityScanResult(
                        tool="Dependency Scanner",
                        passed=False,
                        issues=issues,
                        summary=f"Found {len(issues)} dependency vulnerabilities",
                    )
                except json.JSONDecodeError:
                    return SecurityScanResult(
                        tool="Dependency Scanner",
                        passed=False,
                        issues=[],
                        summary="Failed to parse safety output",
                    )

        except FileNotFoundError:
            return SecurityScanResult(
                tool="Dependency Scanner",
                passed=False,
                issues=[],
                summary="Safety tool not installed (run: pip install safety)",
            )

    def _scan_code_security(self) -> SecurityScanResult:
        """Scan code for security issues."""
        print("\n🔍 Scanning code security...")

        try:
            # Run bandit
            result = subprocess.run(
                [sys.executable, "-m", "bandit", "-r", "scripts/", "-f", "json"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            bandit_data = json.loads(result.stdout)
            issues = bandit_data.get("results", [])

            # Filter out low-confidence issues
            high_issues = [
                issue
                for issue in issues
                if issue.get("confidence", "").lower() != "low"
            ]

            passed = len(high_issues) == 0

            return SecurityScanResult(
                tool="Code Security Scanner",
                passed=passed,
                issues=high_issues,
                summary=f"Found {len(high_issues)} high-confidence security issues",
            )

        except FileNotFoundError:
            return SecurityScanResult(
                tool="Code Security Scanner",
                passed=False,
                issues=[],
                summary="Bandit tool not installed (run: pip install bandit)",
            )
        except json.JSONDecodeError:
            return SecurityScanResult(
                tool="Code Security Scanner",
                passed=False,
                issues=[],
                summary="Failed to parse bandit output",
            )

    def _scan_configuration(self) -> SecurityScanResult:
        """Scan configuration for security issues."""
        print("\n🔍 Scanning configuration...")

        issues = []

        # Check for hardcoded secrets
        config_files = [
            "scripts/Utilities/config.py",
            "scripts/config/settings.py",
            "pytest.ini",
            "pyproject.toml",
        ]

        secret_patterns = [
            "password",
            "secret",
            "key",
            "token",
            "api_key",
            "database_url",
            "db_url",
            "connection_string",
        ]

        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                try:
                    content = file_path.read_text()
                    for pattern in secret_patterns:
                        if pattern.lower() in content.lower():
                            # Check if it's just a comment or variable name
                            lines = content.split("\n")
                            for i, line in enumerate(lines, 1):
                                if pattern.lower() in line.lower():
                                    # Skip comments and variable declarations
                                    if not (
                                        line.strip().startswith("#")
                                        or "=" in line
                                        or "os.getenv" in line
                                    ):
                                        issues.append(
                                            {
                                                "file": str(config_file),
                                                "line": i,
                                                "pattern": pattern,
                                                "content": line.strip(),
                                            }
                                        )
                except Exception as e:
                    issues.append({"file": str(config_file), "error": str(e)})

        # Check environment variable usage
        env_vars = [
            "FWMIS_DATABASE_PATH",
            "FWMIS_LOG_LEVEL",
            "FWMIS_DEBUG",
            "FWMIS_SECURITY_SESSION_TIMEOUT",
            "FWMIS_SECURITY_MAX_ATTEMPTS",
        ]

        missing_env_vars = []
        for var in env_vars:
            if var not in os.environ:
                missing_env_vars.append(var)

        if missing_env_vars:
            issues.append(
                {
                    "type": "missing_env_vars",
                    "variables": missing_env_vars,
                    "recommendation": "Consider setting default values for production",
                }
            )

        passed = len(issues) == 0

        return SecurityScanResult(
            tool="Configuration Scanner",
            passed=passed,
            issues=issues,
            summary=f"Found {len(issues)} configuration issues",
        )

    def _scan_database_security(self) -> SecurityScanResult:
        """Scan database configuration for security issues."""
        print("\n🔍 Scanning database security...")

        issues = []

        # Check database file permissions
        db_path = self.project_root / "data" / "fruitless.db"
        if db_path.exists():
            # Check if database file is world-readable
            import stat

            file_stat = db_path.stat()
            permissions = stat.filemode(file_stat.st_mode)

            if "o" in permissions:  # Others have permissions
                issues.append(
                    {
                        "type": "database_permissions",
                        "file": str(db_path),
                        "permissions": permissions,
                        "recommendation": "Database file should not be world-readable",
                    }
                )

        # Check for SQL injection patterns (already handled by code scanner)
        # This is a placeholder for future database-specific checks

        passed = len(issues) == 0

        return SecurityScanResult(
            tool="Database Security Scanner",
            passed=passed,
            issues=issues,
            summary=f"Found {len(issues)} database security issues",
        )

    def _scan_file_permissions(self) -> SecurityScanResult:
        """Scan file permissions for security issues."""
        print("\n🔍 Scanning file permissions...")

        issues = []

        # Check critical files
        critical_files = [
            "data/fruitless.db",
            "scripts/config/settings.py",
            "scripts/Utilities/config.py",
        ]

        for file_path_str in critical_files:
            file_path = self.project_root / file_path_str
            if file_path.exists():
                import stat

                try:
                    file_stat = file_path.stat()
                    permissions = stat.filemode(file_stat.st_mode)

                    # Check if file is world-readable/writable
                    if permissions[7] in ["r", "w"] or permissions[8] in ["r", "w"]:
                        issues.append(
                            {
                                "file": file_path_str,
                                "permissions": permissions,
                                "recommendation": "Consider restricting file permissions",
                            }
                        )
                except Exception as e:
                    issues.append({"file": file_path_str, "error": str(e)})

        passed = len(issues) == 0

        return SecurityScanResult(
            tool="File Permissions Scanner",
            passed=passed,
            issues=issues,
            summary=f"Found {len(issues)} file permission issues",
        )

    def _print_summary(self) -> None:
        """Print comprehensive security scan summary."""
        print("\n" + "=" * 50)
        print("🔒 SECURITY SCAN SUMMARY")
        print("=" * 50)

        total_issues = sum(len(result.issues) for result in self.results)
        passed_scans = sum(1 for result in self.results if result.passed)
        total_scans = len(self.results)

        print(f"Scans Passed: {passed_scans}/{total_scans}")
        print(f"Total Issues: {total_issues}")

        if total_issues > 0:
            print("\n🚨 ISSUES FOUND:")
            for result in self.results:
                if not result.passed and result.issues:
                    print(f"\n{result.tool}:")
                    for issue in result.issues[:5]:  # Show first 5 issues
                        if isinstance(issue, dict):
                            if "file" in issue:
                                print(
                                    f"  - {issue['file']}:{issue.get('line', 'N/A')} - {issue.get('pattern', issue.get('type', 'Unknown'))}"
                                )
                            else:
                                print(f"  - {issue}")
                        else:
                            print(f"  - {issue}")

                    if len(result.issues) > 5:
                        print(f"  ... and {len(result.issues) - 5} more issues")

        print("\n📋 RECOMMENDATIONS:")
        print("1. Run security scans regularly in CI/CD pipeline")
        print("2. Keep dependencies updated and scanned")
        print("3. Review code for security anti-patterns")
        print("4. Use environment variables for sensitive configuration")
        print("5. Implement proper access controls")

        overall_passed = all(result.passed for result in self.results)
        if overall_passed:
            print("\n✅ ALL SECURITY CHECKS PASSED!")
        else:
            print("\n❌ SECURITY ISSUES FOUND - REVIEW REQUIRED!")


def main() -> int:
    """Main entry point for security scanner."""
    project_root = Path(__file__).parent.parent

    scanner = SecurityScanner(project_root)
    success = scanner.run_full_scan()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
