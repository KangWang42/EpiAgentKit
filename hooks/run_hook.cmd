@echo off
setlocal
set "BASH_EXE="
for /f "delims=" %%I in ('where bash.exe 2^>nul') do if not defined BASH_EXE set "BASH_EXE=%%I"
for /f "delims=" %%I in ('where git.exe 2^>nul') do if not defined BASH_EXE if exist "%%~dpI..\bin\bash.exe" for %%J in ("%%~dpI..\bin\bash.exe") do set "BASH_EXE=%%~fJ"
if not defined BASH_EXE if exist "%ProgramFiles%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
if not defined BASH_EXE if exist "%LocalAppData%\Programs\Git\bin\bash.exe" set "BASH_EXE=%LocalAppData%\Programs\Git\bin\bash.exe"
if "%~1"=="" exit /b 0
if not defined BASH_EXE (
  echo Git Bash not found. Install Git for Windows or put bash.exe on PATH. 1>&2
  exit /b 1
)
if not "%~2"=="" set "EPIAGENTKIT_HOOK_CLIENT=%~2"
"%BASH_EXE%" "%~1"
exit /b %ERRORLEVEL%
