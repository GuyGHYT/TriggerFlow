:: THIS FILE IS DEPRECIATED AND IS LEGACY. USE IN RARE CASES ONLY.
 
 --- IGNORE ---

@echo off
title TriggerFlow Installer
echo.
echo ========================================
echo   TriggerFlow Automatic Installer
echo ========================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel%==0 (
    echo Python found! Running setup...
    python setup.py --gui
    goto :end
)

echo Python not found. Installing portable Python...
echo.

:: Create temp directory
if not exist "temp" mkdir temp
cd temp

:: Download portable Python (embeddable package)
echo Downloading Python (this may take a moment)...
powershell -command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.6/python-3.11.6-embed-amd64.zip' -OutFile 'python.zip'}"

if not exist "python.zip" (
    echo Failed to download Python!
    pause
    goto :end
)

:: Extract Python
echo Extracting Python...
powershell -command "& {Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory('python.zip', 'python')}"

:: Download get-pip
echo Setting up pip...
powershell -command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'}"

:: Install pip
python\python.exe get-pip.py

:: Add current directory to Python path
echo import site; site.addsitedir('..') > python\sitecustomize.py

:: Run setup
echo.
echo Running TriggerFlow setup...
cd ..
temp\python\python.exe setup.py --console

:end
echo.
echo Setup complete! You can now run TriggerFlow.bat
pause