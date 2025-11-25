import os
import sys
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
    Factory-Funktion zur Erstellung der Flask-App.
    """
    app = Flask(__name__)

    # 1. Absoluten Pfad zur DB-Datei erzwingen
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, "student_db.sqlite")

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    print(f"--- DEBUG INFO ---")
    print(f"Datenbank Pfad: {db_path}")
    print(f"--- DEBUG INFO ---")

    db.init_app(app)

    student_repo: StudentRepository = SqlAlchemyStudentRepository(db.session)

    with app.app_context():
        # 2. Brutale Methode: Alles löschen und neu machen (Sicherer für Demos)
        print("Lösche alte Tabellen (falls vorhanden)...")
        db.drop_all()

        print("Erstelle Tabellen neu...")
        db.create_all()

        # 3. Seeding durchführen
        print("Starte Seeding...")
        seed_database_sqlalchemy(db.session)

        # 4. Explizit committen!
        db.session.commit()
        print("Commit durchgeführt.")

        # 5. VERIFIKATION: Prüfen, ob Max wirklich da ist
        check_student = db.session.get(StudentOrm, 1)
        if check_student:
            print(f"VERIFIKATION ERFOLGREICH: Student ID 1 ({check_student.name}) ist in der DB.")
        else:
            print("KRITISCHER FEHLER: Seeding lief durch, aber Student 1 ist NICHT in der DB!")

    dashboard_service = DashboardService(student_repo=student_repo)
    controller_instance = DashboardController()
    dashboard_bp = controller_instance.create_dashboard_controller(dashboard_service)
    app.register_blueprint(dashboard_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)