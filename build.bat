@echo off
title APC Mini EXE Builder

echo ==========================================
echo APC Mini Mk1 Tester - EXE Builder
echo ==========================================
echo.

python --version
if errorlevel 1 (
    echo Python wurde nicht gefunden.
    pause
    exit /b
)

echo.
echo Installiere/aktualisiere Abhaengigkeiten...
python -m pip install --upgrade pip
python -m pip install pyinstaller mido python-rtmidi

echo.
echo Alte Build-Dateien entfernen...

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Erzeuge EXE...

pyinstaller ^
 --onefile ^
 --windowed ^
 --name APCMiniTester ^
 --hidden-import=mido.backends.rtmidi ^
 --hidden-import=rtmidi ^
 apc_mini_tester.py

echo.
echo ==========================================
echo Fertig
echo ==========================================
echo.

if exist dist\APCMiniTester.exe (
    echo EXE erfolgreich erstellt:
    echo.
    echo dist\APCMiniTester.exe
    echo.
) else (
    echo Fehler beim Erstellen der EXE.
)

pause