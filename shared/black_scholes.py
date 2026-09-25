#!/usr/bin/env python3
"""
black_scholes.py — EINE Black-Scholes-Implementierung für alle Options-Pipelines.

WARUM GEMEINSAM: Skew-Historie und Live-Tageswert landen in DERSELBEN Reihe, über
die das Frontend Rank/Percentile rechnet. Sobald beide Seiten die IV auch nur
leicht unterschiedlich bestimmen, entsteht ein systematischer Versatz zwischen
Backfill- und Live-Punkten — und der Percentile misst dann den Methodenwechsel
statt den Skew.

Gemessener Schaden vor der Vereinheitlichung (2026-09-09): Provider-IV vs. eigene
BS-Inversion wichen im Zeta um 0,84–1,30 Punkte ab, bei NVDA so viel wie der
gesamte Interquartilsabstand der Reihe (1,28) — der Live-Punkt landete dadurch
im 99. Percentil, rein methodisch. Deshalb: eine Quelle, keine Kopien.
"""
from __future__ import annotations
import math
import re
from datetime import date as _date

# Risk-free-Näherung; q=0. Für Differenzen INNERHALB einer Expiry unkritisch,
# muss aber auf beiden Seiten identisch sein.
R = 0.045


def cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_price(S, K, T, sig, typ):
    if T <= 0 or sig <= 0 or S <= 0 or K <= 0:
        return max(0.0, (S - K) if typ == "call" else (K - S))
    srt = sig * math.sqrt(T)
    d1 = (math.log(S / K) + (R + 0.5 * sig * sig) * T) / srt
    d2 = d1 - srt
    if typ == "call":
        return S * cdf(d1) - K * math.exp(-R * T) * cdf(d2)
    return K * math.exp(-R * T) * cdf(-d2) - S * cdf(-d1)


def bs_delta(S, K, T, sig, typ):
    srt = sig * math.sqrt(T)
    d1 = (math.log(S / K) + (R + 0.5 * sig * sig) * T) / srt
    return cdf(d1) if typ == "call" else cdf(d1) - 1.0


# Zulaessiger IV-Bereich. EINE Quelle fuer Bisektions-Bracket UND die
# Plausibilitaetspruefung der Aufrufer: vorher klammerte die Bisektion bis 5,0,
# die Aufrufer verwarfen aber ab 4,0 — alles dazwischen wurde berechnet und dann
# weggeworfen. Reiner Datenverlust, der genau die High-Vol-Titel trifft
# (Earnings, Biotech-Events), deren Skew am interessantesten ist.
IV_MIN, IV_MAX = 0.01, 5.0


def implied_vol(price, S, K, T, typ):
    """IV per Bisektion; None wenn kein Root (z.B. Preis = reiner innerer Wert
    oder echte IV oberhalb IV_MAX — dann liegt die Nullstelle ausserhalb des
    Brackets und beide Randwerte haben dasselbe Vorzeichen)."""
    if price is None or price <= 0 or T <= 0:
        return None
    lo, hi = 1e-4, IV_MAX
    plo = bs_price(S, K, T, lo, typ) - price
    phi = bs_price(S, K, T, hi, typ) - price
    if plo * phi > 0:
        return None
    for _ in range(64):
        mid = 0.5 * (lo + hi)
        pm = bs_price(S, K, T, mid, typ) - price
        if abs(pm) < 1e-6:
            return mid
        if plo * pm < 0:
            hi = mid
        else:
            lo, plo = mid, pm
    return 0.5 * (lo + hi)

# ── Konstante Laufzeit (Constant Maturity) ───────────────────────────────────
# Diese Parameter MUESSEN auf beiden Seiten identisch sein (Backfill + Live),
# sonst driften die Reihen wieder auseinander — dieselbe Klasse Fehler, die die
# BS-Vereinheitlichung oben beseitigt hat. Deshalb hier zentral, nicht als
# Kopie je Skript.
CM_DAYS = 30              # Ziel-Laufzeit der Reihe
CM_DTE_MIN, CM_DTE_MAX = 7, 75   # zulaessige Spanne fuer Stuetzstellen
CM_SINGLE_TOL = 10        # nur EINE Stuetzstelle: max. Abstand zu CM_DAYS
DELTA_TOL = 0.08          # max. Abweichung vom Ziel-Delta, sonst unbrauchbar
# Volumen-Perzentilfilter. ABGESCHALTET seit 2026-09-11 — er war das falsche
# Kriterium und hat den Radar messbar verdorben.
#
# Gedacht war er gegen veraltete Prints. Volumen misst aber AKTIVITAET, nicht
# PREISQUALITAET. Belegt an SOXX (Expiry 2026-10-16, 35 DTE): der Cutoff lag bei
# Volumen 2, also zwischen "ein Kontrakt gehandelt" und "zwei". Er verwarf damit
#   K=570, Volumen 1, IV 0.3930, Delta-Abstand 0.008
# zugunsten von
#   K=585, Volumen 2, IV 0.4759, Delta-Abstand 0.017
# K=570 war NACHWEISLICH korrekt (Anbieter-IV 0.3896, Abweichung 0.0034), K=585
# ragt aus dem Smile (570->0.393, 575->0.388, 585->0.476). Der Skew kippte
# dadurch von +1.79 auf -6.50. Im veroeffentlichten Stand hatten 21 % der Ticker
# die 25d-Put-IV UNTER der ATM-IV — bei Aktien praktisch ausgeschlossen.
#
# Der Ersatz ist NICHT ein anderer Schwellwert, sondern ein anderes Kriterium:
# Abweichung vom geglaetteten Smile der Nachbarstrikes (Leave-one-out, sonst
# versteckt der Ausreisser sein eigenes Residuum). Siehe docs/OPTIONS.md.
# Bis dahin: kein Filter. Die stabile Historie ist mit 0.0 entstanden.
VOL_PCTL = 0.0


