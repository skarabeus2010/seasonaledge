"""Ereigniskatalog der Börsenschließungen (Vertrag B4, docs/KALENDER_UMSTELLUNG.md V1c-1;
Entwurf docs/review_prompts/2026-10-11_kalender_v1c_entwurf*.md, freigegeben in v4).

Die EINE Quelle der Schließungsregeln: `shared/exchange_holidays.py` und `shared/nyse_holidays.py` leiten ihre
Feiertagsmengen (`get_holidays`, `is_holiday`, `_compute_*_holidays`) über `kompat()` hieraus ab.

Ein Ereignis je Regeltermin:
  nominal    Regeltermin (z. B. 25.12., 3. Montag im Juli)
  rechtlich  der gesetzlich bestimmte Tag des Feiertags in diesem Jahr (≠ nominal nur bei Verlegung)
  wirksam    Schließungstag
  ersatzgrund keiner | wochenende (LSE/NYSE) | furikae (TSE) | verlegung (Sondergesetz/Proklamation)
  verlegt    True, wenn der rechtliche Tag ein verlegter Termin ist (auch bei anschließendem Furikae)
  art        feiertag (wirksam == nominal) | ersatztag (wirksam ≠ nominal) | sonderschliessung | unbestimmt
             (Tabelleneintrag ohne Regel) — `halbtag` folgt in V1c-3
  nominal_herkunft regel | tabelle (Tabellen-Datum ist eine technische Konvention, KEIN Beleg des Feiertags)
ereignis_id = "<boerse>:<regel_id>:<nominal ISO>"  (Tabelle: "<boerse>:tabelle:<Datum>")

Projektionen:
  kompat(b, j)        die bisherige Feiertagsmenge (inkl. Wochenenddaten) — Bestandsschutz gegen
                      scripts/fixtures/kalender_vor_v1c.json; TSE behält bei Furikae den rechtlichen Sonntag.
  schliessungen(b, j) eindeutige wirksame Vollschließungen auf sonst offenen Tagen (Mo–Fr).
Versionen: `ereignisversion()` über die aufgelösten Inhalte (jede Inhaltsänderung), `kalenderversion()` über die
Schließungsprojektion (ändert sich genau dann, wenn sie sich ändert).
"""
from __future__ import annotations

import functools
import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta

from shared.exchange_holidays import (
    _HKEX_HOLIDAYS,
    _KRX_HOLIDAYS,
    _TSE_BOERSE_GESCHLOSSEN,
    _TSE_EINMALIG_FEIERTAG,
    _TSE_OLYMPIA,
    XETRA_SONDER,
    _ascension_day,
    _easter_monday,
    _whit_monday,
)
from shared.nyse_holidays import (
    _NYSE_SPECIAL_CLOSURES,
    _good_friday,
    _monday_if_sunday,
    _nth_weekday,
    _observed,
)

ARTEN = ("feiertag", "ersatztag", "sonderschliessung", "unbestimmt", "halbtag")
ERSATZGRUENDE = ("keiner", "wochenende", "furikae", "verlegung")
NOMINAL_BLEIBT = frozenset({"TSE"})       # nur dort enthält die bisherige Menge den rechtlichen Sonntag (Furikae)
ALIAS = {"NASDAQ": "NYSE"}


@dataclass(frozen=True)
class Ereignis:
    boerse: str
    regel_id: str
    art: str
    nominal: date
    rechtlich: date
    wirksam: date
    ersatzgrund: str
    verlegt: bool
    nominal_herkunft: str
    name_de: str | None
    name_en: str | None
    quelle: str
    # V1c-3 Halbtage: nur bei art == 'halbtag' gesetzt, sonst None (Bedeutung: shared/halbtage_belege.py)
    schlusszeit: str | None = None
    zeitzone: str | None = None
    sitzung: str | None = None

    @property
    def ereignis_id(self) -> str:
        if self.nominal_herkunft == "tabelle":
            return "%s:tabelle:%s" % (self.boerse, self.nominal.isoformat())
        return "%s:%s:%s" % (self.boerse, self.regel_id, self.nominal.isoformat())

    def als_dict(self) -> dict:
        """Vollständiges Objekt wie in der JS-API: Inhalt + `kalenderversion` (Hash der Schließungsprojektion des
        gesamten Katalogs, B4.1). Die Version ist NICHT Teil von `inhalt()` und damit nicht der `ereignisversion`."""
        return dict(self.inhalt(), kalenderversion=_kalenderversion_gesamt())

    def inhalt(self) -> dict:
        """Aufgelöster Inhalt ohne Versionsfelder — Grundlage der `ereignisversion`."""
        from shared.kalender_quellen import QUELLEN
        q = QUELLEN[self.quelle]
        return {
            "ereignis_id": self.ereignis_id, "boerse": self.boerse, "regel_id": self.regel_id, "art": self.art,
            "nominal": self.nominal.isoformat(), "rechtlich": self.rechtlich.isoformat(),
            "wirksam": self.wirksam.isoformat(), "ersatzgrund": self.ersatzgrund, "verlegt": self.verlegt,
            "nominal_herkunft": self.nominal_herkunft, "name_de": self.name_de, "name_en": self.name_en,
            "quelle": self.quelle, "quelle_titel": q[0], "quelle_beleg": q[1], "quelle_stand": q[2],
            "schlusszeit": self.schlusszeit, "zeitzone": self.zeitzone, "sitzung": self.sitzung,
        }


