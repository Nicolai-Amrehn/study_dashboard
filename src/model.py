from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional, Protocol


class Pruefungsform(Enum):
    KLAUSUR = "Klausur"
    HAUSARBEIT = "Hausarbeit"


class ModulStatus(Enum):
    BESTANDEN = "Bestanden"
    NICHT_BESTANDEN = "Nicht bestanden"
    ANGEMELDET = "Angemeldet"

class Abschluss(Enum):
    BSC = "Bachelor of Science"
    MSC = "Master of Science"

class ZielStatus(Enum):
    ERREICHT = "Erreicht"
    NICHT_ERREICHT = "Nicht erreicht"
    IN_ARBEIT = "In Arbeit"

@dataclass(frozen=True)
class ZielBewertung:
    ziel_id: int
    status: ZielStatus


@dataclass(frozen=True)
class Studienziel(ABC):
    """
    Abstrakte Basisklasse für alle Studienziele.
    """
    id: int

    @property
    @abstractmethod
    def beschreibung(self) -> str:
        """Eine für Menschen lesbare Beschreibung des Ziels."""
        ...

    @abstractmethod
    def werte_status_aus(self, student: Student) -> ZielStatus:
        """Wertet den Status des Ziels basierend auf den Studentendaten aus."""
        ...

@dataclass(frozen=True)
class Notenziel(Studienziel):
    """Ein Studienziel, das auf dem Notendurchschnitt basiert."""

    zielnote: float

    @property
    def beschreibung(self) -> str:
        return f"Notenziel (≤ {self.zielnote})"

    def werte_status_aus(self, student: Student) -> ZielStatus:
        bestandene = [l.note for l in student.leistungen if l.status == ModulStatus.BESTANDEN and l.note is not None]
        if not bestandene:
            return ZielStatus.IN_ARBEIT
        durchschnitt = sum(bestandene) / len(bestandene)
        return ZielStatus.ERREICHT if durchschnitt <= self.zielnote else ZielStatus.NICHT_ERREICHT

@dataclass(frozen=True)
class Zeitziel(Studienziel):
    """Ein Studienziel, das auf der Studiendauer basiert."""

    zieldauer_in_jahren: int

    @property
    def beschreibung(self) -> str:
        return f"Abschluss in {self.zieldauer_in_jahren} Jahren"

    def werte_status_aus(self, student: Student) -> ZielStatus:
        jahre_im_studium = (date.today() - student.studienbeginn).days / 365.25
        return ZielStatus.ERREICHT if jahre_im_studium <= self.zieldauer_in_jahren else ZielStatus.NICHT_ERREICHT


@dataclass
class Studiengang:
    id: int
    bezeichnung: str
    gesamtects: int
    abschluss: Abschluss
    module: List[Modul] = field(default_factory=list)

@dataclass
class Modul:
    id: int
    bezeichnung: str
    ects_punkte: int
    semester: int
    pruefungsform: Pruefungsform


@dataclass
class Studienleistung:
    id: int
    modul: Modul
    note: Optional[float]
    status: ModulStatus


@dataclass
class Student:
    id: int
    name: str
    matrikelnummer: int
    studienbeginn: date
    studiengang: Studiengang
    leistungen: List[Studienleistung] = field(default_factory=list)
    ziele: List[Studienziel] = field(default_factory=list)

    def werte_ziele_aus(self) -> List[ZielBewertung]:
        return [ZielBewertung(ziel.id, ziel.werte_status_aus(self)) for ziel in self.ziele]

    def berechne_gesamt_ects(self) -> int:
        return sum(l.modul.ects_punkte for l in self.leistungen if l.status == ModulStatus.BESTANDEN)

    def berechne_notendurchschnitt(self) -> float | None:
        bestandene = [l.note for l in self.leistungen if l.status == ModulStatus.BESTANDEN and l.note is not None]
        if not bestandene:
            return None
        return sum(bestandene) / len(bestandene)

    def berechne_aktuelles_semester(self) -> int:
        return int(sum(l.modul.ects_punkte for l in self.leistungen if l.status == ModulStatus.BESTANDEN)/30)


class StudentRepository(Protocol):
    def save(self, student: Student) -> None: ...

    def find_by_id(self, student_id: int) -> Optional[Student]: ...