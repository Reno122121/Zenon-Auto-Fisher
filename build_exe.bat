@echo off
setlocal
cd /d "%~dp0"

set "BUILD_HOME=%LOCALAPPDATA%\ZenonFishingHelperBuild"
set "PYTHON=%BUILD_HOME%\venv\Scripts\python.exe"

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher was not found. Install Python 3.10 or newer from python.org.
    pause
    exit /b 1
)

if not exist "%PYTHON%" (
    if not exist "%BUILD_HOME%" mkdir "%BUILD_HOME%"
    py -3 -m venv "%BUILD_HOME%\venv"
    if errorlevel 1 goto failed
)

"%PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto failed
"%PYTHON%" -m pip install --upgrade -r requirements.txt pyinstaller
if errorlevel 1 goto failed

"%PYTHON%" -m PyInstaller --noconfirm --clean --onefile --windowed --name "Zenon" --icon "%~dp0fishing.ico" --distpath "%~dp0release" --collect-all cv2 --collect-all mss --collect-all pynput fishing_helper.py
if errorlevel 1 goto failed

echo.
echo Finished: %~dp0release\Zenon.exe
pause
exit /b 0

:failed
echo.
echo Build failed. Check the error above, then try again.
pause
exit /b 1
