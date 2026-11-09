# Vorbereitungsblatt Block 1 (S02–S08)

KI-Hilfe (Claude) vor dem Schreiben, offengelegt nach ADR 0031. Das Blatt enthält nur mechanische Fundstellen aus
`uv run python src/catalogue.py find "<Begriff>"` und die Klassenregeln (ADR 0029). Es enthält keine Frage, keine
Antwort, keinen Typ und kein Relevanzurteil; diese legt Jonas fest. Erstellt am 29.10.2026.

Regel für alle Slots: Jeder Abschnitt, der einen für die Antwort nötigen Teil enthält, gehört in die relevanten
Abschnitte (Referenz Fragenkatalog: „im ganzen Korpus suchen“). „Nur hier“ heißt: `find` liefert genau diesen
Abschnitt.

## S02 · multi-section · D037#use-a-subscription-or-api-key

Regel: mindestens zwei Abschnitte, jeder nötig.

- Doppelt vorhanden: die Abo-Tabelle (`npx e2e login …`) auch in `D055#subscriptions`; die Anbieter-Tabelle auch in
  `D036#ai-sdk-providers`; „Copilot uses your GitHub CLI login“ auch in `D055#sign-in-help`; „The wizard writes the
  config …“ auch in `D037#run-your-first-test`. Ein Teil aus diesen Stellen macht beide Fundstellen relevant.
- Fundstellen zu verwandten Themen: `D055#set-up`, `D055#ci` (Claude Max or Team, API-Schlüssel in CI),
  `D036#what-fails-and-where` (`npx e2e login`, `CONFIG_LOAD_FAILED`), `D041#env-files` (`process.loadEnvFile()`).

## S03 · paraphrase · D035#hosted-devices

Regel: genau ein Abschnitt; die Frage teilt kein Inhaltswort mit „Hosted devices“ oder dem Seitentitel „Mobile“
(auch keine Wortformen: host…, device…, mobile…).

- Nur hier: „replay cache keys on `app.bundleId`“, „a service bills a session while it runs“.
- Mehrfach: `acquire`/`release`, `cleanupTimeout`, „every exit path“, `request.env` stehen auch in
  `D005#write-a-provider` und weiteren Abschnitten zu Browser-Anbietern; `DeviceProvider` auch in
  `D023#use-a-service-with-no-integration`, `D047#engine`, `D047#exported-types`; Limrun hat eine eigene Seite (D026).

## S04 · multi-section · D035#expo-development-builds

Regel: mindestens zwei Abschnitte, jeder nötig.

- Nur hier: `expo-dev-client`, `--initialUrl`, der `exp+<slug>://expo-development-client/…`-Link, „dev launcher“,
  „longer timeout“ für die erste Prüfung.
- Fundstellen zu verwandten Themen: `D035#launch-arguments-and-permissions` (`launchArguments`, Aufwärmen),
  `D041#the-app-under-test` (`readyUrl`, `command`, `launchArguments`), `D059#let-the-runner-start-it` (`readyUrl`),
  `D035#the-device-fixture` und `D047#device` (`openLink`), `D039#open` (`app.open()`).

## S05 · single · D058#stored-screenshots

Regel: genau ein Abschnitt, dessen Hauptinhalt die Antwort ist.

- Nur hier: „fonts and rendering differ“ (je Ziel und Betriebssystem eine Datei).
- Mehrfach: `--update-snapshots` auch in `D058#in-ci`, `D058#when-it-fails`, `D045#screenshot-matchers`,
  `D040#commands`, `D033#map-each-api`; der Ordner `…-snapshots/` auch in `D045#screenshot-matchers`, `D058#in-ci`,
  `D058#when-it-fails`. Eine Frage zum Aktualisieren hätte mehrere relevante Abschnitte.

## S06 · multi-section · D019#start-signed-in

Regel: mindestens zwei Abschnitte, jeder nötig.

- Nur hier: „restores the session“, „plans no sign-in step“.
- `--session <name>` auch in `D040#commands`.
- Fundstellen zu verwandten Themen: `D004#sign-in-once-in-a-setup-test`, `D004#session-rules` (Setup-Test, Sitzung
  speichern), `D051#screenshots-after-a-secret-fill`, `D051#secret-fills` (keine Screenshots nach Passwort).

## S07 · detail · D036#ai-sdk-providers

Regel: genau ein Abschnitt, ein einzelnes Faktum, Referenzantwort höchstens 30 Wörter.

- Nur hier: DeepSeek V4 und Meta Muse Spark lehnen die erzwungene Tool-Wahl ab; „AI SDK language model specification
  v2 or later“.
- Doppelt: die ganze Anbieter-Tabelle (Pakete, Variablen, Modelle, `CONFIG_LOAD_FAILED`-Hinweise) steht auch in
  `D037#use-a-subscription-or-api-key`; `process.loadEnvFile()` auch in `D041#env-files` und zwei D036-Abschnitten.
  Ein Faktum daraus hätte zwei relevante Abschnitte.

## S08 · multi-section · D016#what-the-model-can-do

Regel: mindestens zwei Abschnitte, jeder nötig.

- Nur hier: `secondary_tap`, die Option `none` („`none` blocks the step“).
- Fundstellen zu verwandten Themen: `D016#how-text-gets-typed` und `D018#what-the-context-holds` (`typeSecret`);
  `D038#action-tools`, `D047#agent-tools`, `D042#capabilities`, `D046#the-catalog` (`dismiss_keyboard`).
