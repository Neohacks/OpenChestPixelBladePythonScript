@echo off
:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set "params=%*"
    echo UAC.ShellExecute "cmd.exe", "/c %~s0 %params%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"
:--------------------------------------

:: Set the name of your Python script here
set SCRIPT_NAME=openchest.py

:: Check if the Python script exists
if not exist "%SCRIPT_NAME%" (
    echo.
    echo ERROR: Python script '%SCRIPT_NAME%' not found in this folder.
    echo Please make sure this .bat file is in the same folder as your Python script.
    pause
    exit /B
)

echo.
echo ===================================
echo  Pixel Blade Chest Opener Launcher
echo ===================================
echo.

:: Check for Python
echo Checking for Python installation...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not added to your system's PATH.
    echo Please install Python 3 from python.org and ensure "Add to PATH" is checked during installation.
    pause
    exit /B
)
echo Python found.
echo.

:: Check and install dependencies using a more robust method that avoids redirection issues.
echo Checking for required libraries...
set "PACKAGES=pyautogui keyboard pygetwindow pywin32"
for %%p in (%PACKAGES%) do (
    set "installed="
    for /f "tokens=*" %%a in ('python -m pip show %%p 2^>nul ^| findstr /I "Version:"') do (
        set "installed=true"
    )

    if not defined installed (
        echo   -> '%%p' not found, attempting to install...
        python -m pip install %%p
    )
)

echo.
echo All requirements are met. Launching the script...
echo.

:: Run the script
python "%SCRIPT_NAME%"

echo.
echo Script has finished. Press any key to exit.
pause >nul