def _e(b, rid, nominal, de, en, q, wirksam=None, rechtlich=None, grund="keiner", verlegt=False, art=None):
    rechtlich = rechtlich or nominal
    wirksam = wirksam or rechtlich
    if art is None:
        art = "feiertag" if wirksam == nominal else "ersatztag"
    return Ereignis(b, rid, art, nominal, rechtlich, wirksam, grund, verlegt, "regel", de, en, q)


def _sonder(b, d, kurz, de, en, q):
    return Ereignis(b, "%s.sonder.%s_%s" % (b, d.isoformat(), kurz), "sonderschliessung", d, d, d, "keiner",
                    False, "regel", de, en, q)


def _tabelle(b, d, q):
    return Ereignis(b, "%s.tabelle" % b, "unbestimmt", d, d, d, "keiner", False, "tabelle", None, None, q)


# ── Gemeinsame Termine ──────────────────────────────────────────────────────────────────────────────────────
def _fest(b, j, liste, q):
    """[(regel_kurz, datum, de, en)] → Feiertage ohne Ersatz (EU-Börsen: kein Wochenend-Ersatz)."""
    return [_e(b, "%s.%s" % (b, k), d, de, en, q) for k, d, de, en in liste]


# ── NYSE ────────────────────────────────────────────────────────────────────────────────────────────────────
_NYSE_SONDER_TEXT = {
    date(2025, 1, 9): ("carter", "Staatstrauer Jimmy Carter", "National Day of Mourning (Jimmy Carter)"),
    date(2018, 12, 5): ("bush", "Staatstrauer George H. W. Bush", "National Day of Mourning (George H. W. Bush)"),
    date(2012, 10, 29): ("sandy_1", "Hurrikan Sandy (Tag 1)", "Hurricane Sandy (day 1)"),
    date(2012, 10, 30): ("sandy_2", "Hurrikan Sandy (Tag 2)", "Hurricane Sandy (day 2)"),
    date(2007, 1, 2): ("ford", "Staatstrauer Gerald Ford", "National Day of Mourning (Gerald Ford)"),
    date(2004, 6, 11): ("reagan", "Staatstrauer Ronald Reagan", "National Day of Mourning (Ronald Reagan)"),
    date(2001, 9, 11): ("911_1", "Anschläge 11. September (Tag 1)", "September 11 attacks (day 1)"),
    date(2001, 9, 12): ("911_2", "Anschläge 11. September (Tag 2)", "September 11 attacks (day 2)"),
    date(2001, 9, 13): ("911_3", "Anschläge 11. September (Tag 3)", "September 11 attacks (day 3)"),
    date(2001, 9, 14): ("911_4", "Anschläge 11. September (Tag 4)", "September 11 attacks (day 4)"),
    date(1994, 4, 27): ("nixon", "Staatstrauer Richard Nixon", "National Day of Mourning (Richard Nixon)"),
    date(1985, 9, 27): ("gloria", "Hurrikan Gloria", "Hurricane Gloria"),
    date(1980, 11, 4): ("wahl", "Präsidentschaftswahl", "Presidential Election Day"),
    date(1977, 7, 14): ("stromausfall", "Stromausfall New York", "New York City blackout"),
    date(1976, 11, 2): ("wahl", "Präsidentschaftswahl", "Presidential Election Day"),
    date(1973, 1, 25): ("johnson", "Staatstrauer Lyndon B. Johnson", "National Day of Mourning (Lyndon B. Johnson)"),
    date(1972, 12, 28): ("truman", "Staatstrauer Harry S. Truman", "National Day of Mourning (Harry S. Truman)"),
    date(1972, 11, 7): ("wahl", "Präsidentschaftswahl", "Presidential Election Day"),
}


