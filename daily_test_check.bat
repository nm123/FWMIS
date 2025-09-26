@echo off
REM FWMIS Daily Test Verification Script
REM Run this at the end of each development day to ensure test coverage

echo ========================================
echo FWMIS Daily Test Verification
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Running test verification...
python daily_test_verification.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ VERIFICATION PASSED - All tests properly integrated!
    echo.
    echo Next steps:
    echo   - Run full test suite: python test_runner.py --full-suite
    echo   - Commit your changes
) else (
    echo.
    echo ❌ VERIFICATION FAILED - Issues need attention!
    echo.
    echo To auto-fix common issues, run:
    echo   python daily_test_verification.py --auto-fix
    echo.
    echo Then re-run this script.
)

echo.
echo Press any key to continue...
pause >nul
