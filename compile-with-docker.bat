@echo off
setlocal

if "%VERSION_SUFFIX%"=="" (
    echo VERSION_SUFFIX must be set to exactly 7 uppercase letters or digits.
    echo Example: set VERSION_SUFFIX=LNR24C5
    exit /b 1
)

set "GIT_BASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%GIT_BASH%" set "GIT_BASH=%LocalAppData%\Programs\Git\bin\bash.exe"

if not exist "%GIT_BASH%" (
    echo Git Bash was not found. Install Git for Windows or run compile-with-docker.sh from WSL.
    exit /b 1
)

"%GIT_BASH%" "%~dp0compile-with-docker.sh"
exit /b %errorlevel%
