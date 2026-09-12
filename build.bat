@echo off
setlocal
cd /d "%~dp0"
set VERSION=0.2.0
set PYTHONNOUSERSITE=1
if not exist ".build-temp" mkdir ".build-temp"
set TEMP=%CD%\.build-temp
set TMP=%CD%\.build-temp
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv || exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements.txt || exit /b 1
.venv\Scripts\python.exe -m pytest -q --basetemp ".build-temp\pytest-%RANDOM%-%RANDOM%" || exit /b 1
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name ZeroHourHotkeyEditor --icon "assets\app_icon.ico" --version-file "assets\version_info.txt" --hidden-import PIL.TgaImagePlugin --add-data "data\overrides;data\overrides" --add-data "assets\app_icon.png;assets" main.py || exit /b 1
if not exist "release" mkdir "release"
tar.exe -a -c -f "release\ZeroHourHotkeyEditor-v%VERSION%-Windows.zip" -C "dist\ZeroHourHotkeyEditor" . || exit /b 1
echo.
echo Build ready: dist\ZeroHourHotkeyEditor\ZeroHourHotkeyEditor.exe
echo Release ready: release\ZeroHourHotkeyEditor-v%VERSION%-Windows.zip
endlocal
