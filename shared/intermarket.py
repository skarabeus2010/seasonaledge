#!/usr/bin/env python3
"""
intermarket.py — Signale aus der Lead-Lag-Studie, fuer das Daily Briefing.

Setzt genau das um, was in scripts/research/bond_lead_lag.py und
bond_kontrollen.py gemessen wurde — nicht mehr. Die Studie und dieses Modul
duerfen nicht auseinanderlaufen; wer hier eine Schwelle aendert, aendert eine
Aussage, die auf gemessenen Zahlen beruht.

WAS GEMELDET WIRD, und unter welcher Bedingung:

1. ANLEIHEN-SIGNAL (das belastbarere)
   Ausloeser: TLT-Kursanstieg von mindestens 4,1 % ueber 10 Handelstage.
   BEDINGUNG: die realisierte Volatilitaet des S&P 500 liegt UEBER 13,9 %
   (annualisiert, 21 Handelstage). Ohne diese Bedingung wird nicht gemeldet.

   Warum die Bedingung zwingend ist: gemessen ueber 2002-2026 stieg der S&P 500
   nach einem solchen Anstieg im Schnitt um +2,09 % in zwei Wochen gegen einen
   Marktdurchschnitt von +0,48 %. Getrennt nach Marktumfeld zerfaellt das aber:
   in unruhigen Phasen +3,65 % (p < 0,001), in RUHIGEN +0,53 % bei p = 0,935 —
   also exakt der Marktdurchschnitt, sprich nichts. Ein Signal ohne diese
   Bedingung waere Rauschen, das wie eine Aussage aussieht.

   Und es ist kein Orakel: der S&P 500 ist VOR dem Ereignis im Median um 1,33 %
   gefallen. Was gemessen wurde, ist ein Erholungsmuster nach einer Flucht in
   Staatsanleihen, keine Vorhersage aus heiterem Himmel. Der Text sagt das.

2. KRYPTO-SIGNAL (schwaecher, deshalb strenger)
   Ausloeser: Bitcoin oder Ether mindestens 20 % ueber 10 Handelstage.
   Darunter zeigte die Studie nichts: die viel zitierte 5-%-Schwelle ist bei
   Bitcoin der MEDIAN aller 10-Tage-Bewegungen, also die normalste Bewegung
   ueberhaupt, und der Effekt dort liegt unter dem Marktdurchschnitt. Erst ab
   20 % war ueberhaupt etwas messbar (+2,29 % nach drei Wochen, p = 0,027), und
   bei Bitcoin nach vier Wochen nur noch ein Grenzfall (p = 0,050).

SCHWELLEN sind bewusst fest und nicht rollierend: sie stammen aus einer
gerechneten Studie mit ausgewiesenen p-Werten. Eine selbstkalibrierende
Schwelle waere bequemer, haette aber keine gemessene Grundlage mehr. Nach einer
Neuberechnung der Studie gehoeren sie angepasst — Stand 2026-09-22.
"""
from __future__ import annotations

import math

from shared.data import KursreiheFehlt, lade_closes
from shared.realized_vol import log_returns, rv_aus_returns

FENSTER = 10                 # Handelstage, ueber die die Bewegung gemessen wird

# EXAKT der Wert aus scripts/research/bond_lead_lag.schwellen(), nicht die
# im Artikel angezeigte Rundung "4,1 %". Die gerundete Zahl 0,041 waehlt eine
# andere Ereignismenge und wuerde hier ein anderes Signal ausloesen als das,
# was gemessen wurde.
TLT_SCHWELLE = 0.040632      # 90. Perzentil der TLT-10-Tage-Bewegungen
VOLA_SCHWELLE = 0.139        # Median der realisierten SPY-Vola (21 HT, annualisiert)
KRYPTO_SCHWELLE = 0.20       # darunter war in der Studie nichts messbar

KRYPTOS = (("BTC-USD", "Bitcoin"), ("ETH-USD", "Ether"))


