@echo off
TITLE Study Dashboard Installer
CLS

echo ========================================================
echo   STUDY DASHBOARD - AUTOMATISCHE INSTALLATION
echo ========================================================
echo.

REM 1. PRÜFEN OB PYTHON INSTALLIERT IST
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Python wurde nicht gefunden!
    echo.
    echo Bitte installieren Sie Python (z.B. aus dem Microsoft Store)
    echo oder fuegen Sie es Ihrem PATH hinzu.
    echo.
    pause
    exit /b
)

echo [OK] Python gefunden.
echo.

REM 2. VIRTUELLE UMGEBUNG (VENV) ERSTELLEN
IF NOT EXIST "venv" (
    echo [INFO] Erstelle virtuelle Umgebung 'venv'...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo [FEHLER] Konnte venv nicht erstellen.
        pause
        exit /b
    )
) ELSE (
    echo [INFO] Virtuelle Umgebung existiert bereits.
)

REM 3. ABHÄNGIGKEITEN INSTALLIEREN
echo [INFO] Installiere Bibliotheken aus requirements.txt...
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul
IF %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Installation der Bibliotheken fehlgeschlagen.
    pause
    exit /b
)
echo [OK] Bibliotheken installiert.

REM 4. ANWENDUNG STARTEN
echo.
echo ========================================================
echo   STARTVORGANG ERFOLGREICH
echo   Die Datenbank wird automatisch neu angelegt.
echo.
echo   Oeffnen Sie im Browser: http://127.0.0.1:5000/dashboard
echo ========================================================
echo.

python app.py

echo.
echo Die Anwendung wurde beendet.
pause