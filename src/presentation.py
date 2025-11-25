from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.service import DashboardService


class DashboardController:
    """
    Controller-Klasse für das Dashboard.

    Dient als Factory für den Blueprint und ermöglicht die Injektion
    des DashboardServices, damit die Routen auf die Geschäftslogik zugreifen können.
    """

    def create_dashboard_controller(self, service: DashboardService) -> Blueprint:
        """
        Factory-Funktion zur Erstellung des Dashboard-Blueprints.

        Definiert die URL-Routen für das Dashboard und verknüpft sie mit
        der Logik aus dem DashboardService.
        """

        dashboard_bp = Blueprint(
            'dashboard',
            __name__,
            template_folder='templates'
        )

        @dashboard_bp.route('/')
        def get_dashboard():
            """
            Lädt die Hauptansicht des Dashboards (GET).

            Holt die aufbereiteten Daten für den Studenten (hier ID 1) vom Service
            und entscheidet, welcher Semester-Tab initial geöffnet sein soll
            (entweder über URL-Parameter oder basierend auf dem aktuellen Semester).
            """
            student_data = service.get_student_dashboard(1)

            # Prüfen, ob ein spezifisches Semester über die URL angefragt wurde (?semester=X)
            selected_semester = request.args.get('semester', type=int)

            active_tab = selected_semester
            if active_tab is None:
                # Fallback: Aktuelles Semester öffnen, wenn nichts ausgewählt wurde
                active_tab = student_data.get('aktuelles_semester')

            return render_template(
                'dashboard.html',
                student_data=student_data,
                active_tab=active_tab
            )

        @dashboard_bp.route('/student/<int:student_id>/leistung/<int:leistung_id>/note_eintragen', methods=['POST'])
        def note_eintragen(student_id, leistung_id):
            """
            Verarbeitet das Formular zum Eintragen einer Note (POST).

            Führt eine Eingabevalidierung durch (z.B. Umwandlung von Komma zu Punkt),
            ruft die Geschäftslogik 'note_speichern' auf und gibt Feedback per Flash-Message.
            Leitet anschließend zurück zum Dashboard.
            """
            semester = request.form.get('semester')

            try:
                # 1. Daten aus dem Formular holen
                note_str = request.form.get('note')
                if not note_str:
                    flash("Keine Note angegeben.", "danger")
                    # Korrektur: Der Blueprint-Name ist 'dashboard', daher 'dashboard.get_dashboard'
                    return redirect(url_for('dashboard.get_dashboard'))

                # Komma (deutsch) zu Punkt (technisch) umwandeln für Float
                note = float(note_str.replace(',', '.'))

                # 2. Den Service aufrufen, um Status und Note zu aktualisieren
                service.note_speichern(student_id, leistung_id, note)

                semester = request.form.get('semester')

                flash("Note erfolgreich gespeichert!", "success")

            except ValueError:
                # Fängt Fehler ab, wenn der String nicht in eine Zahl wandelbar ist
                flash("Ungültige Note. Bitte verwenden Sie eine Zahl (z.B. 1,7).", "danger")
            except Exception as e:
                # Allgemeiner Fehler-Handler
                flash(f"Ein Fehler ist aufgetreten: {e}", "danger")

            # Redirect zurück zum Dashboard, wobei der aktive Tab (Semester) erhalten bleibt
            return redirect(url_for('dashboard.get_dashboard', semester=semester))

        return dashboard_bp