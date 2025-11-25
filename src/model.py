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
    """Bündelt alle Daten für ein ausgewertetes Ziel."""
    beschreibung: str
    logical_status: str
    display_text: str

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
        durchschnitt = student.berechne_notendurchschnitt()

        # Fall 1: Keine Noten vorhanden
        if durchschnitt is None:
            return ZielStatus.IN_ARBEIT

        # Fall 2: Ziel erreicht
        if durchschnitt <= self.zielnote:
            return ZielStatus.ERREICHT

        # Fall 3: Toleranzbereich (Gelb)
        toleranz = 0.3
        if durchschnitt <= (self.zielnote + toleranz):
            return ZielStatus.IN_ARBEIT

        # Fall 4: Ziel verfehlt (Rot)
        return ZielStatus.NICHT_ERREICHT

@dataclass(frozen=True)
class Zeitziel(Studienziel):
    """Ein Studienziel, das auf der Studiendauer basiert."""

    zieldauer_in_jahren: int

    @property
    def beschreibung(self) -> str:
        return f"Abschluss in {self.zieldauer_in_jahren} Jahren"

    def werte_status_aus(self, student: Student) -> ZielStatus:
        """
        Wertet das Zeitziel basierend auf einem "Soll-Ist"-Vergleich der ECTS aus.
        """

        # 1. Soll-Rate berechnen
        gesamtects = student.studiengang.gesamtects
        if self.zieldauer_in_jahren <= 0:
            return ZielStatus.IN_ARBEIT  # Ziel ungültig

        soll_rate_pro_jahr = gesamtects / self.zieldauer_in_jahren

        # 2. Zeit vergangen berechnen
        tage_im_studium = (date.today() - student.studienbeginn).days
        jahre_im_studium = tage_im_studium / 365.25

        # 3. Soll- vs. Ist-Stand
        soll_ects_stand_heute = soll_rate_pro_jahr * jahre_im_studium
        ist_ects_stand_heute = student.berechne_gesamt_ects()

        # 4. Die "Ampel" definieren
        differenz = ist_ects_stand_heute - soll_ects_stand_heute

        if differenz >= 0:
            # Du bist auf Kurs oder voraus
            return ZielStatus.ERREICHT

        # Du bist im Rückstand. Wie stark?
        # Wir definieren "Gelb" als einen Puffer von 15 ECTS (ca. ein halbes Semester)
        pufferzone_ects = 15

        if abs(differenz) <= pufferzone_ects:
            # Leicht im Rückstand -> Warnung
            return ZielStatus.IN_ARBEIT
        else:
            # Deutlich im Rückstand -> Gefahr
            return ZielStatus.NICHT_ERREICHT

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

    def _berechne_notendurchschnitt_text(self) -> str:
        """Private Helper-Methode: Berechnet den Schnitt als String."""
        durchschnitt = self.berechne_notendurchschnitt()
        return f"{durchschnitt:.1f}" if durchschnitt is not None else "N/A"

    def _format_zeitziel_status(self, ziel: Zeitziel) -> str:
        # 1. Konstanten
        tage_gesamt = ziel.zieldauer_in_jahren * 365.25
        gesamtects = self.studiengang.gesamtects

        # 2. Zeit vergangen
        tage_im_studium = (date.today() - self.studienbeginn).days

        # 3. Berechnung des "Soll-Standes" auf Tage gerechnet
        if tage_gesamt > 0:
            soll_ects = (gesamtects / tage_gesamt) * tage_im_studium
        else:
            soll_ects = 0

        # 4. Ist-Stand
        ist_ects = self.berechne_gesamt_ects()

        # 5. Formatierung für die Anzeige
        return f"Ist: {ist_ects} ECTS | Soll: {int(soll_ects)} ECTS"

    def werte_ziele_aus(self) -> List[ZielBewertung]:
        """
        Wertet alle Ziele aus und gibt eine Liste von "intelligenten"
        ZielBewertung-Objekten zurück.
        """
        view_data_list = []
        for ziel in self.ziele:
            # 1. Logischen Status für die Ampel holen
            logical_status_enum = ziel.werte_status_aus(self)
            logical_status_str = logical_status_enum.value

            # 2. Anzeigetext holen
            display_text = ""

            if isinstance(ziel, Notenziel):
                # Ist vs. Soll anzeigen + 2 Nachkommastellen
                schnitt = self.berechne_notendurchschnitt()
                if schnitt:
                    # Zeige 2 Nachkommastellen (z.B. 1.94)
                    display_text = f"Ist: {schnitt:.2f} | Soll: ≤ {ziel.zielnote}"
                else:
                    display_text = "Noch keine Noten"

            elif isinstance(ziel, Zeitziel):
                display_text = self._format_zeitziel_status(ziel)
            else:
                display_text = logical_status_str

            # 3. Objekt erstellen
            view_data_list.append(ZielBewertung(
                beschreibung=ziel.beschreibung,
                logical_status=logical_status_str,
                display_text=display_text
            ))

        return view_data_list

    def berechne_gesamt_ects(self) -> int:
        return sum(l.modul.ects_punkte for l in self.leistungen if l.status == ModulStatus.BESTANDEN)

    def berechne_notendurchschnitt(self) -> float | None:
        # Berechnet den Notendurchschnitt. Gefiltert nach "Note vorhanden".
        relevante_noten = [
            l.note for l in self.leistungen
            if l.note is not None and l.status in (ModulStatus.BESTANDEN, ModulStatus.NICHT_BESTANDEN)
        ]

        if not relevante_noten:
            return None

        return sum(relevante_noten) / len(relevante_noten)

    def berechne_aktuelles_semester(self) -> int:
        heute = date.today()
        # Berechne die Differenz in Monaten
        jahre_diff = heute.year - self.studienbeginn.year
        monate_diff = heute.month - self.studienbeginn.month

        gesamt_monate = (jahre_diff * 12) + monate_diff

        # Ein Semester dauert 6 Monate.
        # +1, da man im 0. Monat bereits im 1. Semester ist.
        semester = (gesamt_monate // 6) + 1

        return semester

    def note_eintragen(self, leistung_id: int, note: float):
        """
        Trägt eine Note für eine Leistung ein und aktualisiert deren Status.
        """

        # 1. Die richtige Leistung in der Liste finden
        leistung = next((l for l in self.leistungen if l.id == leistung_id), None)

        if leistung is None:
            raise ValueError(f"Studienleistung mit ID {leistung_id} nicht gefunden.")

        if leistung.status != ModulStatus.ANGEMELDET:
            raise ValueError(f"Für diese Leistung wurde bereits eine Note eingetragen.")

        # 2. Die Note validieren und setzen
        if not (1.0 <= note <= 5.0):
            raise ValueError("Note muss zwischen 1,0 und 5,0 liegen.")

        leistung.note = note

        # 3. Geschäftslogik: Status basierend auf der Note aktualisieren
        if 1.0 <= note <= 4.0:
            leistung.status = ModulStatus.BESTANDEN
        else:
            leistung.status = ModulStatus.NICHT_BESTANDEN

class StudentRepository(Protocol):
    """
    Repository für die Datenbankanbindung für den Studenten
    """
    def save(self, student: Student) -> None: ...

    def find_by_id(self, student_id: int) -> Optional[Student]: ...