def cm_interp(v1, t1, v2, t2, t_target=CM_DAYS):
    """IV auf konstante Laufzeit interpolieren — linear in der TOTALEN VARIANZ.

    Linear in sigma^2*T (nicht in sigma), weil sich Varianz ueber die Zeit
    addiert; das ist dieselbe Interpolation, die der VIX fuer seine 30-Tage-
    Konstante nutzt. Linear in sigma laege bis zu 3 Vol-Punkte daneben.

    Ohne diesen Schritt misst die Reihe die Position im Verfallszyklus statt den
    Skew: die Laufzeit laeuft von ~46 Tagen auf ~10 herunter und springt beim
    Roll zurueck, die IV folgt der Term-Struktur mit."""
    if v1 is None or v2 is None or t1 is None or t2 is None or t1 == t2:
        return None
    if t1 > t2:
        v1, t1, v2, t2 = v2, t2, v1, t1
    w1, w2 = v1 * v1 * t1, v2 * v2 * t2
    var = w1 + (w2 - w1) * (t_target - t1) / (t2 - t1)
    if var <= 0 or t_target <= 0:
        return None
    return round(math.sqrt(var / t_target), 4)

# ── 25Δ-Leg aus Rohpreisen — EINE Implementierung fuer Live und Backfill ──────
ATM_MAX_MONEYNESS = 0.05   # naechster Strike weiter als 5 % vom Forward -> kein Anker
PARITAET_TOL = 0.03        # max. IV-Differenz Call vs Put am GLEICHEN Strike
# Wie weit darf die ATM-IV die Fluegel ueberragen, bevor die Leg unbrauchbar ist?
# GEMESSEN am 2026-09-19 an 33 Tickern mit SYNCHRONER Kursreihe (also ohne den
# Spot-Fehler), Verteilung von iv_atm - max(call_iv, put_iv) in Vol-Punkten:
#   Median -1.78 | 75. Perz. -0.44 | 90. +0.60 | 95. +1.83 | max +7.41
# Der Normalfall ist also NEGATIV (konvexer Smile, ATM ist sein Minimum).
# Kleine positive Werte sind legitim: die 25Delta-Fluegel liegen nicht symmetrisch
# um ATM, und Event-Risiko oder breite Quotes heben das Geld an. No-Arbitrage
# erzwingt PREIS-Konvexitaet, nicht IV-Konvexitaet — das hier ist also KEINE
# harte Invariante, sondern eine Ausreisser-Grenze.
# 3.0 liegt jenseits des 95. Perzentils der gesunden Verteilung und haette den
# groben Fall vom 2026-09-18 gefangen (NVDA +5.06 Punkte bei veraltetem Spot),
# ohne die vier gesunden Ticker zwischen +0.4 und +1.8 zu verwerfen.
ATM_KONKAV_TOL = 0.03
PARITAET_BAND = 0.08       # nur hier pruefen: |log(K/F)| <= 8 % (amerikanische
                           # Ausuebung verletzt die Paritaet weiter im Geld legitim)


def forward(spot: float, T: float, r: float = R) -> float:
    """Forward-Preis. Der ATM-Anker gehoert an den FORWARD, nicht an den Spot:
    bei q=0 und r>0 ist K=F=S*exp(rT) der konsistente Punkt. Bei 30 Tagen sind
    das nur ~0,37 %, was bei dichtem Strike-Raster aber den gewaehlten Strike
    aendern kann — deshalb auf beiden Seiten identisch."""
    return spot * math.exp(r * T)


_OCC = re.compile(r"^O:([A-Z]+\d*)\d{6}[CP]\d{8}$")


