from typing import Optional
from datetime import date
from sqlalchemy.orm import joinedload, Session
from src.model import (
    Student, Modul, Studiengang, Studienleistung, StudentRepository,
    Notenziel, Zeitziel, Pruefungsform, ModulStatus, Abschluss, Studienziel
)
from src.infrastructure.orm_models import (
    StudentOrm, StudiengangOrm, StudienleistungOrm, ModulOrm,
    StudienzielOrm, NotenzielOrm, ZeitzielOrm
)


class SqlAlchemyStudentRepository(StudentRepository):
    """
    Implementierung des StudentRepository mittels SQLAlchemy.

    Diese Klasse fungiert als Brücke zwischen der Domain-Logik und der Datenbank.
    Sie kümmert sich um das Mapping von Domain-Objekten zu ORM-Objekten (und umgekehrt)
    und verwaltet die Transaktionen.
    """

    def __init__(self, db_session: Session):
        """
        Initialisiert das Repository mit einer aktiven Datenbank-Session.
        """
        self.session = db_session

    def save(self, student: Student) -> None:
        """
        Speichert oder aktualisiert einen Studenten in der Datenbank.

        Wandelt das übergebene Domain-Objekt 'Student' in ein entsprechendes
        ORM-Objekt um. Existiert der Datensatz bereits, wird er aktualisiert,
        ansonsten wird ein neuer Eintrag angelegt. Auch abhängige Listen
        (Leistungen, Ziele) werden hierbei synchronisiert.
        """
        orm = self.session.get(StudentOrm, student.id)

        if orm is None:
            orm = StudentOrm(id=student.id)
            self.session.add(orm)

        # Mapping der Basisdaten
        orm.name = student.name
        orm.matrikelnummer = student.matrikelnummer
        orm.studienbeginn = student.studienbeginn
        orm.studiengang_id = student.studiengang.id

        # Erneutes Mapping der Listen, um Änderungen (neue Noten/Ziele) zu erfassen
        orm.leistungen = [
            self._map_domain_to_orm_leistung(leistung_domain)
            for leistung_domain in student.leistungen
        ]
        orm.ziele = [
            self._map_domain_to_orm_ziel(ziel_domain) for ziel_domain in student.ziele
        ]

        self.session.commit()

    def find_by_id(self, student_id: int) -> Optional[Student]:
        """
        Sucht einen Studenten anhand der ID.

        Verwendet 'joinedload', um verknüpfte Daten (Studiengang, Module, Leistungen)
        effizient in einer Abfrage zu laden (verhindert N+1 Probleme).
        Gibt None zurück, wenn kein Student gefunden wurde.
        """
        print(f"Suche Student {student_id} in der PostgreSQL-DB.")

        orm = self.session.get(StudentOrm, student_id, options=[
            joinedload(StudentOrm.studiengang).joinedload(StudiengangOrm.module),
            joinedload(StudentOrm.leistungen).joinedload(StudienleistungOrm.modul),
            joinedload(StudentOrm.ziele)
        ])

        if orm is None:
            return None

        return self._map_orm_to_domain_student(orm)

    # --- Mapper-Methoden ---
    # Diese Methoden sind für die interne Umwandlung zwischen der
    # Datenbank-Repräsentation (ORM) und der Business-Logik (Domain) zuständig.

    def _map_orm_to_domain_modul(self, orm: ModulOrm) -> Modul:
        """Konvertiert ein Modul-ORM-Objekt in ein Domain-Modul."""
        return Modul(
            id=orm.id,
            bezeichnung=orm.bezeichnung,
            ects_punkte=orm.ects_punkte,
            semester=orm.semester,
            pruefungsform=orm.pruefungsform
        )

    def _map_orm_to_domain_studiengang(self, orm: StudiengangOrm) -> Studiengang:
        """Konvertiert einen Studiengang (inkl. Modulliste) in die Domain-Struktur."""
        return Studiengang(
            id=orm.id,
            bezeichnung=orm.bezeichnung,
            gesamtects=orm.gesamtects,
            abschluss=orm.abschluss,
            module=[self._map_orm_to_domain_modul(m) for m in orm.module]
        )

    def _map_orm_to_domain_leistung(self, orm: StudienleistungOrm) -> Studienleistung:
        """Konvertiert eine erbrachte Leistung in die Domain-Struktur."""
        return Studienleistung(
            id=orm.id,
            modul=self._map_orm_to_domain_modul(orm.modul),
            note=orm.note,
            status=orm.status
        )

    def _map_orm_to_domain_ziel(self, orm: StudienzielOrm) -> Studienziel:
        """Erkennt den spezifischen Ziel-Typ (Note oder Zeit) und konvertiert entsprechend."""
        if isinstance(orm, NotenzielOrm):
            return Notenziel(id=orm.id, zielnote=orm.zielnote)
        if isinstance(orm, ZeitzielOrm):
            return Zeitziel(id=orm.id, zieldauer_in_jahren=orm.zieldauer_in_jahren)
        raise ValueError(f"Unbekannter Ziel-Typ: {orm.type}")

    def _map_orm_to_domain_student(self, orm: StudentOrm) -> Student:
        """Baut das komplette Student-Domain-Objekt aus den ORM-Daten zusammen."""
        return Student(
            id=orm.id,
            name=orm.name,
            matrikelnummer=orm.matrikelnummer,
            studienbeginn=orm.studienbeginn,
            studiengang=self._map_orm_to_domain_studiengang(orm.studiengang),
            leistungen=[self._map_orm_to_domain_leistung(l) for l in orm.leistungen],
            ziele=[self._map_orm_to_domain_ziel(z) for z in orm.ziele]
        )

    def _map_domain_to_orm_ziel(self, domain: Studienziel) -> StudienzielOrm:
        """Konvertiert ein Domain-Ziel (Note/Zeit) in das entsprechende ORM-Objekt."""
        if isinstance(domain, Notenziel):
            return NotenzielOrm(id=domain.id, zielnote=domain.zielnote)
        if isinstance(domain, Zeitziel):
            return ZeitzielOrm(id=domain.id, zieldauer_in_jahren=domain.zieldauer_in_jahren)
        raise ValueError(f"Unbekannter Ziel-Typ: {type(domain)}")

    def _map_domain_to_orm_leistung(self, domain: Studienleistung) -> StudienleistungOrm:
        """Konvertiert eine Domain-Leistung in ein ORM-Objekt für die Speicherung."""
        return StudienleistungOrm(
            id=domain.id,
            note=domain.note,
            status=domain.status,
            modul_id=domain.modul.id
        )

