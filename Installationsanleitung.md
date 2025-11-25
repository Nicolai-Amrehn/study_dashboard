# Installationsanleitung
### Voraussetzungen:
- Python installiert und im PATH.

### Schritte automatisches Setup Windows:
1. start_project.bat öffnen

2. Browser öffnen unter: http://127.0.0.1:5000/dashboard

### Schritte manuelles Setup Windows:

1. Eingabeaufforderung (CMD) oder PowerShell öffnen und in den Projektordner wechseln:
   cd pfad\zu\nicolai-amrehn-study_dashboard

2. Eine virtuelle Umgebung erstellen, um Systemkonflikte zu vermeiden:
   python -m venv venv

3. Umgebung aktivieren
   Windows CMD:        venv\Scripts\activate
   Windows PowerShell: .\venv\Scripts\Activate

4. Notwendige Pakete installieren:
   pip install -r requirements.txt

5. Anwendung starten:
   python app.py

6. Browser öffnen unter: http://127.0.0.1:5000/dashboard