def standardserie_filter(contracts, underlying: str, ticker_feld=None):
    """Angepasste Optionsserien aus einer Kette entfernen.

    Nach einer Kapitalmassnahme (Sonderdividende, Spin-off, Split mit Baranteil)
    entsteht eine ANGEPASSTE Serie mit abweichendem Lieferumfang. Sie traegt
    dieselbe Expiry und denselben Strike, aber eine Wurzel mit Ziffernsuffix:
    `SPGI1` neben `SPGI`. Ihr Preis gehoert NICHT zum normalen Spot.

    Gemessen am 2026-09-11: SPGIs Kette enthielt 350 `SPGI1`-Kontrakte neben
    904 regulaeren. Jeder Strike kam doppelt vor, mit voellig verschiedenen
    Preisen (K=450: 21.40 und 3.00). Die Anbieter-IV passte jeweils zum
    regulaeren. Unser 25Δ-Call landete auf der angepassten Serie und wies 92 %
    IV neben 28,5 % ATM aus.

    UMGANG MIT UNBEKANNTEM FORMAT — bewusst weder stur fail-open noch
    fail-closed, sondern nach Befundlage:
      * Passt KEIN Kontrakt der Kette auf das OCC-Muster, ist das Format
        insgesamt anders (andere Quelle, Index-Konvention). Dann wird NICHT
        gefiltert — sonst verschwindet der Ticker still und vollstaendig.
      * Passen WELCHE, ist das Muster gueltig. Dann fliegt alles raus, was nicht
        auf die eigene Wurzel passt — auch Unlesbares. Ein einzelner Kontrakt
        mit kaputtem Symbol ist genau der stille Datenfehler, den wir suchen.
    """
    hol = ticker_feld or (lambda c: (c.get("details") or {}).get("ticker", ""))
    passend = [(c, _OCC.match(hol(c) or "")) for c in contracts]
    if not any(m for _, m in passend):
        return list(contracts), 0          # Format unbekannt -> nicht filtern
    wurzel = (underlying or "").upper()
    behalten = [c for c, m in passend if m and m.group(1) == wurzel]
    return behalten, len(contracts) - len(behalten)


# ── Diagnose: warum wurde eine Leg verworfen? ────────────────────────────────
# Standardmaessig AUS. Ohne diese Zaehler sieht man nur das Ergebnis (`single`,
# `None`) und nicht den Grund — genau deshalb wurde am 2026-09-15..18 zwei Tage
# lang OPEX verdaechtigt, waehrend die Ursache ein veralteter Spot war.
# Das Verhalten der Funktionen aendert sich dadurch NICHT.

_diag: dict | None = None


def diagnose_start() -> None:
    """Zaehlung einschalten und zuruecksetzen."""
    global _diag
    _diag = {}


def diagnose_stop() -> dict:
    """Zaehlung ausschalten und Ergebnis liefern."""
    global _diag
    d = _diag or {}
    _diag = None
    return d


def _zaehl(grund: str, n: int = 1) -> None:
    if _diag is not None:
        _diag[grund] = _diag.get(grund, 0) + n


SMILE_MIN_NACHBARN = 3     # weniger -> nicht filtern, sondern unbewertbar lassen
SMILE_TOL = 0.08           # max. Abweichung vom Nachbar-Fit, in Vol-Punkten


def _smile_ausreisser(punkte, tol: float = SMILE_TOL,
                      min_n: int = SMILE_MIN_NACHBARN) -> set:
    """Indizes von Kontrakten, deren IV nicht zu ihren Nachbarn passt.

    LEAVE-ONE-OUT: der Referenzfit wird OHNE den geprueften Kontrakt gebildet.
    Sonst zieht ein Ausreisser die Kurve zu sich und versteckt sein eigenes
    Residuum — er wuerde sich selbst freisprechen.

    Der Smile ist glatt in log-Moneyness, also genuegt eine Gerade durch die
    naechsten Nachbarn derselben Seite. Bei zu wenigen Nachbarn wird NICHT
    gefiltert: dann ist die Lage unbewertbar, und Raten waere schlimmer als
    Nichtstun.

    Warum es das braucht: der Zweipass repariert die AUSWAHL des Strikes, nicht
    die QUALITAET seines Preises. SPGI zeigte am 2026-09-11 einen 25Δ-Call mit
    92 % IV neben einer ATM-IV von 28,5 % — Strike richtig, Preis unbrauchbar.
    """
    raus = set()
    punkte = sorted(punkte, key=lambda p: p[1])          # nach Strike
    n = len(punkte)
    for i, (_, K, iv) in enumerate(punkte):
        lo, hi = max(0, i - 2), min(n, i + 3)
        nachbarn = [p for j, p in enumerate(punkte[lo:hi], start=lo) if j != i]
        if len(nachbarn) < min_n:
            continue                                     # unbewertbar, nicht filtern
        xs = [math.log(p[1]) for p in nachbarn]
        ys = [p[2] for p in nachbarn]
        mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
        nen = sum((x - mx) ** 2 for x in xs)
        steig = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / nen if nen else 0.0
        erwartet = my + steig * (math.log(K) - mx)
        if abs(iv - erwartet) > tol:
            raus.add(i)
    return {punkte[i][1:] for i in raus}                 # {(K, iv)}


