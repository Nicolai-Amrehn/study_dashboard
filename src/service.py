# application_services.py
from datetime import date
from src.model import (
    Student, StudentRepository,
    Notenziel, Zeitziel, ModulStatus
)

class DashboardService:
    """Implementiert den Use Case 'Studenten-Dashboard anzeigen'."""

    def __init__(self, student_repo: StudentRepository):
        self.repo = student_repo

    def _berechne_notendurchschnitt_text(self, student: Student) -> str:
        durchschnitt = student.berechne_notendurchschnitt()
        return f"{durchschnitt:.1f}" if durchschnitt is not None else "N/A"

    def _format_zeitziel_status(self, student: Student, ziel: Zeitziel) -> str:
        tage_im_studium = (date.today() - student.studienbeginn).days
        tage_gesamt = ziel.zieldauer_in_jahren * 365.25
        tage_verbleibend = tage_gesamt - tage_im_studium

        prozent_verbraucht = (tage_im_studium / tage_gesamt) * 100
        monate_verbleibend = tage_verbleibend / 30.44

        return f"{100 - prozent_verbraucht:.0f}% verbleibend ({monate_verbleibend:.0f} Monate)"

    def get_student_dashboard(self, student_id: int) -> dict:
        """Holt einen Studenten und transformiert ihn in ein View Model (dict)."""

        student = self.repo.find_by_id(student_id)
        erreichte_ects = student.berechne_gesamt_ects()
        gesamt_ects = student.studiengang.gesamtects
        aktuelles_semester = student.berechne_aktuelles_semester()

        fortschritt_prozent = 0
        if gesamt_ects > 0:
            fortschritt_prozent = round((erreichte_ects / gesamt_ects) * 100)

        # Ziele für die View aufbereiten
        view_ziele = []
        for ziel in student.ziele:

            if isinstance(ziel, Notenziel):
                status_text = f"Aktuell {self._berechne_notendurchschnitt_text(student)}"
            elif isinstance(ziel, Zeitziel):
                status_text = self._format_zeitziel_status(student, ziel)

            view_ziele.append({
                "beschreibung": ziel.beschreibung,
                "status": status_text
            })

        # Semesterübersicht (nur aktuelles Semester)
        view_semester_uebersicht = []
        for leistung in student.leistungen:
            if leistung.modul.semester == aktuelles_semester:
                view_semester_uebersicht.append({
                    "modul": leistung.modul.bezeichnung,
                    "form": leistung.modul.pruefungsform.value,
                    "note": leistung.note,
                    "status": "bestanden" if leistung.status == ModulStatus.BESTANDEN else "ausstehend"
                })

        # Finales View Model
        student_view_data = {
            "name": student.name,
            "matrikelnummer": student.matrikelnummer,
            "studiengang": f"{student.studiengang.bezeichnung} ({student.studiengang.abschluss.value})",
            "studienbeginn": student.studienbeginn.strftime("%d.%m.%Y"),
            "aktuelles_semester": aktuelles_semester,
            "ziele": view_ziele,
            "semester_uebersicht": view_semester_uebersicht,
            "fortschritt": {
                "aktuell_ects": erreichte_ects,
                "gesamt_ects": gesamt_ects,
                "prozent": fortschritt_prozent
            }
        }

        return student_view_data