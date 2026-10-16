Keine neuen Befunde im R3-Prüfumfang.

1. **Ja, der Rückfall stimmt auch mit aktivem Jahresfilter überein.** [embed.html:123](/C:/dev/SeasonalEdge/landing/embed.html:123) begrenzt die Jahresmenge auf das Seitenfenster, wendet denselben Filter an und mittelt dieselben Jahreskurven wie [jahreszyklus.html:1891](/C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1891).

   Gegenprobe auf den echten Seitenpfaden: `years=10`, IQR, drei Ausreißer, **7/8 vollständige Vorjahre**. Beide zeigen „Saisonaler Ø (8J)“; **alle 365 Kurvenwerte sind identisch**, Tag 101 jeweils **100,91**. Der ausschließlich im Speicher wiederhergestellte alte Rückfall liefert dagegen 12 Jahre und **104,44** an Tag 101 – der Vergleich erkennt den Fehler.

2. **Freigabe für R3.** Alle **48 Seitenprüfungen** bestanden; `git diff --check` unauffällig. Der neue Lückenfall sichert zusätzlich den Rückfall ohne Jahresfilter ab.

Block 8 ließ sich wegen seines benötigten temporären Schreibzugriffs im Nur-Lesen-Modus nicht abschließen. Den Mutationstest habe ich nicht erneut ausgeführt. Keine Dateien geändert.

**FREIGABE (Code): ja**
