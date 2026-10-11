**Urteil:** Mit Änderungen; noch keine Freigabe als Bauvorlage. Der konkrete Analytics-/Tour-Befund aus Runde 4 ist auf Entwurfsebene aufgelöst; die allgemeine Netz-Zusage bleibt unvollständig.

**Befunde**

- **P2 – Attributänderungen umgehen die Einfügehüllen** ([v5:9](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_v1b_entwurf_v5.md:9)). Nach Sperre kann `document.createElement('img').src = url` eine Anfrage auslösen, ohne Einfügung oder HTML-Setter. Der Observer sieht das abgehängte Bild nicht. Das Laden folgt der [`src`-Änderung](https://html.spec.whatwg.org/multipage/images.html#updating-the-image-data). Die Inventarsuche erfasst außerdem bestehende Bild-Zuweisungen wie [auth.js:143](/C:/dev/SeasonalEdge/landing/js/auth.js:143) nicht.
- **P2 – Der Ressourcenzähler kann blind grün bleiben** ([v5:22](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_v1b_entwurf_v5.md:22)). jsdom lädt Bilder [nur mit installiertem `canvas`](https://github.com/jsdom/jsdom#loading-subresources); die vorhandene Testumgebung deklariert ausschließlich jsdom. Ein eigener `ResourceLoader` allein beweist daher keine unterbundene Bildanfrage.

**Auflagen**

- Ressourcenstartende Attribut-/Property-Änderungen synchron sperren und ins Inventar aufnehmen; abgehängte Bilder ausdrücklich prüfen.
- Positive Kontrollen je geprüfter Ressourcenart verlangen: ungesperrt zählt die Anfrage, gesperrt bleibt sie aus; entfernte Hülle macht die benannte Prüfung rot. Bildprobe mit funktionierender Bildunterstützung oder echtem Browser.
- Die übrigen Proben bleiben Voraussetzung der Code-Abnahme. Ausschließlich lesend geprüft; nichts geschrieben.
