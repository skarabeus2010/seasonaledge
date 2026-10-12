# Sicherung der Halbtagsbelege NYSE (V1c-3) — Abruf 2026-10-12

Zweck: der Quellenstand hinter `shared/halbtage_belege.py` bleibt nachprüfbar. Jede Quelle ist eine
**unveränderliche Archivfassung** der amtlichen NYSE-Kalenderseite (bis 2014 nyx.com) bei web.archive.org; die
SHA-256 bezieht sich auf die Bytes der Archivfassung (`id_`-Adresse, ohne Archiv-Rahmen), beim Stand 2026 identisch
mit dem direkten Abruf von nyse.com am 2026-10-12. Übernommen werden nur **Fakten** (Datum; 13:00 ET Aktien-
Kernhandel, Optionen 13:15) — wörtliche Absätze werden bewusst nicht kopiert.

| Kennung | Archivfassung | SHA-256 (Byte) | Jahre | Übernommene Halbtage |
|---|---|---|---|---|
| `NYSE.halbtage_archiv20131129` | https://web.archive.org/web/20131129003407id_/http://www.nyx.com/holidays-and-hours/nyse | `8cec5115e043156ecaf8fb9955524694645e24e583ebfc74243f92731f880fb5` (42317) | Abdeckung 2013, 2014 (Seite listet 2013–2014) | 2013-07-03, 2013-11-29, 2013-12-24, 2014-07-03, 2014-11-28, 2014-12-24 |
| `NYSE.halbtage_archiv20150210` | https://web.archive.org/web/20150210033400id_/https://www.nyse.com/markets/hours-calendars | `edc8799a85cec668ed966f4246a5b0aff133142843047ac9d97f595270e61fb3` (30312) | Abdeckung 2015, 2016 (Seite listet 2015–2016) | 2015-11-27, 2015-12-24, 2016-11-25 |
| `NYSE.halbtage_archiv20160204` | https://web.archive.org/web/20160204112739id_/https://www.nyse.com/markets/hours-calendars | `0af4c54b4ee2f0fcbbd6f738e9db8183b270a01781bb76b6eec2dbd29243534f` (78758) | Abdeckung 2017 (Seite listet 2016–2017) | 2017-07-03, 2017-11-24 |
| `NYSE.halbtage_archiv20170303` | https://web.archive.org/web/20170303135722id_/https://www.nyse.com/markets/hours-calendars | `81e984b95a909a42e01ab9da823894991a1b133a92ec363651fd906ca04afa39` (232865) | Abdeckung 2018, 2019 (Seite listet 2017–2019) | 2018-07-03, 2018-11-23, 2018-12-24, 2019-07-03, 2019-11-29, 2019-12-24 |
| `NYSE.halbtage_archiv20200219` | https://web.archive.org/web/20200219200315id_/https://www.nyse.com/markets/hours-calendars | `902b381d9b42c81e96e26f80f6123e9743434232f60be1c7e2e1d5857e0d0137` (183790) | Abdeckung 2020, 2021, 2022 (Seite listet 2020–2022) | 2020-11-27, 2020-12-24, 2021-11-26, 2022-11-25 |
| `NYSE.halbtage_archiv20210208` | https://web.archive.org/web/20210208220700id_/https://www.nyse.com/markets/hours-calendars | `a43a686cbfad9c362dd5594a96718f5fabb207aa2e691517271d8c0f2bd1e582` (93533) | Abdeckung 2023 (Seite listet 2021–2023) | 2023-07-03, 2023-11-24 |
| `NYSE.halbtage_archiv20240111` | https://web.archive.org/web/20240111002222id_/https://www.nyse.com/markets/hours-calendars | `9b02f75db96aa8f0bf4ebfae2c991ed5a19c391ca703974b49176b5d1ae4bc40` (127218) | Abdeckung 2024, 2025 (Seite listet 2024–2026) | 2024-07-03, 2024-11-29, 2024-12-24, 2025-07-03, 2025-11-28, 2025-12-24 |
| `NYSE.halbtage_nyse20261012` | https://web.archive.org/web/20261009200946id_/https://www.nyse.com/trade/hours-calendars | `79602f7be5a8f1d39c2b1cac4dd02c4c07f18cf9f92d70602834069154719bad` (109229) | Abdeckung 2026, 2027, 2028 (Seite listet 2026–2028) | 2026-11-27, 2026-12-24, 2027-11-26, 2028-07-03, 2028-11-24 |

Gegenprobe: dieselben Termine nennen die ICE-Pressemitteilungen 2013/2016/2017/2018/2021/2022 (von Codex gegen
die Quellen bestätigt, docs/review_prompts/2026-10-12_kalender_v1c3_entwurf_v2_antwort.md); sie verweigern den
direkten Abruf und sind nur teilweise archiviert, deshalb nicht mehr Belegquelle.

Pflege: halbjährlich (mit `shared/produkttermine_listung.py`) die aktuelle NYSE-Seite neu abrufen, archivieren
lassen und als neue Kennung mit Prüfsumme eintragen.
