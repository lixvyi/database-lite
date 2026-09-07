@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -3 server.py & goto :done)
where python >nul 2>nul
if %errorlevel%==0 (python server.py & goto :done)
where python3 >nul 2>nul
if %errorlevel%==0 (python3 server.py & goto :done)
set "BUNDLED_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%BUNDLED_PY%" ("%BUNDLED_PY%" server.py & goto :done)
echo [错误] 未找到 Python 3，请先安装 Python 3.11 或更高版本。
:done
pause
