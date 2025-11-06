from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Date, ForeignKey, Enum as DbEnum, Table
from src.infrastructure.extensions import db
from src.model import Pruefungsform, ModulStatus, Abschluss


# --- Assoziationstabelle (M:N) für Studiengang <-> Modul ---
studiengang_modul_table = Table(
    "studiengang_modul",
    db.metadata,
    db.Column("studiengang_id", Integer, ForeignKey("studiengang.id"), primary_key=True),
    db.Column("modul_id", Integer, ForeignKey("modul.id"), primary_key=True),
)


# --- ORM-Modelle ---

class ModulOrm(db.Model):
    __tablename__ = "modul"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bezeichnung: Mapped[str] = mapped_column(String(200))
    ects_punkte: Mapped[int] = mapped_column(Integer)
    semester: Mapped[int] = mapped_column(Integer)
    pruefungsform: Mapped[Pruefungsform] = mapped_column(DbEnum(Pruefungsform))


class StudiengangOrm(db.Model):
    __tablename__ = "studiengang"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bezeichnung: Mapped[str] = mapped_column(String(200))
    gesamtects: Mapped[int] = mapped_column(Integer)
    abschluss: Mapped[Abschluss] = mapped_column(DbEnum(Abschluss))

    module: Mapped[List[ModulOrm]] = relationship(
        secondary=studiengang_modul_table, backref="studiengaenge"
    )


class StudienleistungOrm(db.Model):
    __tablename__ = "studienleistung"
    id: Mapped[int] = mapped_column(Integer, primary_key=True,
                                    autoincrement=False)
    note: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[ModulStatus] = mapped_column(DbEnum(ModulStatus))

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"))
    modul_id: Mapped[int] = mapped_column(ForeignKey("modul.id"))

    student: Mapped["StudentOrm"] = relationship(back_populates="leistungen")
    modul: Mapped[ModulOrm] = relationship()


class StudienzielOrm(db.Model):
    """ Abstrakte Basisklasse für die Persistenz von Zielen """
    __tablename__ = "studienziel"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)  # IDs aus Domain-Modell
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"))

    type: Mapped[str] = mapped_column(String(50))

    __mapper_args__ = {
        "polymorphic_identity": "studienziel",
        "polymorphic_on": "type",
    }


class NotenzielOrm(StudienzielOrm):
    __tablename__ = "notenziel"
    id: Mapped[int] = mapped_column(ForeignKey("studienziel.id"), primary_key=True)
    zielnote: Mapped[float] = mapped_column(Float)

    __mapper_args__ = {"polymorphic_identity": "notenziel"}


class ZeitzielOrm(StudienzielOrm):
    __tablename__ = "zeitziel"
    id: Mapped[int] = mapped_column(ForeignKey("studienziel.id"), primary_key=True)
    zieldauer_in_jahren: Mapped[int] = mapped_column(Integer)

    __mapper_args__ = {"polymorphic_identity": "zeitziel"}


class StudentOrm(db.Model):
    """ das Aggregate Root """
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