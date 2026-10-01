/* Bestandsnutzer: die Watchlist liegt noch unter dem ALTEN, kontolosen
   Schluessel. Seit der Trennung pro Konto liest ein eingeloggter Nutzer unter
   `sa-watchlist-v1::<uid>` — seine Liste darf dabei nicht verschwinden.

   Eine Datenmigration, die niemand prueft, ist ein stiller Verlust: die Seite
   laedt, sie ist nur leer. Geprueft wird deshalb nicht "der Code laeuft",
   sondern dass Ticker UND Notiz ankommen, dass die Liste ins Konto hochgeladen
   wird und dass der alte Schluessel danach leer ist (sonst sammelt ihn das
   naechste Konto ein zweites Mal ein — siehe probe_watchlist_konten.js). */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const REPO = path.resolve(__dirname, '..', '..');

global.window = global;
global.location = { pathname: '/watchlist', search: '', hash: '' };
global.addEventListener = function () {};
global.document = {
  getElementById() { return null; },
  querySelector() { return null; },
  querySelectorAll() { return []; },
  addEventListener() {},
  createElement() { return { style: {} }; }
};

const speicher = {};
global.localStorage = {
  getItem(k) { return k in speicher ? speicher[k] : null; },
  setItem(k, v) { speicher[k] = String(v); },
  removeItem(k) { delete speicher[k]; }
};

const UID = 'nutzer-A';
const fern = { [UID]: [] };

function tabelleStub() {
  const api = {
    select() { return api; }, eq() { return api; }, order() { return api; },
    then(a) { return Promise.resolve({ data: fern[UID].slice(), error: null }).then(a); },
    upsert(z) {
      fern[UID] = fern[UID].filter(x => x.ticker !== z.ticker);
      fern[UID].push({ ticker: z.ticker, added_at: z.added_at || '', note: z.note || '' });
      return { then: (a) => Promise.resolve({ error: null }).then(a) };
    },
    delete() {
      const d = { eq() { return d; }, then: (a) => Promise.resolve({ error: null }).then(a) };
      return d;
    }
  };
  return api;
}

// Bestandszustand VOR der Umstellung: alter Schluessel, zwei Ticker, eine Notiz.
speicher['sa-watchlist-v1'] = JSON.stringify({
  version: 1,
  items: [
    { ticker: 'BESTAND1', added_at: '2026-01-01T00:00:00Z', note: 'wichtig' },
    { ticker: 'BESTAND2', added_at: '2026-01-02T00:00:00Z', note: '' }
  ],
  tombstones: {}
});

global.SA = {
  auth: {
    isLoggedIn: true,
    user: { id: UID, email: 'a@example.com' },
    client: { from: tabelleStub },
    onAuthChange() {}
  }
};

vm.runInThisContext(
  fs.readFileSync(path.join(REPO, 'landing/js/watchlist.js'), 'utf8'),
  { filename: 'watchlist.js' });

(async function () {
  for (let i = 0; i < 40; i++) await Promise.resolve();

  let fehler = 0;
  function pruefe(name, bedingung, zusatz) {
    if (bedingung) { console.log('[OK  ] ' + name); return; }
    console.log('[FEHL] ' + name + (zusatz ? ' — ' + zusatz : ''));
    fehler++;
  }

  const liste = global.SA.watchlist.get();
  const ticker = liste.map(x => x.ticker).sort();
  const hochgeladen = fern[UID].map(x => x.ticker).sort();
  const notiz = (liste.find(x => x.ticker === 'BESTAND1') || {}).note;

  pruefe('Bestandsliste bleibt sichtbar',
    ticker.includes('BESTAND1') && ticker.includes('BESTAND2'), JSON.stringify(ticker));
  pruefe('die Notiz geht nicht verloren', notiz === 'wichtig', JSON.stringify(notiz));
  pruefe('Bestandsliste wird ins Konto hochgeladen',
    hochgeladen.includes('BESTAND1') && hochgeladen.includes('BESTAND2'),
    JSON.stringify(hochgeladen));
  pruefe('der alte Schluessel ist danach geleert',
    speicher['sa-watchlist-v1'] === undefined,
    'noch vorhanden');

  console.log(fehler === 0 ? '\nMigration ok.'
    : '\n' + fehler + ' Fall/Faelle durchgefallen.');
  process.exit(fehler === 0 ? 0 : 1);
})();
