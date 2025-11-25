import os
from flask import Flask
from src.service import DashboardService
from src.presentation import DashboardController
from src.model import StudentRepository
from src.infrastructure.extensions import db
from src.infrastructure.infrastructure import (
    SqlAlchemyStudentRepository,
    seed_database_sqlalchemy,
    StudentOrm
)


def create_app() -> Flask:
    """
    Factory-Funktion zur Erstellung und Konfiguration der Flask-Anwendung.

    Hier passiert das "Wiring" der Anwendung:
    1. Konfiguration der SQLite-Datenbank.
    2. Initialisierung der Datenbank-Verbindung (SQLAlchemy).
    3. Reset und Seeding der Datenbank (nur für Prototyping/Demo-Zwecke).
    4. Manuelle Dependency Injection: Repository -> Service -> Controller.
    5. Registrierung der Blueprints (Routen).
    """
    app = Flask(__name__)
    app.secret_key = "prototypischer_entwicklungsschluessel"

    # Pfad zur SQLite-Datei im aktuellen Verzeichnis bestimmen
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, "student_db.sqlite")

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    print(f"--- DEBUG INFO ---")
    print(f"Datenbank Pfad: {db_path}")
    print(f"--- DEBUG INFO ---")

    # SQLAlchemy mit der App verbinden
    db.init_app(app)

    # Repository-Instanz erstellen (Infrastruktur-Schicht)
    student_repo: StudentRepository = SqlAlchemyStudentRepository(db.session)

    # Datenbank-Setup bei jedem Neustart
    with app.app_context():
        # 1. Alles löschen und neu machen (für Demo-Zwecke)
        print("Lösche alte Tabellen (falls vorhanden)...")
        db.drop_all()

        print("Erstelle Tabellen neu...")
        db.create_all()

        # 2. Seeding durchführen (Testdaten einfügen)
        print("Starte Seeding...")
        seed_database_sqlalchemy(db.session)

        # 3. Explizit committen, damit Daten persistiert werden
        db.session.commit()
        print("Commit durchgeführt.")

        # 4. VERIFIKATION: Prüfen, ob der Test-Student korrekt angelegt wurde
        check_student = db.session.get(StudentOrm, 1)
        if check_student:
            print(f"VERIFIKATION ERFOLGREICH: Student ID 1 ({check_student.name}) ist in der DB.")
        else:
            print("KRITISCHER FEHLER: Seeding lief durch, aber Student 1 ist NICHT in der DB!")

    # Repository wird in den Service injiziert
    dashboard_service = DashboardService(student_repo=student_repo)

    # Service wird in den Controller injiziert
    controller_instance = DashboardController()
    dashboard_bp = controller_instance.create_dashboard_controller(dashboard_service)

    # Controller-Blueprint in der App registrieren
    app.register_blueprint(dashboard_bp)

    return app


if __name__ == "__main__":
    # Startet den Server im Debug-Modus (Hot-Reloading aktiv)
    app = create_app()
    app.run(debug=True)