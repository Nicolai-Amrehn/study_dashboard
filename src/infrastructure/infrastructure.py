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

    def __init__(self, db_session: Session):
        self.session = db_session

    def save(self, student: Student) -> None:
        orm = self.session.get(StudentOrm, student.id)

        if orm is None:
            orm = StudentOrm(id=student.id)
            self.session.add(orm)

        orm.name = student.name
        orm.matrikelnummer = student.matrikelnummer
        orm.studienbeginn = student.studienbeginn
        orm.studiengang_id = student.studiengang.id
        orm.leistungen = [
            self._map_domain_to_orm_leistung(leistung_domain)
            for leistung_domain in student.leistungen
        ]
        orm.ziele = [
            self._map_domain_to_orm_ziel(ziel_domain) for ziel_domain in student.ziele
        ]

        self.session.commit()

    def find_by_id(self, student_id: int) -> Optional[Student]:
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

    def _map_orm_to_domain_modul(self, orm: ModulOrm) -> Modul:
        return Modul(
            id=orm.id,
            bezeichnung=orm.bezeichnung,
            ects_punkte=orm.ects_punkte,
            semester=orm.semester,
            pruefungsform=orm.pruefungsform
        )

    def _map_orm_to_domain_studiengang(self, orm: StudiengangOrm) -> Studiengang:
        return Studiengang(
            id=orm.id,
            bezeichnung=orm.bezeichnung,
            gesamtects=orm.gesamtects,
            abschluss=orm.abschluss,
            module=[self._map_orm_to_domain_modul(m) for m in orm.module]
        )

    def _map_orm_to_domain_leistung(self, orm: StudienleistungOrm) -> Studienleistung:
        return Studienleistung(
            id=orm.id,
            modul=self._map_orm_to_domain_modul(orm.modul),
            note=orm.note,
            status=orm.status
        )

    def _map_orm_to_domain_ziel(self, orm: StudienzielOrm) -> Studienziel:
        if isinstance(orm, NotenzielOrm):
            return Notenziel(id=orm.id, zielnote=orm.zielnote)
        if isinstance(orm, ZeitzielOrm):
            return Zeitziel(id=orm.id, zieldauer_in_jahren=orm.zieldauer_in_jahren)
        raise ValueError(f"Unbekannter Ziel-Typ: {orm.type}")

    def _map_orm_to_domain_student(self, orm: StudentOrm) -> Student:
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
        if isinstance(domain, Notenziel):
            return NotenzielOrm(id=domain.id, zielnote=domain.zielnote)
        if isinstance(domain, Zeitziel):
            return ZeitzielOrm(id=domain.id, zieldauer_in_jahren=domain.zieldauer_in_jahren)
        raise ValueError(f"Unbekannter Ziel-Typ: {type(domain)}")

    def _map_domain_to_orm_leistung(self, domain: Studienleistung) -> StudienleistungOrm:
        return StudienleistungOrm(
            id=domain.id,
            note=domain.note,
            status=domain.status,
            modul_id=domain.modul.id
        )

def seed_database_sqlalchemy(session: Session):
    """
    Befüllt die Datenbank mit Seeding-Daten.
    """

    studiengang_check = session.get(StudiengangOrm, 1)

    if not studiengang_check:

        modul_prog1 = ModulOrm(id=101, bezeichnung="Programmieren 1", ects_punkte=6, semester=1,
                               pruefungsform=Pruefungsform.KLAUSUR)
        modul_mathe1 = ModulOrm(id=102, bezeichnung="Mathematik 1", ects_punkte=8, semester=1,
                                pruefungsform=Pruefungsform.KLAUSUR)
        modul_webdev = ModulOrm(id=201, bezeichnung="Webentwicklung", ects_punkte=6, semester=2,
                                pruefungsform=Pruefungsform.HAUSARBEIT)
        modul_prog2 = ModulOrm(id=202, bezeichnung="Programmierung 2", ects_punkte=6, semester=3,
                               pruefungsform=Pruefungsform.KLAUSUR)
        modul_db = ModulOrm(id=203, bezeichnung="Datenbanken", ects_punkte=6, semester=3,
                            pruefungsform=Pruefungsform.HAUSARBEIT)
        modul_mathe3 = ModulOrm(id=301, bezeichnung="Mathe 3", ects_punkte=8, semester=3,
                                pruefungsform=Pruefungsform.KLAUSUR)

        module_list = [modul_prog1, modul_mathe1, modul_webdev, modul_prog2, modul_db, modul_mathe3]
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
        print("Bereits Seeding-Daten vorhanden.")

    student_check = session.get(StudentOrm, 1)

    if not student_check:

        ziel_note = NotenzielOrm(id=1, zielnote=2.0)
        ziel_zeit = ZeitzielOrm(id=2, zieldauer_in_jahren=3)

        start_datum = date(date.today().year - 1, date.today().month - 2, 1)

        student_max = StudentOrm(
            id=1,
            name="Max Mustermann",
            matrikelnummer=123456,
            studienbeginn=start_datum,
            studiengang_id=1,

            leistungen=[
                StudienleistungOrm(id=1, modul_id=202, note=1.7, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=2, modul_id=203, note=2.0, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=3, modul_id=301, note=None, status=ModulStatus.ANGEMELDET),
                StudienleistungOrm(id=4, modul_id=101, note=2.3, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=5, modul_id=102, note=3.0, status=ModulStatus.BESTANDEN),
                StudienleistungOrm(id=6, modul_id=201, note=1.3, status=ModulStatus.BESTANDEN),
            ],

            ziele=[ziel_note, ziel_zeit]
        )
        session.add(student_max)

    print("Seeding abgeschlossen.")