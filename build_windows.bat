@echo off
setlocal enableextensions

set "ROOT=%~dp0"
cd /d "%ROOT%"

if not exist ".venv\Scripts\activate.bat" (
  echo .venv not found.
  exit /b 1
)

call ".venv\Scripts\activate.bat"

python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
  python -m pip install pyinstaller
  if errorlevel 1 exit /b 1
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m PyInstaller --noconfirm --clean --onedir --name SnapperShot ^
  --add-data "src\snappershot\symbols\symbol_cache.json;src\snappershot\symbols" ^
  --add-data "src\snappershot\data\companies.json;src\snappershot\data" ^
  main.py

exit /b %errorlevel%