def _waehle_delta(gueltig, spot: float, T: float, iv_atm: float, ziel: float) -> dict:
    """Je Seite den Kontrakt, dessen Delta — mit der EINEN Referenz-IV gerechnet —
    am naechsten an `ziel` liegt. Rueckgabe {"call"|"put": (abstand, iv, K) | None}.

    Aus Schritt 5 von leg_from_prices herausgezogen (2026-09-25), damit
    leg_from_prices, smile_from_prices und die Tick-Unsicherheit DENSELBEN
    Kontrakt waehlen. Schleifenreihenfolge und striktes "<" sind unveraendert —
    bei Gleichstand gewinnt wie bisher der zuerst gefundene."""
    best = {"call": None, "put": None}
    for typ, K, iv in gueltig:
        d = abs(abs(bs_delta(spot, K, T, iv_atm, typ)) - ziel)
        if best[typ] is None or d < best[typ][0]:
            best[typ] = (d, iv, K)
    return best


def bs_vega(S, K, T, sig):
    """Preisaenderung je 1,0 Volatilitaet (nicht je Vol-Punkt)."""
    if T <= 0 or sig <= 0:
        return 0.0
    srt = sig * math.sqrt(T)
    d1 = (math.log(S / K) + (R + 0.5 * sig * sig) * T) / srt
    return S * math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi) * math.sqrt(T)


def beobachtetes_raster(px: float) -> float:
    """Das GROEBSTE Kursraster, auf dem der beobachtete Preis entstanden sein kann.

    Cboe (Rule 5.4): Klassen im Penny-Programm handeln unter 3 $ in 0,01, ab 3 $
    in 0,05; alle anderen unter 3 $ in 0,05, ab 3 $ in 0,10. Welche Klasse ein
    Kontrakt hat, liefert der Anbieter nicht, und aus den Kursen laesst es sich
    nicht sauber ablesen: gemessen am 2026-09-24 lag der Anteil nicht-nickliger
    Preise unter 3 $ bei Penny-Titeln bei 0,68-0,84, bei HCA, BKNG, SO, TMO,
    RSP und XLC aber zwischen 0,20 und 0,48 — dazwischen, nicht bei null.
    Deshalb je KONTRAKT das groebste mit seinem Preis vereinbare Raster:
    0,38 kann nur auf 0,01 entstanden sein, 0,35 auch auf 0,05, 3,40 auch auf
    0,10. Beweisbar konservativ, ohne die Klasse zu kennen (Codex-Review
    2026-09-25: "ein Cent ist keine allgemeingueltige Tickgroesse")."""
    cents = round(px * 100)
    if cents % 5:
        return 0.01
    if px >= 3 and cents % 10 == 0:
        return 0.10
    return 0.05


def skew_intervall_pts(cands, spot: float, dte: int, _punkte=None):
    """Exakter Bereich des 25d-Skews (Put-IV − Call-IV, in Vol-Punkten), wenn
    jeder der beiden gewaehlten Preise um ein halbes Raster falsch sein kann.

    Ersetzt die lineare Naeherung "halber Tick / Vega": kurz vor Verfall ist
    der Zusammenhang Preis -> IV stark gekruemmt. Codex konstruierte einen Fall
    mit Skew −0,698 und Naeherung U = 0,699 — "richtungsfest" —, dessen exakt
    invertiertes Intervall aber [−1,398; +0,001] war und die Null enthielt.
    Hier werden die Grenzpreise direkt invertiert:
        min = IV_put(p − h_p) − IV_call(c + h_c)
        max = IV_put(p + h_p) − IV_call(c − h_c)
    Rueckgabe {"lo", "hi", "raster_put", "raster_call"} UNGERUNDET, oder None,
    wenn keine 25d-Leg waehlbar ist. Ist eine Grenze nicht invertierbar (Preis
    minus halbes Raster unter dem inneren Wert), ist sie offen (−inf/+inf) —
    die Richtung ist dann nicht belegbar."""
    g = _punkte if _punkte is not None else _gefilterte_punkte(cands, spot, dte)
    if g is None:
        return None
    gueltig, iv_atm, T, _klammer = g
    wahl = _waehle_delta(gueltig, spot, T, iv_atm, 0.25)
    if not wahl["call"] or not wahl["put"]:
        return None
    preis = {}
    for c in (cands or []):
        preis.setdefault((c["typ"], c["K"]), c["px"])
    grenzen = {}
    for typ in ("call", "put"):
        _d, iv, K = wahl[typ]
        # Der beobachtete Preis; fehlt die Kette (Aufruf nur mit _punkte), wird
        # er aus der eigenen IV rekonstruiert — die Bisektion trifft ihn auf
        # ~1e-6, der Cent-Wert ist damit eindeutig.
        px = preis.get((typ, K))
        if px is None:
            px = round(bs_price(spot, K, T, iv, typ), 2)
        h = beobachtetes_raster(px) / 2.0
        unten = implied_vol(px - h, spot, K, T, typ) if px - h > 0 else None
        oben = implied_vol(px + h, spot, K, T, typ)
        grenzen[typ] = (unten, oben, beobachtetes_raster(px))
    pu, po, rp = grenzen["put"]
    cu, co, rc = grenzen["call"]
    inf = float("inf")
    lo = (pu - co) * 100.0 if (pu is not None and co is not None) else -inf
    hi = (po - cu) * 100.0 if (po is not None and cu is not None) else inf
    return {"lo": lo, "hi": hi, "raster_put": rp, "raster_call": rc}