def seed_database_sqlalchemy(session: Session):
    """
    Initialisiert die Datenbank mit Beispieldaten für Entwicklungszwecke.

    Erstellt (falls nicht vorhanden):
    1. Einen Informatik-Studiengang mit Modulen über 3 Semester.
    2. Einen Beispiel-Studenten 'Max Mustermann' mit:
       - Bestandenen Leistungen aus Sem 1 & 2.
       - Angemeldeten Leistungen im 3. Semester.
       - Zielen (Notenziel und Zeitziel).
    """

    # Prüfen, ob Studiengang existiert
    studiengang_check = session.get(StudiengangOrm, 1)

    if not studiengang_check:
        print("Erstelle Module und Studiengang...")

        # --- 1. Semester (6 Kurse) ---
        m101 = ModulOrm(id=101, bezeichnung="Programmieren 1", ects_punkte=5, semester=1, pruefungsform=Pruefungsform.KLAUSUR)
        m102 = ModulOrm(id=102, bezeichnung="Mathematik 1 (Analysis)", ects_punkte=5, semester=1, pruefungsform=Pruefungsform.KLAUSUR)
        m103 = ModulOrm(id=103, bezeichnung="Technische Informatik", ects_punkte=5, semester=1, pruefungsform=Pruefungsform.KLAUSUR)
        m104 = ModulOrm(id=104, bezeichnung="Theoretische Informatik 1", ects_punkte=5, semester=1, pruefungsform=Pruefungsform.KLAUSUR)
        m105 = ModulOrm(id=105, bezeichnung="Einführung in die Informatik", ects_punkte=5, semester=1, pruefungsform=Pruefungsform.HAUSARBEIT)
        m106 = ModulOrm(id=106, bezeichnung="Soft Skills & Englisch", ects_punkte=5, semester=1, pruefungsform=Pruefungsform.HAUSARBEIT)

        # --- 2. Semester (6 Kurse) ---
        m201 = ModulOrm(id=201, bezeichnung="Programmieren 2", ects_punkte=5, semester=2, pruefungsform=Pruefungsform.KLAUSUR)
        m202 = ModulOrm(id=202, bezeichnung="Mathematik 2 (Lineare Algebra)", ects_punkte=5, semester=2, pruefungsform=Pruefungsform.KLAUSUR)
        m203 = ModulOrm(id=203, bezeichnung="Algorithmen & Datenstrukturen", ects_punkte=5, semester=2, pruefungsform=Pruefungsform.KLAUSUR)
        m204 = ModulOrm(id=204, bezeichnung="Betriebssysteme", ects_punkte=5, semester=2, pruefungsform=Pruefungsform.KLAUSUR)
        m205 = ModulOrm(id=205, bezeichnung="Rechnernetze", ects_punkte=5, semester=2, pruefungsform=Pruefungsform.KLAUSUR)
        m206 = ModulOrm(id=206, bezeichnung="Statistik & Wahrscheinlichkeit", ects_punkte=5, semester=2, pruefungsform=Pruefungsform.KLAUSUR)

        # --- 3. Semester (4 Kurse) ---
        m301 = ModulOrm(id=301, bezeichnung="Datenbanken", ects_punkte=5, semester=3, pruefungsform=Pruefungsform.KLAUSUR)
        m302 = ModulOrm(id=302, bezeichnung="Software Engineering", ects_punkte=5, semester=3, pruefungsform=Pruefungsform.HAUSARBEIT)
        m303 = ModulOrm(id=303, bezeichnung="Webentwicklung", ects_punkte=5, semester=3, pruefungsform=Pruefungsform.HAUSARBEIT)
        m304 = ModulOrm(id=304, bezeichnung="Mathematik 3 (Numerik)", ects_punkte=5, semester=3, pruefungsform=Pruefungsform.KLAUSUR)

        module_list = [
            m101, m102, m103, m104, m105, m106,
            m201, m202, m203, m204, m205, m206,
            m301, m302, m303, m304
        ]
        session.add_all(module_list)

        studiengang_info = StudiengangOrm(
            id=1,
            bezeichnung="Informatik",
            abschluss=Abschluss.BSC,
            gesamtects=180,
            module=module_list
        )
        session.add(studiengang_info)
    else:
        print("Bereits Seeding-Daten für Studiengang vorhanden.")

    # Prüfen, ob Student existiert
    student_check = session.get(StudentOrm, 1)

    if not student_check:
        print("Erstelle Student Max Mustermann...")

        ziel_note = NotenzielOrm(id=1, zielnote=1.9)
        ziel_zeit = ZeitzielOrm(id=2, zieldauer_in_jahren=3)

        # Studienbeginn vor ca. 1 Jahr (damit er jetzt im 3. Sem ist)
        start_datum = date(date.today().year - 1, 10, 1)

        student_max = StudentOrm(
            id=1,
            name="Max Mustermann",
            matrikelnummer=123456,
            studienbeginn=start_datum,
            studiengang_id=1,

            leistungen=[
                # --- 1. Semester ---
                StudienleistungOrm(id=1, modul_id=101, note=1.3, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=2, modul_id=102, note=2.7, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=3, modul_id=103, note=2.0, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=4, modul_id=104, note=3.3, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=5, modul_id=105, note=1.0, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=6, modul_id=106, note=1.7, status=ModulStatus.BESTANDEN),

                # --- 2. Semester ---
                StudienleistungOrm(id=7, modul_id=201, note=1.7, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=8, modul_id=202, note=3.0, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=9, modul_id=203, note=2.3, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=10, modul_id=204, note=2.0, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=11, modul_id=205, note=1.3, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=12, modul_id=206, note=2.7, status=ModulStatus.BESTANDEN),

                # --- 3. Semester ---
                StudienleistungOrm(id=13, modul_id=301, note=None, status=ModulStatus.ANGEMELDET),
                StudienleistungOrm(id=14, modul_id=302, note=None, status=ModulStatus.ANGEMELDET),
                StudienleistungOrm(id=15, modul_id=303, note=None, status=ModulStatus.ANGEMELDET),
                StudienleistungOrm(id=16, modul_id=304, note=None, status=ModulStatus.ANGEMELDET),
            ],

            ziele=[ziel_note, ziel_zeit]
        )
        session.add(student_max)

    print("Seeding abgeschlossen.")