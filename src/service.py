from src.model import (
    StudentRepository,
    ModulStatus
)


class DashboardService:
    """
    Service-Layer für das Dashboard.

    Diese Klasse implementiert den Anwendungsfall (Use Case) 'Studenten-Dashboard anzeigen'.
    Sie dient als Bindeglied zwischen dem Controller (Web) und der Domain (Model).
    Ihre Hauptaufgabe ist die Orchestrierung von Datenabruf, Aufbereitung für die View
    und das Anstoßen von Änderungen.
    """

    def __init__(self, student_repo: StudentRepository):
        """Initialisiert den Service mit dem notwendigen Repository."""
        self.repo = student_repo

    def get_student_dashboard(self, student_id: int) -> dict:
        """
        Holt alle notwendigen Daten für einen Studenten und transformiert sie
        in ein View Model (Dictionary), das direkt vom Frontend (HTML-Template)
        verwendet werden kann.

        Schritte:
        1. Laden des Studenten-Aggregats aus der Datenbank.
        2. Berechnung von aggregierten Werten (ECTS-Summe, Fortschritt in %).
        3. Aufbereitung der Studienziele für die Anzeige (Ampelsystem).
        4. Gruppierung der Leistungen nach Semestern für die Tab-Ansicht.
        """

        student = self.repo.find_by_id(student_id)

        # Aggregierte Daten berechnen
        erreichte_ects = student.berechne_gesamt_ects()
        gesamt_ects = student.studiengang.gesamtects
        aktuelles_semester = student.berechne_aktuelles_semester()

        fortschritt_prozent = 0
        if gesamt_ects > 0:
            fortschritt_prozent = round((erreichte_ects / gesamt_ects) * 100)

        # Ziele für die View aufbereiten (Domain-Objekte -> View-Daten)
        ziele_view_data = student.werte_ziele_aus()

        view_ziele = [
            {
                "beschreibung": z.beschreibung,
                "logical_status": z.logical_status,
                "display_text": z.display_text
            }
            for z in ziele_view_data
        ]

        # Semesterübersicht initialisieren (Semester 1 bis 6)
        semester_daten_map = {i: [] for i in range(1, 7)}

        # Leistungen den entsprechenden Semestern zuordnen
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

        # Finales View Model zusammenstellen
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
        Orchestriert den Prozess der Noteneintragung.

        Ablauf:
        1. Lädt das Student-Aggregat.
        2. Führt die Geschäftslogik am Domain-Objekt aus (Validierung & Statusänderung).
        3. Persistiert den geänderten Zustand in der Datenbank.
        """
        student = self.repo.find_by_id(student_id)

        try:
            student.note_eintragen(leistung_id, note)
        except ValueError as e:
            # Reicht Domain-Fehler (z.B. ungültige Note) an den Controller weiter
            raise e

        self.repo.save(student)