def _nyse(j):
    b, q = "NYSE", "NYSE.regelwerk"
    out = []
    nj = date(j, 1, 1)
    out.append(_e(b, "NYSE.new_year", nj, "Neujahr", "New Year's Day", q,
                  wirksam=_monday_if_sunday(nj), grund="wochenende" if nj.weekday() == 6 else "keiner"))
    if j >= 1998:
        out.append(_e(b, "NYSE.mlk_day", _nth_weekday(j, 1, 0, 3), "Martin Luther King Jr. Day", "Martin Luther King Jr. Day", q))
    out.append(_e(b, "NYSE.presidents_day", _nth_weekday(j, 2, 0, 3), "Presidents' Day", "Presidents' Day", q))
    out.append(_e(b, "NYSE.good_friday", _good_friday(j), "Karfreitag", "Good Friday", q))
    out.append(_e(b, "NYSE.memorial_day", _nth_weekday(j, 5, 0, -1), "Memorial Day", "Memorial Day", q))
    for rid, d, de, en, ab in (("NYSE.juneteenth", date(j, 6, 19), "Juneteenth", "Juneteenth", 2022),
                               ("NYSE.independence_day", date(j, 7, 4), "Unabhängigkeitstag", "Independence Day", 0),
                               ("NYSE.christmas", date(j, 12, 25), "Weihnachten", "Christmas Day", 0)):
        if j >= ab:
            w = _observed(d)
            out.append(_e(b, rid, d, de, en, q, wirksam=w, grund="wochenende" if w != d else "keiner"))
    out.append(_e(b, "NYSE.labor_day", _nth_weekday(j, 9, 0, 1), "Labor Day", "Labor Day", q))
    out.append(_e(b, "NYSE.thanksgiving", _nth_weekday(j, 11, 3, 4), "Thanksgiving", "Thanksgiving Day", q))
    for d in sorted(x for x in _NYSE_SPECIAL_CLOSURES if x.year == j):
        kurz, de, en = _NYSE_SONDER_TEXT[d]
        out.append(_sonder(b, d, kurz, de, en, "NYSE.sonderschliessungen"))
    out.extend(_halbtage(b, j))
    return out


def _halbtage(b, j):
    """Belegte Halbtage (V1c-3) — nur aus shared/halbtage_belege.py, nie aus einer Regel; offene Sitzungen."""
    from shared.halbtage_belege import HALBTAGE, NAMEN
    reihe = HALBTAGE.get(b)
    if not reihe:
        return []
    out = []
    for iso, (kurz, quelle) in sorted(reihe["ereignisse"].items()):
        d = date.fromisoformat(iso)
        if d.year != j:
            continue
        de, en = NAMEN[kurz]
        out.append(Ereignis(b, "%s.halbtag.%s" % (b, kurz), "halbtag", d, d, d, "keiner", False, "regel", de, en,
                            quelle, reihe["schlusszeit"], reihe["zeitzone"], reihe["sitzung"]))
    return out


# ── XETRA, EURONEXT, MILAN, SIX, STOCKHOLM, OSLO (feste Daten, kein Ersatz) ─────────────────────────────────
def _xetra(j):
    b = "XETRA"
    liste = [("neujahr", date(j, 1, 1), "Neujahr", "New Year's Day"),
             ("karfreitag", _good_friday(j), "Karfreitag", "Good Friday"),
             ("ostermontag", _easter_monday(j), "Ostermontag", "Easter Monday"),
             ("tag_der_arbeit", date(j, 5, 1), "Tag der Arbeit", "Labour Day"),
             ("weihnachten_1", date(j, 12, 25), "1. Weihnachtstag", "Christmas Day"),
             ("weihnachten_2", date(j, 12, 26), "2. Weihnachtstag", "Boxing Day")]
    if j >= 2001:
        liste += [("heiligabend", date(j, 12, 24), "Heiligabend", "Christmas Eve"),
                  ("silvester", date(j, 12, 31), "Silvester", "New Year's Eve")]
    out = _fest(b, j, liste, "XETRA.regelwerk")
    texte = {"pfingstmontag": ("Pfingstmontag (Sonderschließung)", "Whit Monday (special closure)"),
             "einheit": ("Tag der Deutschen Einheit (Sonderschließung)", "German Unity Day (special closure)"),
             "reformationstag": ("Reformationstag 500 Jahre (Sonderschließung)", "Reformation Day, 500th anniversary (special closure)")}
    for d in sorted(x for x in XETRA_SONDER if x.year == j):
        if d == _whit_monday(j):
            kurz = "pfingstmontag"
        elif (d.month, d.day) == (10, 3):
            kurz = "einheit"
        elif (d.month, d.day) == (10, 31):
            kurz = "reformationstag"
        else:
            raise ValueError("XETRA-Sonderschließung ohne Zuordnung: %s" % d)
        out.append(_sonder(b, d, kurz, texte[kurz][0], texte[kurz][1], "XETRA.sonderschliessungen"))
    return out


