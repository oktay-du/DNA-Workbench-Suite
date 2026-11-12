@echo off
setlocal
set "DNA_SUITE_ROOT=%~dp0"
cd /d "%~dp0"
set "DNA_PY="
for /d %%P in ("%~dp0DNA_Software\Windows\Python\cpython-*") do if exist "%%~fP\python.exe" set "DNA_PY=%%~fP\python.exe"
if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" goto arm64_python
if /I "%PROCESSOR_ARCHITEW6432%"=="ARM64" goto arm64_python
goto selected_python
:arm64_python
for /d %%P in ("%~dp0DNA_Software\Windows\Python-arm64\cpython-*") do if exist "%%~fP\python.exe" set "DNA_PY=%%~fP\python.exe"
:selected_python
if not defined DNA_PY (
  echo Portable Python fehlt. Bitte zuerst DNA_Launcher.exe einrichten. 1>&2
  exit /b 1
)
set "PYTHONIOENCODING=utf-8"
set "PYTHONNOUSERSITE=1"
"%DNA_PY%" "%~dp0DNA_Software\Launcher\dna_cli.py" %*
exit /b %errorlevel%
