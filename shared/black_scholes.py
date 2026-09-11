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
    if not cands or not spot or dte <= 0:
        return None
    T = dte / 365.0
    F = forward(spot, T)

    # Schritt 1: IV je Kontrakt invertieren.
    gueltig = []
    for c in cands:
        iv = implied_vol(c["px"], spot, c["K"], T, c["typ"])
        if iv is None or iv <= IV_MIN or iv > IV_MAX:
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
    gueltig = [p for p in gueltig if (p[1], p[2]) not in verdaechtig]
    if not gueltig:
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
                continue                  # ein Preis taugt nicht -> Strike raus
            anker[K] = (ca + pu) / 2
        else:
            anker[K] = ca if ca is not None else pu
    if not anker:
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
            return None                   # Kette deckt den Forward nicht ab
        iv_atm = anker[k]
    if not iv_atm or iv_atm <= IV_MIN or iv_atm > IV_MAX:
        return None

    # Schritt 5: Deltas mit der EINEN Referenz-IV — nicht mit der je Kontrakt.
    # Der gemeldete Wert ist dann die EIGENE IV des gewaehlten Kontrakts: die
    # Auswahl ist stabil, die Messung bleibt die des Kontrakts.
    best = {"call": None, "put": None}
    for typ, K, iv in gueltig:
        d = abs(abs(bs_delta(spot, K, T, iv_atm, typ)) - 0.25)
        if best[typ] is None or d < best[typ][0]:
            best[typ] = (d, iv)
    call, put = best["call"], best["put"]
    if not call or not put or call[0] > delta_tol or put[0] > delta_tol:
        return None
    return {"dte": dte, "call_iv": call[1], "put_iv": put[1],
            "iv_atm": round(iv_atm, 4)}