def _gefilterte_punkte(cands, spot: float, dte: int):
    """Schritte 1-4 von `leg_from_prices`: IV-Inversion, Smile-Ausreisser,
    Paritaet im ATM-Band, ATM ueber Moneyness am Forward.

    Liefert `(punkte, iv_atm, T)` mit punkte = [(typ, K, iv), ...] nach allen
    Filtern, oder None. Herausgezogen (2026-09-25), damit Term-Struktur und
    Smile-Kurve DIESELBE Filterkette nutzen wie der 25d-Skew statt einer
    Kopie. Der Code ist woertlich aus `leg_from_prices` verschoben; deren
    Ergebnis ist unveraendert (Nachweis in scripts/verify_skew_anzeige.py)."""
    if not cands or not spot or dte <= 0:
        return None
    T = dte / 365.0
    F = forward(spot, T)

    # Schritt 1: IV je Kontrakt invertieren.
    gueltig = []
    for c in cands:
        iv = implied_vol(c["px"], spot, c["K"], T, c["typ"])
        if iv is None or iv <= IV_MIN or iv > IV_MAX:
            _zaehl("iv_unbrauchbar")
            continue
        gueltig.append((c["typ"], c["K"], iv))
    if not gueltig:
        return None

    # Schritt 2: Smile-Ausreisser ZUERST entfernen — VOR der ATM-Berechnung.
    # Sonst vergiftet ein verdorbener Kontrakt nahe dem Forward den Anker, und
    # der spaetere Filter korrigiert ihn nicht mehr.
    verdaechtig = set()
    for seite in ("call", "put"):
        verdaechtig |= _smile_ausreisser([p for p in gueltig if p[0] == seite])
    _zaehl("smile_ausreisser", len(verdaechtig))
    gueltig = [p for p in gueltig if (p[1], p[2]) not in verdaechtig]
    if not gueltig:
        _zaehl("leg_None_kein_kandidat_nach_smile")
        return None

    # Schritt 3: Paritaetspruefung — NUR in der ATM-Region.
    #
    # Call und Put mit gleichem Strike muessen nach Put-Call-Paritaet dieselbe
    # IV haben. Das gilt allerdings fuer EUROPAEISCHE Ausuebung; unsere
    # Kontrakte sind amerikanisch, und der Fruehausuebungswert eines Puts kann
    # die Paritaet legitim verletzen. Nahe dem Forward ist dieser Aufschlag bei
    # 30 Tagen und q=0 vernachlaessigbar — weiter im Geld nicht. Deshalb wird
    # nur dort geprueft, wo der ATM-Anker herkommt.
    #
    # Ohne die Pruefung vergiftete eine verdorbene Seite den Anker: SPY wies am
    # 2026-09-11 (call 0.12 + put 0.65)/2 = 0.385 aus, realistisch ~0.13.
    je_strike: dict[float, dict] = {}
    for typ, K, iv in gueltig:
        if abs(math.log(K / F)) <= PARITAET_BAND:
            je_strike.setdefault(K, {})[typ] = iv

    anker = {}
    for K, d in je_strike.items():
        ca, pu = d.get("call"), d.get("put")
        if ca is not None and pu is not None:
            if abs(ca - pu) > PARITAET_TOL:
                _zaehl("paritaet_bruch")
                continue                  # ein Preis taugt nicht -> Strike raus
            anker[K] = (ca + pu) / 2
        else:
            anker[K] = ca if ca is not None else pu
    if not anker:
        _zaehl("leg_None_kein_atm_anker")
        return None

    # Schritt 4: ATM-IV ueber MONEYNESS am Forward, zwischen den zwei Strikes
    # um F interpoliert. Kein Delta-basierter Pick — eine zu hohe IV zoege das
    # Delta jedes Strikes Richtung 0,50.
    strikes = sorted(anker)
    unten = [k for k in strikes if k <= F]
    oben = [k for k in strikes if k > F]
    if unten and oben:
        k1, k2 = unten[-1], oben[0]
        v1, v2 = anker[k1], anker[k2]
        m1, m2 = math.log(k1 / F), math.log(k2 / F)
        iv_atm = v1 if m1 == m2 else v1 + (v2 - v1) * (0.0 - m1) / (m2 - m1)
    else:
        k = unten[-1] if unten else oben[0]
        if abs(math.log(k / F)) > ATM_MAX_MONEYNESS:
            _zaehl("leg_None_kette_ohne_forward")
            return None                   # Kette deckt den Forward nicht ab
        iv_atm = anker[k]
    if not iv_atm or iv_atm <= IV_MIN or iv_atm > IV_MAX:
        _zaehl("leg_None_atm_ausserhalb_band")
        return None

    # Klammer-Information fuer Aufrufer, die KEINE Fluegel verlangen
    # (atm_from_prices). leg_from_prices ignoriert sie — ihr Verhalten bleibt.
    if unten and oben:
        klammer = {"beidseitig": True,
                   "max_abstand": max(abs(math.log(unten[-1] / F)), abs(math.log(oben[0] / F)))}
    else:
        kk = unten[-1] if unten else oben[0]
        klammer = {"beidseitig": False, "max_abstand": abs(math.log(kk / F))}
    return gueltig, iv_atm, T, klammer


