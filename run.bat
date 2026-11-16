@echo off
setlocal
cd /d "%~dp0"

set "VENV=.venv"
set "VENV_PY=%VENV%\Scripts\python.exe"

rem --- locate a Python interpreter ---
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    echo Python was not found on PATH. Install Python 3 and try again.
    exit /b 1
)

rem --- create the virtual environment on first run ---
if not exist "%VENV_PY%" (
    echo Creating virtual environment in %VENV% ...
    %PY% -m venv "%VENV%"
    if errorlevel 1 (
        echo Failed to create the virtual environment.
        exit /b 1
    )
)

rem --- install / refresh dependencies ---
echo Installing dependencies ...
"%VENV_PY%" -m pip install --disable-pip-version-check --quiet -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements.
    exit /b 1
)

rem --- no arguments: show how to use it ---
if "%~1"=="" (
    echo.
    echo Usage: run.bat ^<globoplay-url^> [options]
    echo.
    echo Example:
    echo   run.bat https://globoplay.globo.com/v/15170205/ -q 720 --subtitles
    echo.
    echo Run "run.bat --help" for all options.
    exit /b 1
)

rem --- run the downloader, forwarding every argument ---
"%VENV_PY%" globoplay_dl.py %*
exit /b %ERRORLEVEL%
