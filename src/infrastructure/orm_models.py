from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Date, ForeignKey, Enum as DbEnum, Table
from src.infrastructure.extensions import db
from src.model import Pruefungsform, ModulStatus, Abschluss


# --- Assoziationstabelle (M:N) für Studiengang <-> Modul ---
# Diese Tabelle wird benötigt, da ein Modul in mehreren Studiengängen vorkommen kann
# und ein Studiengang viele Module hat. Sie hat keine eigene Klasse, da sie keine
# zusätzlichen Attribute außer den Fremdschlüsseln besitzt.
studiengang_modul_table = Table(
    "studiengang_modul",
    db.metadata,
    db.Column("studiengang_id", Integer, ForeignKey("studiengang.id"), primary_key=True),
    db.Column("modul_id", Integer, ForeignKey("modul.id"), primary_key=True),
)


# --- ORM-Modelle ---

class ModulOrm(db.Model):
    """
    Repräsentiert ein einzelnes Modul (z. B. 'Mathematik 1') in der Datenbank.
    Enthält Metadaten wie ECTS, Semesterempfehlung und Prüfungsform.
    """
    __tablename__ = "modul"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bezeichnung: Mapped[str] = mapped_column(String(200))
    ects_punkte: Mapped[int] = mapped_column(Integer)
    semester: Mapped[int] = mapped_column(Integer)
    pruefungsform: Mapped[Pruefungsform] = mapped_column(DbEnum(Pruefungsform))


class StudiengangOrm(db.Model):
    """
    Repräsentiert einen Studiengang (z. B. 'Informatik B.Sc.').
    Über die 'module'-Relationship (Many-to-Many) weiß der Studiengang,
    welche Kurse belegt werden müssen.
    """
    __tablename__ = "studiengang"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bezeichnung: Mapped[str] = mapped_column(String(200))
    gesamtects: Mapped[int] = mapped_column(Integer)
    abschluss: Mapped[Abschluss] = mapped_column(DbEnum(Abschluss))

    module: Mapped[List[ModulOrm]] = relationship(
        secondary=studiengang_modul_table, backref="studiengaenge"
    )


class StudienleistungOrm(db.Model):
    """
    Verknüpfungstabelle zwischen Student und Modul mit Zusatzdaten (Payload).
    Hier wird gespeichert, welche Note ein Student in einem spezifischen Modul
    erzielt hat und wie der Status ist (z. B. ANGEMELDET, BESTANDEN).
    """
    __tablename__ = "studienleistung"
    # autoincrement=False, da wir die IDs aus der Domain-Logik übernehmen
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    note: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[ModulStatus] = mapped_column(DbEnum(ModulStatus))

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"))
    modul_id: Mapped[int] = mapped_column(ForeignKey("modul.id"))

    student: Mapped["StudentOrm"] = relationship(back_populates="leistungen")
    modul: Mapped[ModulOrm] = relationship()


class StudienzielOrm(db.Model):
    """
    Basisklasse für verschiedene Arten von Studienzielen.
    Implementiert 'Joined Table Inheritance':
    - Alle gemeinsamen Felder stehen in dieser Tabelle ('studienziel').
    - Spezifische Felder stehen in den Kind-Tabellen ('notenziel', 'zeitziel').
    SQLAlchemy unterscheidet die Typen automatisch anhand der Spalte 'type'.
    """
    __tablename__ = "studienziel"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"))

    type: Mapped[str] = mapped_column(String(50))

    __mapper_args__ = {
        "polymorphic_identity": "studienziel",
        "polymorphic_on": "type",
    }


class NotenzielOrm(StudienzielOrm):
    """
    Spezifische Ausprägung eines Studienziels für Notendurchschnitte.
    Speichert nur die Zielnote, erbt den Rest von StudienzielOrm.
    """
    __tablename__ = "notenziel"
    id: Mapped[int] = mapped_column(ForeignKey("studienziel.id"), primary_key=True)
    zielnote: Mapped[float] = mapped_column(Float)

    __mapper_args__ = {"polymorphic_identity": "notenziel"}


class ZeitzielOrm(StudienzielOrm):
    """
    Spezifische Ausprägung eines Studienziels für die Studiendauer.
    Speichert die gewünschte Dauer in Jahren.
    """
    __tablename__ = "zeitziel"
    id: Mapped[int] = mapped_column(ForeignKey("studienziel.id"), primary_key=True)
    zieldauer_in_jahren: Mapped[int] = mapped_column(Integer)

    __mapper_args__ = {"polymorphic_identity": "zeitziel"}


class StudentOrm(db.Model):
    """
    Das zentrale Datenbank-Objekt (Aggregate Root) für einen Studenten.
    Enthält die Stammdaten und verweist auf:
    1. Den gewählten Studiengang (One-to-Many).
    2. Die Liste der erbrachten Leistungen (One-to-Many).
    3. Die definierten Ziele (One-to-Many, polymorph).

    'cascade="all, delete-orphan"' sorgt dafür, dass Leistungen und Ziele
    automatisch gelöscht werden, wenn der Student gelöscht wird.
    """
    __tablename__ = "student"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(100))
    matrikelnummer: Mapped[int] = mapped_column(Integer, unique=True)
    studienbeginn: Mapped[date] = mapped_column(Date)

    studiengang_id: Mapped[int] = mapped_column(ForeignKey("studiengang.id"))

    studiengang: Mapped[StudiengangOrm] = relationship()

    leistungen: Mapped[List[StudienleistungOrm]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    ziele: Mapped[List[StudienzielOrm]] = relationship(
        cascade="all, delete-orphan"
    )