def leg_from_prices(cands, spot: float, dte: int, delta_tol: float = DELTA_TOL):
    """25Δ-Call-/Put-IV + ATM-IV EINER Expiry aus Rohpreisen.

    cands: [{"typ": "call"|"put", "K": float, "px": float}]

    WARUM ZWEI DURCHGAENGE. Frueher wurde je Kontrakt die IV aus dem Preis
    invertiert und das Delta DANN aus genau dieser IV berechnet. Ein schlechter
    Preis erzeugte damit beides: die falsche IV UND das Delta, das den Kontrakt
    wie den gesuchten Strike aussehen liess. `delta_tol` prueft gegen dieselbe
    verdorbene Groesse und kann es nicht fangen.

    Am ATM-Pick war das am schlimmsten: eine zu hohe IV zieht das Delta JEDES
    Strikes Richtung 0,50, also gewann ein weit aus dem Geld liegender Kontrakt
    mit veraltetem Preis — und brachte seine falsche IV als "ATM-IV" mit.
    Gemessen am 2026-09-11: SPY ATM 38 % statt ~13 %, SPGI 43 % ueber beiden
    Fluegeln, HON gar keine.

    Deshalb:
      1. ATM ueber MONEYNESS bestimmen (preisunabhaengig), IV zwischen den zwei
         gueltigen Strikes um F interpolieren.
      2. ALLE Deltas mit dieser EINEN Referenz-IV rechnen und den 25Δ-Kontrakt
         waehlen. Der gemeldete Wert ist dann dessen EIGENE IV — die Auswahl ist
         stabil, die Messung bleibt die des Kontrakts.

    Ohne gueltigen ATM-Anker gibt es KEINEN Rueckfall auf einen Fluegel oder auf
    0: die Expiry ist unbewertbar und faellt aus der Rangreihe.
    """
    g = _gefilterte_punkte(cands, spot, dte)
    if g is None:
        return None
    gueltig, iv_atm, T, _klammer = g

    # Schritt 5: Deltas mit der EINEN Referenz-IV — nicht mit der je Kontrakt.
    # Der gemeldete Wert ist dann die EIGENE IV des gewaehlten Kontrakts: die
    # Auswahl ist stabil, die Messung bleibt die des Kontrakts.
    best = _waehle_delta(gueltig, spot, T, iv_atm, 0.25)
    call, put = best["call"], best["put"]
    if not call or not put:
        _zaehl("leg_None_seite_fehlt")
        return None
    if call[0] > delta_tol or put[0] > delta_tol:
        _zaehl("leg_None_delta_toleranz")
        return None

    # INVARIANTE: die ATM-IV darf nicht ueber BEIDEN Fluegeln liegen.
    # Der Smile ist am Geld konvex — ATM ist sein Minimum, die Fluegel liegen
    # darueber (reiner Skew) oder gleichauf. Liegt ATM ueber beiden, ist der
    # Smile am Geld konkav: kein Marktzustand, sondern ein Messfehler.
    # Gemessen am 2026-09-15..18: 14-21 % der Zeilen hatten das, ausgeloest durch
    # einen um eine Session veralteten Spot (NVDA iv_atm 0.4201 gegen call 0.3695
    # und put 0.2869). Die Toleranz laesst Messrauschen bei liquiden Titeln durch,
    # ohne die grossen Faelle zu verpassen.
    if iv_atm > max(call[1], put[1]) + ATM_KONKAV_TOL:
        _zaehl("leg_None_atm_konkav")
        return None
    return {"dte": dte, "call_iv": call[1], "put_iv": put[1],
            "iv_atm": round(iv_atm, 4)}


ATM_MAX_SIGMA = 0.5        # nur atm_from_prices: max. Ankerabstand in sigma*sqrt(T)