def _euronext_liste(j):
    return [("neujahr", date(j, 1, 1), "Neujahr", "New Year's Day"),
            ("karfreitag", _good_friday(j), "Karfreitag", "Good Friday"),
            ("ostermontag", _easter_monday(j), "Ostermontag", "Easter Monday"),
            ("tag_der_arbeit", date(j, 5, 1), "Tag der Arbeit", "Labour Day"),
            ("weihnachten_1", date(j, 12, 25), "1. Weihnachtstag", "Christmas Day"),
            ("weihnachten_2", date(j, 12, 26), "2. Weihnachtstag", "Boxing Day")]


def _euronext(j):
    return _fest("EURONEXT", j, _euronext_liste(j), "EURONEXT.regelwerk")


def _milan(j):
    liste = _euronext_liste(j) + [("ferragosto", date(j, 8, 15), "Ferragosto", "Ferragosto (Assumption Day)"),
                                  ("vigilia_di_natale", date(j, 12, 24), "Heiligabend", "Christmas Eve"),
                                  ("san_silvestro", date(j, 12, 31), "Silvester", "New Year's Eve")]
    return _fest("MILAN", j, liste, "MILAN.regelwerk")


def _six(j):
    liste = [("neujahr", date(j, 1, 1), "Neujahr", "New Year's Day"),
             ("berchtoldstag", date(j, 1, 2), "Berchtoldstag", "Berchtold's Day"),
             ("karfreitag", _good_friday(j), "Karfreitag", "Good Friday"),
             ("ostermontag", _easter_monday(j), "Ostermontag", "Easter Monday"),
             ("tag_der_arbeit", date(j, 5, 1), "Tag der Arbeit", "Labour Day"),
             ("auffahrt", _ascension_day(j), "Christi Himmelfahrt", "Ascension Day"),
             ("pfingstmontag", _whit_monday(j), "Pfingstmontag", "Whit Monday"),
             ("bundesfeier", date(j, 8, 1), "Bundesfeier", "Swiss National Day"),
             ("heiligabend", date(j, 12, 24), "Heiligabend", "Christmas Eve"),
             ("weihnachten", date(j, 12, 25), "Weihnachten", "Christmas Day"),
             ("stephanstag", date(j, 12, 26), "Stephanstag", "St. Stephen's Day"),
             ("silvester", date(j, 12, 31), "Silvester", "New Year's Eve")]
    return _fest("SIX", j, liste, "SIX.regelwerk")


def _stockholm(j):
    midsommar = date(j, 6, 19)
    while midsommar.weekday() != 4:
        midsommar += timedelta(days=1)
    liste = [("nyarsdagen", date(j, 1, 1), "Neujahr", "New Year's Day"),
             ("trettondedag_jul", date(j, 1, 6), "Heilige Drei Könige", "Epiphany"),
             ("langfredagen", _good_friday(j), "Karfreitag", "Good Friday"),
             ("annandag_pask", _easter_monday(j), "Ostermontag", "Easter Monday"),
             ("forsta_maj", date(j, 5, 1), "Tag der Arbeit", "Labour Day"),
             ("kristi_himmelsfard", _ascension_day(j), "Christi Himmelfahrt", "Ascension Day"),
             ("nationaldagen", date(j, 6, 6), "Nationalfeiertag", "National Day of Sweden"),
             ("midsommarafton", midsommar, "Mittsommerabend", "Midsummer Eve"),
             ("julafton", date(j, 12, 24), "Heiligabend", "Christmas Eve"),
             ("juldagen", date(j, 12, 25), "Weihnachten", "Christmas Day"),
             ("annandag_jul", date(j, 12, 26), "2. Weihnachtstag", "Boxing Day"),
             ("nyarsafton", date(j, 12, 31), "Silvester", "New Year's Eve")]
    return _fest("STOCKHOLM", j, liste, "STOCKHOLM.regelwerk")


def _oslo(j):
    liste = [("forste_nyttarsdag", date(j, 1, 1), "Neujahr", "New Year's Day"),
             ("skjaertorsdag", _good_friday(j) - timedelta(days=1), "Gründonnerstag", "Maundy Thursday"),
             ("langfredag", _good_friday(j), "Karfreitag", "Good Friday"),
             ("andre_paskedag", _easter_monday(j), "Ostermontag", "Easter Monday"),
             ("arbeidernes_dag", date(j, 5, 1), "Tag der Arbeit", "Labour Day"),
             ("grunnlovsdag", date(j, 5, 17), "Verfassungstag", "Constitution Day"),
             ("kristi_himmelfartsdag", _ascension_day(j), "Christi Himmelfahrt", "Ascension Day"),
             ("andre_pinsedag", _whit_monday(j), "Pfingstmontag", "Whit Monday"),
             ("julaften", date(j, 12, 24), "Heiligabend", "Christmas Eve"),
             ("forste_juledag", date(j, 12, 25), "Weihnachten", "Christmas Day"),
             ("andre_juledag", date(j, 12, 26), "2. Weihnachtstag", "Boxing Day"),
             ("nyttarsaften", date(j, 12, 31), "Silvester", "New Year's Eve")]
    return _fest("OSLO", j, liste, "OSLO.regelwerk")


