from flask import Flask
from src.service import DashboardService
from src.presentation import DashboardController
from src.model import StudentRepository
from src.infrastructure.extensions import db
from src.infrastructure.infrastructure import (
    SqlAlchemyStudentRepository,
    seed_database_sqlalchemy
)

def create_app() -> Flask:
    """
    Factory-Funktion zur Erstellung der Flask-App.
    """

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://user:password@localhost:5432/student_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "geheimer-schluessel-fuer-sessions"
    db.init_app(app)

    student_repo: StudentRepository = SqlAlchemyStudentRepository(db.session)

    with app.app_context():
        # Erstellt die Tabellen (nur falls sie nicht existieren)
        db.create_all()

        # Befüllt die DB mit Testdaten
        seed_database_sqlalchemy(db.session)

    dashboard_service = DashboardService(student_repo=student_repo)
    controller_instance = DashboardController()
    dashboard_bp = controller_instance.create_dashboard_controller(dashboard_service)
    app.register_blueprint(dashboard_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)