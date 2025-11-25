from flask import Blueprint, render_template, request, redirect, url_for, flash
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

        @dashboard_bp.route('/')
        def get_dashboard():
            student_data = service.get_student_dashboard(1)

            selected_semester = request.args.get('semester', type=int)

            active_tab = selected_semester
            if active_tab is None:
                active_tab = student_data.get('aktuelles_semester')

            return render_template(
                'dashboard.html',
                student_data=student_data,
                active_tab=active_tab
            )
        
        @dashboard_bp.route('/student/<int:student_id>/leistung/<int:leistung_id>/note_eintragen', methods=['POST'])
        def note_eintragen(student_id, leistung_id):
            try:
                # 1. Daten aus dem Formular holen
                note_str = request.form.get('note')
                if not note_str:
                    flash("Keine Note angegeben.", "danger")
                    return redirect(url_for('dashboard_controller.get_dashboard'))  # Anpassen

                note = float(note_str.replace(',', '.'))  # Komma zu Punkt umwandeln

                # 2. Den Service aufrufen
                service.note_speichern(student_id, leistung_id, note)

                semester = request.form.get('semester')

                flash("Note erfolgreich gespeichert!", "success")

            except ValueError:
                flash("Ungültige Note. Bitte verwenden Sie eine Zahl (z.B. 1,7).", "danger")
            except Exception as e:
                flash(f"Ein Fehler ist aufgetreten: {e}", "danger")

            return redirect(url_for('dashboard.dashboard', semester=semester))

        return dashboard_bp
