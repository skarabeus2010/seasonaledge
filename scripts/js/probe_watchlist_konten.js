/* Stellt einen KONTOWECHSEL nach und prueft, dass keine Watchlist-Eintraege die
   Kontogrenze ueberschreiten.

   Der Mechanismus, um den es geht: der Cache liegt unter EINEM Schluessel ohne
   Nutzer-ID, er ueberlebt den Logout (bewusst, Gast-Modus), und beim naechsten
   Login werden lokale Eintraege unter der AKTUELLEN Nutzer-ID hochgeladen. RLS
   verhindert das nicht — der Client sendet bereits die neue Kennung als
   Eigentuemer.

   Dazu kommt, dass auth.js seine Listener nur feuert, wenn sich der BOOLEAN
   "eingeloggt" aendert. Ein direkter Wechsel A -> B bleibt damit unbemerkt.

   Drei Zusicherungen:
   (1) Was der Gast anlegt, erreicht nach dem Login Konto A — das ist das
       gewollte Verhalten und darf nicht verloren gehen.
   (2) Konto B sieht NICHTS von Konto A.
   (3) Nichts von Konto A wird als B hochgeladen. */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const REPO = path.resolve(__dirname, '..', '..');

/* ── Umgebung: window IST global, wie im Browser ───────────────────────── */
global.window = global;
global.location = { pathname: '/watchlist', search: '', hash: '' };
global.addEventListener = function () {};
global.document = {
  getElementById() { return null; },
  querySelector() { return null; },
  querySelectorAll() { return []; },
  addEventListener() {},
  createElement() { return { style: {}, classList: { add() {} } }; }
};

const speicher = {};
global.localStorage = {
  getItem(k) { return k in speicher ? speicher[k] : null; },
  setItem(k, v) { speicher[k] = String(v); },
  removeItem(k) { delete speicher[k]; },
  _keys() { return Object.keys(speicher); }
};

/* Supabase-Stub: eine Tabelle je Nutzer, protokolliert jeden Upsert. */
const fern = {};          // user_id -> [{ticker,…}]
const upserts = [];       // {user_id, ticker}
let aktuellerNutzer = null;

function tabelleStub() {
  const zustand = { filterUser: null };
  const api = {
    select() { return api; },
    eq(feld, wert) { if (feld === 'user_id') zustand.filterUser = wert; return api; },
    order() { return api; },
    then(aufl) {
      const uid = zustand.filterUser || aktuellerNutzer;
      return Promise.resolve({ data: (fern[uid] || []).slice(), error: null }).then(aufl);
    },
    upsert(zeile) {
      const uid = zeile.user_id || aktuellerNutzer;
      upserts.push({ user_id: uid, ticker: zeile.ticker });
      fern[uid] = (fern[uid] || []).filter(z => z.ticker !== zeile.ticker);
      fern[uid].push({ ticker: zeile.ticker, added_at: zeile.added_at || '', note: zeile.note || '' });
      return { then: (a) => Promise.resolve({ error: null }).then(a) };
    },
    delete() {
      const d = {
        eq(feld, wert) {
          if (feld === 'ticker') {
            const uid = aktuellerNutzer;
            fern[uid] = (fern[uid] || []).filter(z => z.ticker !== wert);
          }
          return d;
        },
        then: (a) => Promise.resolve({ error: null }).then(a)
      };
      return d;
    }
  };
  return api;
}

global.SA = { auth: null };

/* ── watchlist.js laden ────────────────────────────────────────────────── */
const quelle = fs.readFileSync(path.join(REPO, 'landing/js/watchlist.js'), 'utf8');

let fehler = 0;
function pruefe(name, bedingung, zusatz) {
  if (bedingung) { console.log('[OK  ] ' + name); return; }
  console.log('[FEHL] ' + name + (zusatz ? ' — ' + zusatz : ''));
  fehler++;
}

/* auth-Stub, der einen Nutzerwechsel melden kann. */
const hoerer = [];
function setzeNutzer(id) {
  const vorher = aktuellerNutzer;
  aktuellerNutzer = id;
  global.SA.auth = {
    isLoggedIn: !!id,
    user: id ? { id, email: id + '@example.com' } : null,
    client: { from: tabelleStub },
    onAuthChange(cb) { hoerer.push(cb); }
  };
  // Der Wechsel wird gemeldet — in der echten auth.js nur, wenn er gemeldet WIRD.
  if (vorher !== id) hoerer.forEach(cb => { try { cb(global.SA.auth.user); } catch (e) {} });
}

async function warte() { for (let i = 0; i < 40; i++) await Promise.resolve(); }

async function lauf() {
  // Gast: zwei Ticker anlegen
  setzeNutzer(null);
  vm.runInThisContext(quelle, { filename: 'watchlist.js' });
  const WL = global.SA.watchlist;
  WL.add('GAST1');
  WL.add('GAST2');

  // Login A
  setzeNutzer('nutzer-A');
  await warte();
  const nachA = WL.get().map(x => x.ticker).sort();
  pruefe('(1) Gast-Eintraege erreichen Konto A',
    nachA.includes('GAST1') && nachA.includes('GAST2'),
    'A sieht ' + JSON.stringify(nachA));
  WL.add('NUR-A');
  await warte();

  // Logout, dann Login B (anderes Konto, gleicher Browser)
  setzeNutzer(null);
  await warte();
  setzeNutzer('nutzer-B');
  await warte();

  const nachB = WL.get().map(x => x.ticker).sort();
  pruefe('(2) Konto B sieht NICHTS von Konto A',
    !nachB.includes('NUR-A') && !nachB.includes('GAST1') && !nachB.includes('GAST2'),
    'B sieht ' + JSON.stringify(nachB));

  const fremdUploads = upserts.filter(u => u.user_id === 'nutzer-B' &&
    ['NUR-A', 'GAST1', 'GAST2'].indexOf(u.ticker) >= 0);
  pruefe('(3) nichts von A wird als B hochgeladen',
    fremdUploads.length === 0,
    JSON.stringify(fremdUploads));

  console.log(fehler === 0
    ? '\nAlle Faelle bestanden.'
    : '\n' + fehler + ' Fall/Faelle durchgefallen.');
  process.exit(fehler === 0 ? 0 : 1);
}

lauf();
