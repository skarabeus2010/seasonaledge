# Tage nach Börsenkalender — Plan P3/P4 v8 (nur Releasebindung)

Runde 7: [Plan v7](2026-10-11_kalender_p3p4_plan_v7.md) · [Antwort](2026-10-11_kalender_p3p4_plan_v7_antwort.md) (2 Befunde).
Alles Übrige aus v7 und früher + A/B/C gilt. Read-only.

<task>Prüfe, ob V9 jetzt als Bauplan freigegeben werden kann.</task>

## 1 Bootstrap (Befund 1)
`methode.js` ist die **einzige** Ausnahme: es definiert zuerst `SA.__release`, `SA.__sperre` und die Methode, prüft
dann am Ende **seine eigene** Kennung (`SA.__release('%%RELEASE%%')` als letzte Zeile). Der Einbindungswächter
kennt genau diese eine Ausnahme namentlich (Datei + Position: letzte statt erste Anweisung); jede andere eigene
JS-Datei muss die Prüfung als erste Anweisung haben.

## 2 Seitenweite, dauerhafte Sperre (Befund 2)
Bei der ersten Abweichung ruft `SA.__release` `SA.__sperre(grund)`:
1. setzt `SA.__gesperrt = true` (nicht rücksetzbar, `Object.defineProperty` mit `writable:false`);
2. ersetzt **den gesamten Dokumentinhalt** (`document.body.replaceChildren(hinweis)`) durch den Hinweis „Seite
   veraltet — wird neu geladen" bzw. beim zweiten Versuch „bitte neu laden" — alle Elemente, in die ein Rechner
   schreiben könnte, existieren danach nicht mehr; Charts werden zuvor über `ApexCharts.exec`-Registrierung
   zerstört;
3. blockiert neue Daten: `SA.kurse.laden` und `SA.supabase.get` lehnen bei `SA.__gesperrt` sofort ab
   (`ReleaseFehler`), `fetch` auf `/landing/` wird nicht mehr angestoßen;
4. startet das einmalige Neuladen (v6).
Laufende und spätere Inline-Rechnungen finden damit weder Daten noch Ausgabeziele; ein Ergebnis kann nicht
erscheinen. Probe (jsdom, echte Seiten, u. a. Backtest-Engine und Dashboard): (a) späte Abweichung während einer
laufenden Rechnung, (b) zweiter Ladeversuch, (c) alt/neu in beiden Richtungen, (d) Pause über das ganze Fenster —
jeweils: kein Rechenergebnis im DOM, kein Chart mit Serien nach der Sperre, keine Kursanfrage nach der Sperre.
Mutationen: Sperre ohne DOM-Ersatz; Lader ohne Sperrprüfung; Bootstrap-Prüfung an erster statt letzter Stelle →
jeweils rot.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 20 Zeilen.