def atm_from_prices(cands, spot: float, dte: int, _punkte=None):
    """ATM-IV EINER Expiry aus Rohpreisen — ohne Fluegelzwang.

    Fuer die Term-Struktur. `leg_from_prices` verwirft eine Expiry, wenn einer
    der beiden 25d-Fluegel fehlt, auch wenn der ATM-Anker sauber ist; gemessen
    am 2026-09-24 fehlten dadurch 42 von 237 Term-Punkten. Dieselbe
    Filterkette (Inversion, Smile, Paritaet, Moneyness am Forward) — nur ohne
    Schritt 5."""
    g = _punkte if _punkte is not None else _gefilterte_punkte(cands, spot, dte)
    if g is None:
        return None
    # Ersatz-Schutz fuer den fehlenden Fluegel-Check (Codex-Entwurfspruefung
    # 2026-09-25): leg_from_prices faengt einen falschen Anker ueber die
    # Konkav-Invariante (ATM ueber beiden Fluegeln). Ohne Fluegel geht das
    # nicht. Deshalb hier strenger als dort: der Anker muss BEIDSEITIG um den
    # Forward geklammert sein, und keiner der beiden Strikes darf weiter als
    # ATM_MAX_MONEYNESS vom Forward liegen. Einseitige Anker (bis 5 % entfernt,
    # in leg_from_prices erlaubt) sind hier nicht zulaessig.
    # Abstand in STANDARDABWEICHUNGEN statt in Prozent: 5 % sind bei 7 Tagen
    # fast zwei Sigma (kein ATM mehr), bei 180 Tagen ein Bruchteil davon.
    # Gemessen am 2026-09-24 auf 239 Term-Punkten (40 Ticker): Median z = 0,11,
    # 90. Perzentil 0,49; die Ausreisser sind kurze Laufzeiten mit weit
    # auseinanderliegenden Ankern (XLU 8 T. z = 1,66, KO 8 T. z = 2,05).
    # Eine erste Fassung verlangte "beidseitig und <= 5 %" — das liess genau
    # diese durch und verwarf dafuer einseitige, nahe Anker bei langen
    # Laufzeiten (ARM 57/85/176 T.).
    klammer = g[3]
    iv_atm, T = g[1], g[2]
    z = klammer["max_abstand"] / (iv_atm * math.sqrt(T))
    if klammer["max_abstand"] > ATM_MAX_MONEYNESS or z > ATM_MAX_SIGMA:
        _zaehl("atm_None_klammer_zu_weit")
        return None
    return round(iv_atm, 4)


SMILE_DELTAS = (0.10, 0.25, 0.40)
# Halber Abstand zwischen den Ziel-Deltas ist 0,075. Mit DELTA_TOL = 0,08
# ueberlappten sich die Fenster (10d: 0,02-0,18 / 25d: 0,17-0,33), und
# derselbe Kontrakt haette zwei Kurvenpunkte bedienen koennen (Codex-
# Entwurfspruefung). 0,07 haelt sie disjunkt. Die 25d-Leg des Rankings
# behaelt DELTA_TOL — sie waehlt nur EINEN Punkt je Seite.
SMILE_DELTA_TOL = 0.07


def smile_from_prices(cands, spot: float, dte: int, deltas=SMILE_DELTAS,
                      delta_tol: float = SMILE_DELTA_TOL, _punkte=None):
    """IV je Delta EINER Expiry aus Rohpreisen, Auswahl ueber das REFERENZ-Delta.

    Wie Schritt 5 in `leg_from_prices`: alle Deltas mit der EINEN ATM-IV
    rechnen, den naechstliegenden Kontrakt waehlen, dessen EIGENE IV melden.
    So kann ein falsch bepreister Kontrakt sich nicht selbst in einen
    Delta-Punkt waehlen (das tat der alte Anbieter-Picker: SO-Call K=95 zu
    0,10 $ bei 15 % aus dem Geld als "25d").

    Rueckgabe: {"dte", "iv_atm", "put": {d: iv|None}, "call": {d: iv|None}}.
    Ein Punkt ohne Kontrakt innerhalb `delta_tol` ist None — kein Rueckfall."""
    g = _punkte if _punkte is not None else _gefilterte_punkte(cands, spot, dte)
    if g is None:
        return None
    gueltig, iv_atm, T, _klammer = g
    out = {"dte": dte, "iv_atm": round(iv_atm, 4), "put": {}, "call": {}}
    for ziel in deltas:
        wahl = _waehle_delta(gueltig, spot, T, iv_atm, ziel)
        for typ in ("put", "call"):
            best = wahl[typ]
            out[typ][ziel] = best[1] if (best and best[0] <= delta_tol) else None
    return out


# ── Stuetzstellen-Wahl fuer die konstante Laufzeit ───────────────────────────

def _ist_freitag(iso: str) -> bool:
    try:
        return _date.fromisoformat(iso).weekday() == 4
    except Exception:
        return False


def ist_monatsverfall(iso: str) -> bool:
    """Standard-Monatsverfall = 3. Freitag (Tag 15-21 und ein Freitag)."""
    try:
        d = _date.fromisoformat(iso)
    except Exception:
        return False
    return d.weekday() == 4 and 15 <= d.day <= 21


