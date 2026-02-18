@echo off
echo ========================================
echo simple_libcst_fix Self Test
echo ========================================
echo.

set PYTHON="C:\Program Files\Python312\python.exe"
set TOOL=.\tools\simple_libcst_fix.py
set TESTFILE=.\test_not_py.txt

REM Check if tool exists
if not exist %TOOL% (
    echo ERROR: Tool not found: %TOOL%
    exit /b 1
)

REM Create test file
echo this is a text file > %TESTFILE%
echo Created test file: %TESTFILE%

set PASSED=0
set FAILED=0

:test1
echo.
echo Test 1: Project dry-run
echo Command: %PYTHON% %TOOL% . --dry-run
%PYTHON% %TOOL% . --dry-run
if %errorlevel% equ 0 (
    echo PASS: exit code 0
    set /a PASSED+=1
) else (
    echo FAIL: expected 0, got %errorlevel%
    set /a FAILED+=1
)

:test2
echo.
echo Test 2: Non-Python strict mode
echo Command: %PYTHON% %TOOL% %TESTFILE% --dry-run
%PYTHON% %TOOL% %TESTFILE% --dry-run
if %errorlevel% equ 2 (
    echo PASS: exit code 2
    set /a PASSED+=1
) else (
    echo FAIL: expected 2, got %errorlevel%
    set /a FAILED+=1
)

:test3
echo.
echo Test 3: Non-Python allow mode
echo Command: %PYTHON% %TOOL% %TESTFILE% --dry-run --allow-nonpy -v
%PYTHON% %TOOL% %TESTFILE% --dry-run --allow-nonpy -v
if %errorlevel% equ 0 (
    echo PASS: exit code 0
    set /a PASSED+=1
) else (
    echo FAIL: expected 0, got %errorlevel%
    set /a FAILED+=1
)

:test4
echo.
echo Test 4: Actual fix mode
echo Command: %PYTHON% %TOOL% .
%PYTHON% %TOOL% .
if %errorlevel% equ 0 (
    echo PASS: exit code 0
    set /a PASSED+=1
) else (
    echo FAIL: expected 0, got %errorlevel%
    set /a FAILED+=1
)

:test5
echo.
echo Test 5: Help info
echo Command: %PYTHON% %TOOL% --help
%PYTHON% %TOOL% --help
if %errorlevel% equ 0 (
    echo PASS: exit code 0
    set /a PASSED+=1
) else (
    echo FAIL: expected 0, got %errorlevel%
    set /a FAILED+=1
)

:test6
echo.
echo Test 6: Verbose project check
echo Command: %PYTHON% %TOOL% . --dry-run -v
%PYTHON% %TOOL% . --dry-run -v
if %errorlevel% equ 0 (
    echo PASS: exit code 0
    set /a PASSED+=1
) else (
    echo FAIL: expected 0, got %errorlevel%
    set /a FAILED+=1
)

REM Cleanup
del %TESTFILE% 2>nul
echo.
echo Cleaned up test file

REM Summary
echo.
echo ========================================
echo Test Results
echo ========================================
echo Passed: %PASSED%
echo Failed: %FAILED%

if %FAILED% equ 0 (
    echo.
    echo All tests passed! Tool is functional.
    echo Tool status: PRODUCTION READY
    exit /b 0
) else (
    echo.
    echo Some tests failed. Please check tool functionality.
    exit /b 1
)