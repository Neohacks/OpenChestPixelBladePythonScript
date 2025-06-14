@echo off

net session >nul 2>&1
if %errorlevel% NEQ 0 (
    echo Requesting administrative privileges...
    mshta vbscript:CreateObject^("Shell.Application"^).ShellExecute "C:\Users\offic\AppData\Local\Programs\Python\Python313\python.exe", "C:\Users\offic\Documents\Programming\OpenChestPixelBladePythonScript\openchest.py", "", "runas", 1
    exit /b
)

"C:\Users\offic\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\offic\Documents\Programming\OpenChestPixelBladePythonScript\openchest.py"
pause
