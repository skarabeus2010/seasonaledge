/**
 * release_harness.js — gemeinsamer Helfer für alle Harnesse, die echte Dateien aus landing/js/ laden.
 *
 * Jede eigene JS-Datei beginnt mit `window.SA.__release('<kennung>')` (landing/js/methode.js, V1b). Ein Harness
 * muss deshalb — wie jede Seite — zuerst die ECHTE methode.js gegen dasselbe `window` ausführen und die
 * HTML-Kennung setzen. Keine Ersatzfunktion: wer hier stubbt, prüft eine freundlichere Welt (Codex, Entwurf R1).
 *
 *   const {bereite} = require('./release_harness');
 *   bereite(window);                 // window-Stub, gegen den danach die Dateien laufen
 *   bereite();                       // node: global.window = global (für require()-geladene Dateien)
 *   bereite(window, basisordner);    // Mutationstests mit Kopie: methode.js aus derselben Kopie
 *
 * Die HTML-Kennung ist der Platzhalter — wie im unveränderten Quelltext; Dateien tragen ihn ebenfalls.
 */
'use strict';
const fs = require('fs');
const path = require('path');

function bereite(win, basis) {
  if (!win) {
    if (typeof global.window === 'undefined') global.window = global;
    win = global.window;
  }
  if (win.__SA_RELEASE === undefined) win.__SA_RELEASE = '%%RELEASE%%';
  if (win.SA && win.SA.__release) return win;
  const datei = path.join(basis || path.join(__dirname, '..', '..'), 'landing', 'js', 'methode.js');
  new Function('window', fs.readFileSync(datei, 'utf8'))(win);
  return win;
}

module.exports = {bereite};