# ── LSE ─────────────────────────────────────────────────────────────────────────────────────────────────────
def _lse(j):
    b, q = "LSE", "LSE.regelwerk"
    out = []
    nj = date(j, 1, 1)
    w = nj + timedelta(days=(7 - nj.weekday()) % 7) if nj.weekday() >= 5 else nj
    out.append(_e(b, "LSE.new_year", nj, "Neujahr", "New Year's Day", q, wirksam=w,
                  grund="wochenende" if w != nj else "keiner"))
    out.append(_e(b, "LSE.good_friday", _good_friday(j), "Karfreitag", "Good Friday", q))
    out.append(_e(b, "LSE.easter_monday", _easter_monday(j), "Ostermontag", "Easter Monday", q))
    early = _nth_weekday(j, 5, 0, 1)
    if j == 2020:     # VE Day 75 — Early May Bank Holiday auf Fr 8.5. verlegt (gov.uk)
        out.append(_e(b, "LSE.early_may", early, "Early May Bank Holiday", "Early May Bank Holiday", "LSE.verlegungen",
                      rechtlich=date(2020, 5, 8), grund="verlegung", verlegt=True))
    else:
        out.append(_e(b, "LSE.early_may", early, "Early May Bank Holiday", "Early May Bank Holiday", q))
    spring = _nth_weekday(j, 5, 0, -1)
    verlegt_spring = {2002: date(2002, 6, 4), 2012: date(2012, 6, 4), 2022: date(2022, 6, 2)}
    jubilaeum = {2002: (date(2002, 6, 3), "golden_jubilee", "Goldenes Thronjubiläum", "Golden Jubilee"),
                 2012: (date(2012, 6, 5), "diamond_jubilee", "Diamantenes Thronjubiläum", "Diamond Jubilee"),
                 2022: (date(2022, 6, 3), "platinum_jubilee", "Platin-Thronjubiläum", "Platinum Jubilee")}
    if j in verlegt_spring:
        out.append(_e(b, "LSE.spring_bank", spring, "Spring Bank Holiday", "Spring Bank Holiday", "LSE.verlegungen",
                      rechtlich=verlegt_spring[j], grund="verlegung", verlegt=True))
        d, kurz, de, en = jubilaeum[j]
        out.append(_sonder(b, d, kurz, de, en, "LSE.verlegungen"))
    else:
        out.append(_e(b, "LSE.spring_bank", spring, "Spring Bank Holiday", "Spring Bank Holiday", q))
    out.append(_e(b, "LSE.summer_bank", _nth_weekday(j, 8, 0, -1), "Summer Bank Holiday", "Summer Bank Holiday", q))
    # Weihnachten / Boxing Day (England & Wales, gov.uk): fällt einer auf Sa/So, Ersatz am nächsten freien Werktag;
    # Weihnachten So → Boxing Day Mo 26. (Feiertag), Weihnachts-Ersatz Di 27.
    xmas, boxing = date(j, 12, 25), date(j, 12, 26)
    if xmas.weekday() == 5:        # Sa: Weihnachten → Mo 27., Boxing Day So → Di 28.
        xw, bw = date(j, 12, 27), date(j, 12, 28)
    elif xmas.weekday() == 6:      # So: Boxing Day Mo 26., Weihnachten → Di 27.
        xw, bw = date(j, 12, 27), boxing
    elif boxing.weekday() == 5:    # Fr 25., Boxing Day Sa → Mo 28.
        xw, bw = xmas, date(j, 12, 28)
    else:
        xw, bw = xmas, boxing
    out.append(_e(b, "LSE.christmas", xmas, "Weihnachten", "Christmas Day", q, wirksam=xw,
                  grund="wochenende" if xw != xmas else "keiner"))
    out.append(_e(b, "LSE.boxing_day", boxing, "2. Weihnachtstag", "Boxing Day", q, wirksam=bw,
                  grund="wochenende" if bw != boxing else "keiner"))
    for d, kurz, de, en in ((date(2011, 4, 29), "royal_wedding", "Königliche Hochzeit", "Royal Wedding"),
                            (date(2022, 9, 19), "staatsbegraebnis", "Staatsbegräbnis Elizabeth II.", "State Funeral of Queen Elizabeth II"),
                            (date(2023, 5, 8), "kroenung", "Krönung Charles III.", "Coronation of King Charles III")):
        if d.year == j:
            out.append(_sonder(b, d, kurz, de, en, "LSE.sonderschliessungen"))
    return out


