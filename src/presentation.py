# dashboard_controller.py
from flask import Blueprint, render_template
from src.service import DashboardService

class DashboardController:
    def create_dashboard_controller(self, service: DashboardService) -> Blueprint:
        """
        Factory-Funktion zur Erstellung des Dashboard-Blueprints.
        """

        dashboard_bp = Blueprint(
            'dashboard',
            __name__,
            template_folder='templates'
        )

        @dashboard_bp.route("/")
        @dashboard_bp.route("/dashboard")
        def dashboard():
            """
            Diese Funktion dient zum Routing des Dashboards.
            """
            student_id = 1
            try:
                student_data = service.get_student_dashboard(student_id)
            except AttributeError:
                return "Student {} not found.".format(student_id)

            return render_template("dashboard.html", student_data=student_data)

        return dashboard_bp