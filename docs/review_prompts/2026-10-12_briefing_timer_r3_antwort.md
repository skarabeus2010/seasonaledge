# Daily Briefing auf systemd-Timer — Codex-Antwort Runde 3

**Urteil:** keine Freigabe. Fristprüfung und Journalfehler-Abbruch sind verbessert; zwei Doppelversandpfade bleiben offen.

**Befunde**

- **P1 – Netzwerkfehler gelten fälschlich als sichere Ablehnung:** [shared/email_brevo.py:180](/C:/dev/SeasonalEdge/shared/email_brevo.py:180) liefert bei `RequestException` auch nach möglicher Annahme `False`; [scripts/daily_newsletter.py:315](/C:/dev/SeasonalEdge/scripts/daily_newsletter.py:315) schreibt deshalb `-`. Gegenprobe mit simulierter Annahme und anschließendem Timeout bestätigt dies. Nach einem späteren Laufabbruch darf die Wiederaufnahme denselben Empfänger erneut versenden.
- **P1 – Alte Ablehnung verdeckt neuen ungeklärten Versuch:** [shared/versandsperre.py:100](/C:/dev/SeasonalEdge/shared/versandsperre.py:100) verrechnet Mengen statt chronologischer Zustände. Gegenprobe mit Journalfolge `? → - → ?` ergibt **0 ungeklärte Empfänger** und erlaubt erneuten Versand. Wurde der zweite Versuch angenommen, aber vor `+` beendet, folgt beim dritten Versuch eine doppelte Mail.
- **P2 – Wächter übersieht beide Pfade:** [scripts/verify_briefing_versand.py:135](/C:/dev/SeasonalEdge/scripts/verify_briefing_versand.py:135) ersetzt den Mailadapter vollständig; ab Zeile 241 fehlt ein erneut abgebrochener Wiederaufnahmeversuch nach vorheriger Ablehnung.

**Auflagen**

- Eindeutige Ablehnung und unbekannte Annahme im echten Mailadapter unterscheiden; unbekannte Annahmen bleiben `?`.
- Journal chronologisch auswerten: Ein neuer Versuch muss eine frühere Ablehnung ablösen.
- Beide Gegenproben in Wächter und Mutationstest aufnehmen.

Schreibfrei geprüft: 30/30 Health-/Betriebsprüfungen bestanden; beide Fehler reproduziert. Vollständige Versand-, Linux- und Mutationstests nicht erneut ausgeführt.