def _bewegung(ticker: str, tage: int = FENSTER) -> tuple[float | None, str | None]:
    """Kursbewegung ueber die letzten `tage` Handelstage, als Anteil."""
    try:
        daten, closes = lade_closes(ticker, mindestens=tage + 5)
    except (KursreiheFehlt, Exception):
        return None, None
    if len(closes) < tage + 1:
        return None, None
    lr = log_returns(closes)[-tage:]
    if any(x is None for x in lr):
        return None, daten[-1]
    return math.exp(sum(lr)) - 1.0, daten[-1]


def _spy_vola() -> float | None:
    """Realisierte Vola des S&P 500, 21 Handelstage, annualisiert."""
    try:
        _, closes = lade_closes("SPY", mindestens=40)
    except Exception:
        return None
    return rv_aus_returns(log_returns(closes), 21)


def intermarket_signale() -> list[dict]:
    """Die heute zutreffenden Signale. Leere Liste heisst: nichts zu melden.

    Bewusst still, wenn nichts zutrifft. Eine taegliche Zeile "heute kein
    Signal" waere kein Informationsgewinn und wuerde die Mail nur laenger
    machen — und sie wuerde den Eindruck erwecken, hier gaebe es taeglich etwas
    zu entscheiden.
    """
    out: list[dict] = []

    # ── Anleihen ────────────────────────────────────────────────────────────
    bew, stand = _bewegung("TLT")
    vola = _spy_vola()
    if bew is not None and bew >= TLT_SCHWELLE:
        if vola is not None and vola > VOLA_SCHWELLE:
            out.append({
                "art": "anleihen",
                "titel": "Starke Bewegung in langlaufenden Staatsanleihen",
                "text": ("TLT ist in den letzten %d Handelstagen um %.1f %% gestiegen, "
                         "die Schwankung im S&P 500 liegt mit %.0f %% über dem "
                         "langjährigen Mittel. In dieser Kombination folgte dem "
                         "historisch (2002-2026, 50 Fälle) eine überdurchschnittliche "
                         "Erholung des S&P 500: +3,65 %% in zwei Wochen gegen +0,48 %% "
                         "im Marktdurchschnitt. Wichtig: der S&P 500 war zuvor "
                         "gefallen — gemessen ist ein Erholungsmuster, keine Prognose."
                         % (FENSTER, bew * 100, vola * 100)),
                "stand": stand,
                "artikel": "/blog/anleihen-fruehindikator-aktienmarkt",
            })
        else:
            # Ausloeser ja, Bedingung nein: NICHT melden. Der Zweig existiert,
            # damit beim Lesen klar ist, dass das Weglassen Absicht ist.
            pass

    # ── Krypto ──────────────────────────────────────────────────────────────
    for ticker, name in KRYPTOS:
        bew, stand = _bewegung(ticker)
        if bew is None or abs(bew) < KRYPTO_SCHWELLE:
            continue
        richtung = "gestiegen" if bew > 0 else "gefallen"
        if bew > 0:
            text = ("%s ist in den letzten %d Handelstagen um %.0f %% %s. Bewegungen "
                    "dieser Größenordnung gingen historisch einer leicht "
                    "überdurchschnittlichen Entwicklung des S&P 500 voraus, sichtbar "
                    "erst nach drei bis vier Wochen und statistisch knapp. Kleinere "
                    "Krypto-Anstiege zeigten dagegen keinen Zusammenhang."
                    % (name, FENSTER, bew * 100, richtung))
        else:
            text = ("%s ist in den letzten %d Handelstagen um %.0f %% %s. Für "
                    "Abwärtsbewegungen dieser Größe fand sich in der Untersuchung "
                    "kein belastbarer Zusammenhang zum S&P 500 — die Zeile steht "
                    "hier als Marktinformation, nicht als Signal."
                    % (name, FENSTER, abs(bew) * 100, richtung))
        out.append({"art": "krypto", "titel": "%s: %.0f %% in %d Handelstagen"
                                              % (name, abs(bew) * 100, FENSTER),
                    "text": text, "stand": stand,
                    "artikel": "/blog/laeuft-bitcoin-dem-aktienmarkt-voraus"})
    return out