def cm_leg_kandidaten(dte_je_expiry: dict) -> list:
    """Rangliste von Stuetzstellen-Gruppen fuer die 30-Tage-Interpolation.

    Eingabe: {expiry_iso: dte}. Rueckgabe: Liste von Gruppen, beste zuerst, je
    {"exps": [1-2 Expiry-Schluessel], "pool": monatlich|freitags|alle,
     "art": klammer|extrap_ab|extrap_auf|einzel, "rang": int}.
    Der Aufrufer probiert sie der Reihe nach, bis eine zwei brauchbare Legs
    liefert, und schreibt die Herkunft in die Ergebniszeile.

    ZWEI FEHLER DER VORGAENGERVERSION, beide am 2026-09-18 gemessen:

    1. DER POOL WURDE GEWAEHLT, BEVOR KLAR WAR, OB ER KLAMMERN KANN.
       Sobald irgendein Monatsverfall existierte, wurden Wochenverfaelle NIE
       betrachtet. Am 2026-09-15 lagen die Monatsverfaelle bei 3 Tagen (unter
       CM_DTE_MIN) und 31 Tagen — `below` war also leer, eine echte Klammer um
       30 Tage unmoeglich. Die Wochenverfaelle bei 10, 17 und 24 Tagen haetten
       eine geliefert, kamen aber nicht in Frage.
       Folge: statt zu interpolieren wurde von 31 auf 30 Tage EXTRAPOLIERT,
       mit der 66-Tage-Stuetzstelle als zweitem Punkt.
       Das wiederholt sich JEDEN MONAT im Fenster zwischen "Front-Verfall unter
       CM_DTE_MIN" und dem Verfall selbst.

    2. EINE GESCHEITERTE LEG LIESS DEN GANZEN TAG FALLEN.
       Die 66-Tage-Stuetzstelle ist duenn; `leg_from_prices` verwarf sie. Damit
       blieb eine Leg uebrig -> `cm_mode = "single"`, und `single` zaehlt im
       Frontend nicht fuer das Ranking. Gemessen: die Normierungsquote fiel von
       77-100 % auf 38-56 %, und damit von 148 auf 19 Ticker im Radar.

    Deshalb jetzt: erst in JEDEM Pool nach einer echten Klammer suchen
    (Monatsverfall bevorzugt, weil dort die Liquiditaet sitzt), und erst wenn
    kein Pool klammern kann, extrapolieren. Und als Rangliste, damit eine
    gescheiterte Leg nur die naechste Gruppe kostet, nicht den Tag.
    """
    if not dte_je_expiry:
        return []
    alle = list(dte_je_expiry)
    monatlich = [e for e in alle if ist_monatsverfall(e)]
    freitags = [e for e in alle if _ist_freitag(e)]

    def _spalten(pool):
        unten = sorted([e for e in pool if CM_DTE_MIN <= dte_je_expiry[e] <= CM_DAYS],
                       key=lambda e: dte_je_expiry[e])
        oben = sorted([e for e in pool if CM_DAYS < dte_je_expiry[e] <= CM_DTE_MAX],
                      key=lambda e: dte_je_expiry[e])
        return unten, oben

    gruppen, gesehen = [], set()

    def _nimm(gruppe, pool_name, art):
        """Jede Gruppe traegt ihre HERKUNFT mit: aus welchem Pool sie kommt und
        ob sie klammert, extrapoliert oder ein Einzelpunkt ist.

        Ohne das laesst sich ein spaeterer Percentile-Sprung nicht erklaeren —
        derselbe Ticker kann heute aus dem Monatsverfall und morgen aus einem
        Wochenverfall kommen, und beides sieht im Ergebnis gleich aus."""
        s = tuple(gruppe)
        if gruppe and s not in gesehen:
            gesehen.add(s)
            gruppen.append({"exps": list(gruppe), "pool": pool_name, "art": art,
                            "rang": len(gruppen)})

    # Stufe 1: echte Klammer, Pools in Liquiditaets-Reihenfolge.
    # Eine Interpolation zwischen zwei WIRKLICH klammernden Wochenverfaellen ist
    # belastbarer als eine Extrapolation von 31 auf 30 Tage ueber eine 66-Tage-
    # Stuetzstelle — auch wenn Wochenverfaelle weniger liquide sind.
    for pool_name, pool in (("monatlich", monatlich), ("freitags", freitags), ("alle", alle)):
        unten, oben = _spalten(pool)
        if unten and oben:
            _nimm([unten[-1], oben[0]], pool_name, "klammer")

    # Stufe 2: keine Klammer moeglich -> extrapolieren, wieder pool-weise.
    for pool_name, pool in (("monatlich", monatlich), ("freitags", freitags), ("alle", alle)):
        unten, oben = _spalten(pool)
        if len(oben) >= 2:
            _nimm([oben[0], oben[1]], pool_name, "extrap_ab")   # nach unten (vor dem Roll)
        if len(unten) >= 2:
            _nimm([unten[-2], unten[-1]], pool_name, "extrap_auf")  # nach oben (selten)

    # Stufe 3: Einzelpunkt. Die Laufzeit-Toleranz prueft der Aufrufer.
    for pool_name, pool in (("monatlich", monatlich), ("freitags", freitags), ("alle", alle)):
        unten, oben = _spalten(pool)
        if oben:
            _nimm([oben[0]], pool_name, "einzel")
        if unten:
            _nimm([unten[-1]], pool_name, "einzel")

    return gruppen
