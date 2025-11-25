from src.model import (
    StudentRepository,
    ModulStatus
)

class DashboardService:
    """Implementiert den Use Case 'Studenten-Dashboard anzeigen'."""

    def __init__(self, student_repo: StudentRepository):
        self.repo = student_repo

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
        ziele_view_data = student.werte_ziele_aus()

        view_ziele = [
            {
                "beschreibung": z.beschreibung,
                "logical_status": z.logical_status,
                "display_text": z.display_text
            }
            for z in ziele_view_data
        ]
        # Semesterübersicht
        semester_daten_map = {i: [] for i in range(1, 7)}

        # Füllt die Map mit allen Leistungen
        for leistung in student.leistungen:
            sem = leistung.modul.semester
            if sem in semester_daten_map:
                semester_daten_map[sem].append({
                    "id": leistung.id,
                    "modul": leistung.modul.bezeichnung,
                    "form": leistung.modul.pruefungsform.value,
                    "note": leistung.note,
                    "status": leistung.status.value
                })

        # Finales View Model
        student_view_data = {
            "id": student.id,
            "name": student.name,
            "matrikelnummer": student.matrikelnummer,
            "studiengang": f"{student.studiengang.bezeichnung} ({student.studiengang.abschluss.value})",
            "studienbeginn": student.studienbeginn.strftime("%d.%m.%Y"),
            "aktuelles_semester": aktuelles_semester,
            "ziele": view_ziele,
            "semester_data": semester_daten_map,
            "fortschritt": {
                "aktuell_ects": erreichte_ects,
                "gesamt_ects": gesamt_ects,
                "prozent": fortschritt_prozent
            }
        }

        return student_view_data

    def note_speichern(self, student_id: int, leistung_id: int, note: float):
        """
        Trägt eine Note für eine spezifische Studienleistung ein.
        """
        student = self.repo.find_by_id(student_id)

        try:
            student.note_eintragen(leistung_id, note)
        except ValueError as e:
            raise e

        self.repo.save(student)