# ── TSE ─────────────────────────────────────────────────────────────────────────────────────────────────────
def _tse(j):
    b, q = "TSE", "TSE.regelwerk"

    def equinox(m):
        # Astronomische Näherung (gültig 1980–2099), unverändert aus dem bisherigen Kalendercode
        if m == 3:
            return date(j, 3, int(20.8431 + 0.242194 * (j - 1980) - (j - 1980) // 4))
        return date(j, 9, int(23.2488 + 0.242194 * (j - 1980) - (j - 1980) // 4))

    regeln = []   # (regel_kurz, nominal, rechtlich, de, en, verlegt, quelle)

    def r(kurz, nominal, de, en, rechtlich=None, quelle=q):
        regeln.append((kurz, nominal, rechtlich or nominal, de, en, rechtlich is not None and rechtlich != nominal, quelle))

    r("ganjitsu", date(j, 1, 1), "Neujahr", "New Year's Day")
    r("kenkoku_kinen_no_hi", date(j, 2, 11), "Staatsgründungstag", "National Foundation Day")
    r("shunbun_no_hi", equinox(3), "Frühlingsanfang", "Vernal Equinox Day")
    r("0429", date(j, 4, 29), "Showa-Tag" if j >= 2007 else ("Tag des Grüns" if j >= 1989 else "Kaisergeburtstag"),
      "Showa Day" if j >= 2007 else ("Greenery Day" if j >= 1989 else "Emperor's Birthday"))
    r("kenpo_kinenbi", date(j, 5, 3), "Verfassungstag", "Constitution Memorial Day")
    r("0504", date(j, 5, 4), "Tag des Grüns" if j >= 2007 else "Volksfeiertag (4. Mai)",
      "Greenery Day" if j >= 2007 else "Citizens' Holiday (4 May)")
    r("kodomo_no_hi", date(j, 5, 5), "Kindertag", "Children's Day")
    r("shubun_no_hi", equinox(9), "Herbstanfang", "Autumnal Equinox Day")
    r("bunka_no_hi", date(j, 11, 3), "Kulturtag", "Culture Day")
    r("kinro_kansha_no_hi", date(j, 11, 23), "Tag des Dankes für die Arbeit", "Labour Thanksgiving Day")
    r("seijin_no_hi", _nth_weekday(j, 1, 0, 2) if j >= 2000 else date(j, 1, 15), "Tag der Volljährigkeit", "Coming of Age Day")
    umi = _nth_weekday(j, 7, 0, 3) if j >= 2003 else (date(j, 7, 20) if j >= 1996 else None)
    sport = _nth_weekday(j, 10, 0, 2) if j >= 2000 else (date(j, 10, 10) if j >= 1966 else None)
    yama = date(j, 8, 11) if j >= 2016 else None
    if j in _TSE_OLYMPIA:        # Sondergesetz Olympia: Meeres-, Sport- und Bergtag verlegt
        o = _TSE_OLYMPIA[j]
        r("umi_no_hi", umi, "Tag des Meeres", "Marine Day", rechtlich=o[0], quelle="TSE.olympia")
        r("sports_no_hi", sport, "Tag des Sports", "Sports Day", rechtlich=o[1], quelle="TSE.olympia")
        r("yama_no_hi", yama, "Tag der Berge", "Mountain Day", rechtlich=o[2], quelle="TSE.olympia")
    else:
        if umi:
            r("umi_no_hi", umi, "Tag des Meeres", "Marine Day")
        if sport:
            r("sports_no_hi", sport, "Tag des Sports" if j >= 2020 else "Tag der Gesundheit und des Sports",
              "Sports Day" if j >= 2020 else "Health and Sports Day")
        if yama:
            r("yama_no_hi", yama, "Tag der Berge", "Mountain Day")
    if j >= 2003:
        r("keiro_no_hi", _nth_weekday(j, 9, 0, 3), "Tag der Achtung vor dem Alter", "Respect for the Aged Day")
    elif j >= 1966:
        r("keiro_no_hi", date(j, 9, 15), "Tag der Achtung vor dem Alter", "Respect for the Aged Day")
    if j >= 2020:
        r("tenno_tanjobi", date(j, 2, 23), "Geburtstag des Kaisers", "Emperor's Birthday")
    elif 1989 <= j <= 2018:
        r("tenno_tanjobi", date(j, 12, 23), "Geburtstag des Kaisers", "Emperor's Birthday")
    for d in _TSE_EINMALIG_FEIERTAG.get(j, ()):
        r("einmalig_%s" % d.isoformat(), d, "Thronbesteigung" if d.month == 5 else "Inthronisierungszeremonie",
          "Enthronement Day" if d.month == 5 else "Enthronement Ceremony Day", quelle="TSE.einmalig")

    national = {x[2] for x in regeln}          # rechtliche Feiertage (wie bisher `national`)
    furikae = {}                               # rechtlicher Sonntag → Ersatztag
    for h in sorted(national):
        if h.weekday() == 6 and j >= 1973:
            sub = h + timedelta(days=1)
            if j >= 2007:
                while sub in national:
                    sub += timedelta(days=1)
                furikae[h] = sub
            elif sub not in national:
                furikae[h] = sub
    out = []
    for kurz, nominal, rechtlich, de, en, verlegt, quelle in regeln:
        if rechtlich in furikae:
            out.append(_e(b, "TSE." + kurz, nominal, de, en, quelle, rechtlich=rechtlich, wirksam=furikae[rechtlich],
                          grund="furikae", verlegt=verlegt))
        else:
            out.append(_e(b, "TSE." + kurz, nominal, de, en, quelle, rechtlich=rechtlich,
                          grund="verlegung" if verlegt else "keiner", verlegt=verlegt))
    for h in sorted(national):                 # Kokumin no Kyujitsu: Werktag zwischen zwei Feiertagen
        mid = h + timedelta(days=1)
        if (h + timedelta(days=2)) in national and mid not in national and mid.weekday() < 5:
            out.append(_e(b, "TSE.kokumin_no_kyujitsu", mid, "Brückentag (Volksfeiertag)", "Citizens' Holiday (bridge)", q))
    for d in _TSE_BOERSE_GESCHLOSSEN.get(j, ()):
        out.append(_sonder(b, d, "systemausfall", "Systemausfall (Börse geschlossen)", "System outage (exchange closed)",
                           "TSE.sonderschliessungen"))
    for d, kurz in ((date(j, 1, 2), "0102"), (date(j, 1, 3), "0103"), (date(j, 12, 31), "1231")):
        out.append(_e(b, "TSE.jahreswechsel_" + kurz, d, "Jahreswechsel (Börse geschlossen)",
                      "Year-end/New Year market holiday", "TSE.jahreswechsel"))
    return out


# ── HKEX, KRX (Tabellen 2016–2026, sonst Regel-Rückfall als Konvention) ─────────────────────────────────────
def _hkex(j):
    b = "HKEX"
    if j in _HKEX_HOLIDAYS:
        return [_tabelle(b, date(j, m, d), "HKEX.tabelle") for m, d in _HKEX_HOLIDAYS[j]]
    return _fest(b, j, [("neujahr", date(j, 1, 1), "Neujahr", "New Year's Day"),
                        ("karfreitag", _good_friday(j), "Karfreitag", "Good Friday"),
                        ("ostermontag", _easter_monday(j), "Ostermontag", "Easter Monday"),
                        ("tag_der_arbeit", date(j, 5, 1), "Tag der Arbeit", "Labour Day"),
                        ("hksar", date(j, 7, 1), "Gründungstag der Sonderverwaltungszone", "HKSAR Establishment Day"),
                        ("nationalfeiertag", date(j, 10, 1), "Nationalfeiertag", "National Day"),
                        ("weihnachten", date(j, 12, 25), "Weihnachten", "Christmas Day"),
                        ("weihnachten_2", date(j, 12, 26), "2. Weihnachtstag", "Boxing Day")], "HKEX.konvention")


def _krx(j):
    b = "KRX"
    if j in _KRX_HOLIDAYS:
        return [_tabelle(b, date(j, m, d), "KRX.tabelle") for m, d in _KRX_HOLIDAYS[j]]
    return _fest(b, j, [("neujahr", date(j, 1, 1), "Neujahr", "New Year's Day"),
                        ("samiljeol", date(j, 3, 1), "Unabhängigkeitsbewegung", "Independence Movement Day"),
                        ("tag_der_arbeit", date(j, 5, 1), "Tag der Arbeit", "Labour Day"),
                        ("kindertag", date(j, 5, 5), "Kindertag", "Children's Day"),
                        ("hyeonchungil", date(j, 6, 6), "Gedenktag", "Memorial Day"),
                        ("gwangbokjeol", date(j, 8, 15), "Tag der Befreiung", "Liberation Day"),
                        ("gaecheonjeol", date(j, 10, 3), "Staatsgründungstag", "National Foundation Day"),
                        ("hangeul", date(j, 10, 9), "Hangeul-Tag", "Hangeul Day"),
                        ("weihnachten", date(j, 12, 25), "Weihnachten", "Christmas Day"),
                        ("jahresende", date(j, 12, 31), "Jahresende (Börse geschlossen)", "Year-end market holiday")],
                 "KRX.konvention")


_REGELN = {"NYSE": _nyse, "XETRA": _xetra, "LSE": _lse, "EURONEXT": _euronext, "TSE": _tse, "SIX": _six,
           "MILAN": _milan, "STOCKHOLM": _stockholm, "OSLO": _oslo, "HKEX": _hkex, "KRX": _krx,
           "FOREX": lambda j: [], "CRYPTO": lambda j: []}
BOERSEN = tuple(sorted(_REGELN))


@functools.lru_cache(maxsize=None)
def _ereignisse(boerse: str, jahr: int) -> tuple:
    return tuple(_REGELN[boerse](jahr))


def ereignisse(boerse: str, jahr: int) -> list[Ereignis]:
    """Alle Ereignisse einer Börse in einem Jahr (Jahr = Jahr des Regeltermins). NASDAQ → NYSE (Alias)."""
    b = ALIAS.get(boerse, boerse)
    if b not in _REGELN:
        raise ValueError("unbekannte Börse %r" % boerse)
    return list(_ereignisse(b, jahr))


@functools.lru_cache(maxsize=None)
def kompat(boerse: str, jahr: int) -> frozenset:
    """Die bisherige Feiertagsmenge (Bestandsschutz): wirksame Tage, bei TSE zusätzlich der rechtliche Sonntag
    eines Furikae. Ursprüngliche Regeltermine einer Verlegung NIE."""
    b = ALIAS.get(boerse, boerse)
    menge = set()
    for e in ereignisse(b, jahr):
        if e.art == "halbtag":
            continue
        menge.add(e.wirksam)
        if b in NOMINAL_BLEIBT and e.ersatzgrund == "furikae":
            menge.add(e.rechtlich)
    return frozenset(menge)


def schliessungen(boerse: str, jahr: int) -> list[date]:
    """Eindeutige wirksame Vollschließungen auf sonst offenen Tagen (Mo–Fr; CRYPTO/FOREX: keine)."""
    b = ALIAS.get(boerse, boerse)
    return sorted({e.wirksam for e in ereignisse(b, jahr) if e.art != "halbtag" and e.wirksam.weekday() < 5})


def halbtag_status(boerse: str, jahr: int) -> str:
    """'belegt', wenn eine Quelle die Halbtage des GANZEN Jahres nennt, sonst 'ungeprueft' (auch bei Einzelbelegen)."""
    from shared.halbtage_belege import HALBTAGE
    b = ALIAS.get(boerse, boerse)
    if b not in _REGELN:
        raise ValueError("unbekannte Börse %r" % boerse)
    return "belegt" if jahr in HALBTAGE.get(b, {}).get("abdeckung", {}) else "ungeprueft"


def identitaet(boerse: str, jahr: int) -> str:
    """'tabelle', wenn ein Ereignis des Jahres nur aus einer Datumstabelle stammt (benannte Abnahmelücke), sonst 'regel'."""
    return "tabelle" if any(e.nominal_herkunft == "tabelle" for e in ereignisse(boerse, jahr)) else "regel"


def abnahmeluecken() -> list[tuple[str, int]]:
    """Alle (Börse, Jahr) mit Tabellenidentität — im Wächter als Liste ausgewiesen, nie stillschweigend grün."""
    return [(b, j) for b in BOERSEN for j in range(1885, 2101) if identitaet(b, j) == "tabelle"]


def ereignisversion(boersen=None, von: int = 1885, bis: int = 2100) -> str:
    """SHA-256 über die aufgelösten Ereignisinhalte (alle Felder, Namen, Quellen) — ohne Versionsfelder."""
    h = hashlib.sha256()
    for b in (boersen or BOERSEN):
        for j in range(von, bis + 1):
            for e in ereignisse(b, j):
                h.update(json.dumps(e.inhalt(), sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return h.hexdigest()


@functools.lru_cache(maxsize=None)
def _kalenderversion_gesamt() -> str:
    return kalenderversion()


def kalenderversion(boersen=None, von: int = 1885, bis: int = 2100) -> str:
    """SHA-256 über die Schließungsprojektion — ändert sich genau dann, wenn sie sich ändert."""
    h = hashlib.sha256()
    for b in (boersen or BOERSEN):
        for j in range(von, bis + 1):
            h.update(("%s:%d:%s;" % (b, j, ",".join(d.isoformat() for d in schliessungen(b, j)))).encode("utf-8"))
    return h.hexdigest()
