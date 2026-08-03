@echo off
setlocal EnableDelayedExpansion
set "BUNDLED_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%BUNDLED_PY%" (
  "%BUNDLED_PY%" "%~dp0seedance_pipeline.py" %*
  exit /b !errorlevel!
)
where python >nul 2>nul
if not errorlevel 1 (
  python "%~dp0seedance_pipeline.py" %*
  exit /b !errorlevel!
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0seedance_pipeline.py" %*
  exit /b !errorlevel!
)
echo No usable Python runtime was found. 1>&2
exit /b 2
