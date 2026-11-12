# Vorbereitungsblatt Block 6 (S41–S48)

KI-Hilfe (Claude) vor dem Schreiben, offengelegt nach ADR 0031/0049. Mechanischer Teil wie bei Block 3 bis 5: je Satz
des Ausgangsabschnitts (ohne Codeblöcke; Tabellenzeilen zählen je als ein Satz), ob eine Folge von 5 Wörtern auch im
eigenen Text eines anderen Abschnitts steht (außer umschließenden und enthaltenen Abschnitten), und für Begriffe in
Backticks, in welchen anderen Abschnitten sie vorkommen (nur bei höchstens 10 Treffern gelistet). Dazu die Zeilen aus
`catalogue_overlap.csv` und je Slot die **Typ-Eignung** (ADR 0049, Nachtrag 10.11.2026). Jede Stelle, auf die sich
ein Typ stützt, ist mit `catalogue.py find` auf ihre Kernformulierung geprüft, und jeder Treffer ist gelesen; in
Block 5 hatte eine nur wörtlich geprüfte Stelle (S37) zu einer falschen Angabe „nur hier“ geführt. Die Typ-Eignung ist
ein Vorschlag; den Typ wählt Jonas (ADR 0031). Das Blatt enthält keine Frage, keine Antwort und kein Relevanzurteil.
„ONLY HERE“ heißt nur: kein wörtlicher Treffer. Erstellt am 12.11.2026.

Typziel Block 6 ([Plan](../../docs/plan.md#zeitplan)): **4 conceptual, 1 comparative, 1 limitation, 2 procedural,
0 factual** (`factual` ist mit 12 voll). Vorschlag: S41 procedural, S42 conceptual, S43 limitation, S44 conceptual,
S45 conceptual, S46 conceptual, S47 comparative, S48 procedural. Ausweichen ohne Quotenbruch: S43 `comparative` und
S47 `limitation` tauschen. Closed-Book: Von den 8 Fragen müssen mindestens 2 `miss` sein (ADR 0040; Stand 30 von 40).
Reserven sind nicht analysiert; bei einem Sprung prüfe ich die nächste Reserve wie in Block 5.

## S41 · multi-section · D053#the-browser-fixture  (Browser › Reference › The browser fixture; page title: Browser)

Regel: mindestens zwei Abschnitte, jeder liefert einen nötigen Teil; enthaltene oder umschließende Abschnitte zählen nicht als zweiter; H1 nur mit Grund in `notes`.

**Typ-Eignung:** Ziel `procedural`: wie ein Test native Dialoge behandelt. Zwei Abschnitte liefern je einen nötigen Teil: D005#handle-a-dialog sagt, dass ein unbehandeltes `alert`, `confirm` oder `prompt` den nächsten Schritt scheitern lässt und der Handler vorher registriert wird; nur hier (D053#the-browser-fixture) stehen, was mit einem Funktions-Handler geschieht, der weder `accept` noch `dismiss` aufruft („has the dialog dismissed“, `find "does neither"`: nur hier), und dass Fehler des Handlers erst am nächsten Schritt auftauchen (Tabelle `APP_NOT_OPEN`, `ASSERTION_FAILED`, `ENGINE_FAILURE`; `find "answered neither"`: nur hier). Vorsicht: „fails the next step“ steht auch in D005#handle-a-dialog, `onDialog` außerdem in D053#browser-interface, D051#navigation und den Migrationsseiten (D030, D033, D034). Andere Typen: `procedural` zu `route` geht kaum, weil D005#mock-an-api fast alles schon enthält (Reihenfolge, genau eine Entscheidung, `fallback`). Der Umgang mit einem neuen Tab („Assert on what that tab shows, or open the link's URL with `browser.goto`“) steht nur hier, aber der zweite Abschnitt D053#browser-interface wiederholt nur „not followed“ und liefert keinen eigenen Teil, also kein sauberes `multi-section`.

- **[ONLY HERE]** `browser` is the whole browser, showing one active tab.
    term `browser` also in 146
- **[ALSO: D053#browser-interface]** - What reads or acts on a page acts on the active tab: `goto`, `reload`, `back`, `forward`, `url`, `title`, `waitForURL`, `locator`, `frameLocator`, `evaluate`, `waitForResponse`, `waitForDownload`, `keyboard`, `mouse`, the `expect(browser)` matchers, and every `screen` query.
    term `goto` also in 8: D005#mock-an-api, D016#limits, D027#start-every-test-signed-in, D033#browser-timeouts-and-artifacts, D033#rewrite-one-spec, D033#map-each-api, D051#navigation, D053#browser-interface
    term `reload` also in 10: D006#what-the-agent-does, D012#ios-and-android, D027#what-differs-from-a-local-browser, D031#map-each-detox-call, D033#map-each-api, D034#map-each-webdriver-call, D046#reference-mcp, D050#queries, D053#options, D053#browser-interface
    term `back` also in 77
    term `forward` also in 5: D027#what-differs-from-a-local-browser, D033#map-each-api, D035#physical-devices, D047#device-fixture, D053#browser-interface
    term `url` also in 140
    term `title` also in 37
    term `waitForURL` also in 4: D007#when-a-recording-is-written, D027#start-every-test-signed-in, D033#map-each-api, D053#browser-interface
    term `locator` also in 110
    term `frameLocator` also in 8: D005#reach-into-an-iframe, D005#shadow-dom, D015#common-errors, D025#what-does-not-work, D033#map-each-api, D034#map-each-webdriver-call, D050#locator-reads, D053#browser-interface
    term `evaluate` also in 17
    term `waitForResponse` also in 4: D005#mock-an-api, D030#map-each-command, D033#map-each-api, D053#browser-interface
    term `waitForDownload` also in 9: D005#download-a-file, D005#write-a-provider, D005#downloads-on-the-provider, D015#artifacts, D024#downloads, D025#what-does-not-work, D027#what-differs-from-a-local-browser, D033#map-each-api, D053#browser-interface
    term `keyboard` also in 25
    term `mouse` also in 6: D025#what-does-not-work, D033#map-each-api, D033#port-page-objects, D038#action-tools, D053#options, D053#browser-interface
    term `expect(browser)` also in 13
    term `screen` also in 214
- **[ONLY HERE]** - What belongs to the browser covers every tab: `cookies`, `setCookies`, `route`, `unroute`, `onDialog`, and `addInitScript`.
    term `cookies` also in 20
    term `setCookies` also in 10: D005#cookies, D025#what-works, D025#what-does-not-work, D030#map-each-command, D033#browser-timeouts-and-artifacts, D033#map-each-api, D034#map-each-webdriver-call, D051#policy-denials, D051#screenshots-after-a-secret-fill, D053#browser-interface
    term `route` also in 33
    term `unroute` also in 2: D033#map-each-api, D053#browser-interface
    term `onDialog` also in 7: D005#handle-a-dialog, D025#what-does-not-work, D030#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D051#navigation, D053#browser-interface
    term `addInitScript` also in 4: D005#run-a-script-before-the-page, D033#map-each-api, D053#options, D053#browser-interface
- **[ALSO: D033#map-each-api, D053#browser-interface, D053#options]** - `setViewport` sizes the active tab and every tab opened after it, and `emulateMedia` sets its media the same way.
    term `setViewport` also in 9: D025#what-does-not-work, D030#map-each-command, D033#map-each-api, D053#options, D053#weboptions, D053#browser-interface, D059#viewports, D059#fill-the-window, D059#resize-inside-a-test
    term `emulateMedia` also in 5: D005#emulate-dark-mode-and-reduced-motion, D025#what-does-not-work, D033#map-each-api, D053#options, D053#browser-interface
- **[ALSO: D053#browser-interface, D053#options]** - A tab the app opens itself, from a `target="_blank"` link or `window.open`, is not followed.
    term `target="_blank"` also in 1: D053#browser-interface
    term `window.open` also in 1: D053#browser-interface
- **[ALSO: D053#browser-interface]** The active tab stays the one the attempt opened.
- **[ONLY HERE]** Assert on what that tab shows, or open the link's URL with `browser.goto`.
    term `browser.goto` also in 5: D005#mock-an-api, D016#limits, D033#browser-timeouts-and-artifacts, D033#map-each-api, D051#navigation
- **[ONLY HERE]** - Every `browser` call is a recorded `browser.<method>` step, except `locator` and `frameLocator`.
    term `browser` also in 146
    term `locator` also in 110
    term `frameLocator` also in 8: D005#reach-into-an-iframe, D005#shadow-dom, D015#common-errors, D025#what-does-not-work, D033#map-each-api, D034#map-each-webdriver-call, D050#locator-reads, D053#browser-interface
- **[ONLY HERE]** They build a locator without touching the page, and the action or assertion on it is the step.
- **[ALSO: D041#resolution-order]** - A relative URL resolves against the target's `app.url`, else `APP_URL_REQUIRED`.
    term `app.url` also in 19
    term `APP_URL_REQUIRED` also in 6: D039#open, D041#the-app-under-test, D041#resolution-order, D042#errors, D042#contributed-fixtures, D044#runner-codes
- **[ALSO: D047#reference-mobile]** - Declare `requires: ['browser']` in a suite that also runs on other platforms.
    term `requires: ['browser']` also in 5: D005#browser, D033#map-each-api, D033#port-page-objects, D052#fixtures, D053#options
- **[ONLY HERE]** - `expect(browser)` returns the `BrowserExpectation` the engine attaches: `toHaveURL`, `toHaveTitle`, and `toHaveClass`.
    term `expect(browser)` also in 13
    term `BrowserExpectation` also in 4: D045#browser-matchers, D045#browserexpectation, D053#types, D053#browser-interface
    term `toHaveURL` also in 14
    term `toHaveTitle` also in 6: D005#browser, D025#what-works, D030#map-each-command, D033#map-each-api, D045#browser-matchers, D045#browserexpectation
    term `toHaveClass` also in 3: D033#map-each-api, D045#browser-matchers, D045#browserexpectation
- **[ONLY HERE]** See [browser matchers](/reference/expect#browser-matchers).
- **[ONLY HERE]** | [`goto`](#goto) | `Promise<void>` |
    term `goto` also in 8: D005#mock-an-api, D016#limits, D027#start-every-test-signed-in, D033#browser-timeouts-and-artifacts, D033#rewrite-one-spec, D033#map-each-api, D051#navigation, D053#browser-interface
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`reload`](#reload-back-forward) | `Promise<void>` |
    term `reload` also in 10: D006#what-the-agent-does, D012#ios-and-android, D027#what-differs-from-a-local-browser, D031#map-each-detox-call, D033#map-each-api, D034#map-each-webdriver-call, D046#reference-mcp, D050#queries, D053#options, D053#browser-interface
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`back`](#reload-back-forward) | `Promise<void>` |
    term `back` also in 77
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`forward`](#reload-back-forward) | `Promise<void>` |
    term `forward` also in 5: D027#what-differs-from-a-local-browser, D033#map-each-api, D035#physical-devices, D047#device-fixture, D053#browser-interface
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`url`](#url-title) | `Promise<string>` |
    term `url` also in 140
    term `Promise<string>` also in 9: D039#reference, D039#types, D041#credentialconfig, D042#lifecycle, D042#artifacts, D047#device, D050#locator-reads, D053#options, D053#browser-interface
- **[ONLY HERE]** | [`title`](#url-title) | `Promise<string>` |
    term `title` also in 37
    term `Promise<string>` also in 9: D039#reference, D039#types, D041#credentialconfig, D042#lifecycle, D042#artifacts, D047#device, D050#locator-reads, D053#options, D053#browser-interface
- **[ONLY HERE]** | [`waitForURL`](#waitforurl) | `Promise<void>` |
    term `waitForURL` also in 4: D007#when-a-recording-is-written, D027#start-every-test-signed-in, D033#map-each-api, D053#browser-interface
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`locator`](#locator) | `Locator` |
    term `locator` also in 110
    term `Locator` also in 110
- **[ONLY HERE]** | [`frameLocator`](#framelocator) | `FrameScreen` |
    term `frameLocator` also in 8: D005#reach-into-an-iframe, D005#shadow-dom, D015#common-errors, D025#what-does-not-work, D033#map-each-api, D034#map-each-webdriver-call, D050#locator-reads, D053#browser-interface
    term `FrameScreen` also in 2: D053#types, D053#browser-interface
- **[ONLY HERE]** | [`evaluate`](#evaluate) | `Promise<T>` |
    term `evaluate` also in 17
    term `Promise<T>` also in 3: D042#shared-semantics, D045#expectcall-softexpectcall-and-expect, D053#browser-interface
- **[ONLY HERE]** | [`addInitScript`](#init-scripts) | `Promise<void>` |
    term `addInitScript` also in 4: D005#run-a-script-before-the-page, D033#map-each-api, D053#options, D053#browser-interface
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`route`](#route) | `Promise<void>` |
    term `route` also in 33
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`unroute`](#unroute) | `Promise<void>` |
    term `unroute` also in 2: D033#map-each-api, D053#browser-interface
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`waitForResponse`](#waitforresponse) | `Promise<WebResponse>` |
    term `waitForResponse` also in 4: D005#mock-an-api, D030#map-each-command, D033#map-each-api, D053#browser-interface
    term `Promise<WebResponse>` also in 1: D053#browser-interface
- **[ONLY HERE]** | [`cookies`](#cookies) | `Promise<Cookie[]>` |
    term `cookies` also in 20
    term `Promise<Cookie[]>` also in 1: D053#browser-interface
- **[ONLY HERE]** | [`setCookies`](#setcookies) | `Promise<void>` |
    term `setCookies` also in 10: D005#cookies, D025#what-works, D025#what-does-not-work, D030#map-each-command, D033#browser-timeouts-and-artifacts, D033#map-each-api, D034#map-each-webdriver-call, D051#policy-denials, D051#screenshots-after-a-secret-fill, D053#browser-interface
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`setViewport`](#setviewport) | `Promise<void>` |
    term `setViewport` also in 9: D025#what-does-not-work, D030#map-each-command, D033#map-each-api, D053#options, D053#weboptions, D053#browser-interface, D059#viewports, D059#fill-the-window, D059#resize-inside-a-test
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`emulateMedia`](#media-emulation) | `Promise<void>` |
    term `emulateMedia` also in 5: D005#emulate-dark-mode-and-reduced-motion, D025#what-does-not-work, D033#map-each-api, D053#options, D053#browser-interface
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`onDialog`](#ondialog) | `Promise<() => Promise<void>>` |
    term `onDialog` also in 7: D005#handle-a-dialog, D025#what-does-not-work, D030#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D051#navigation, D053#browser-interface
    term `Promise<() => Promise<void>>` also in 1: D053#browser-interface
- **[ONLY HERE]** | [`waitForDownload`](#waitfordownload) | `Promise<{ path, absolutePath, … }>` |
    term `waitForDownload` also in 9: D005#download-a-file, D005#write-a-provider, D005#downloads-on-the-provider, D015#artifacts, D024#downloads, D025#what-does-not-work, D027#what-differs-from-a-local-browser, D033#map-each-api, D053#browser-interface
- **[ONLY HERE]** | [`keyboard`](#keyboard) | `{ press, down, up, type }` |
    term `keyboard` also in 25
- **[ONLY HERE]** | [`mouse`](#mouse) | `{ move, wheel, down, up }` |
    term `mouse` also in 6: D025#what-does-not-work, D033#map-each-api, D033#port-page-objects, D038#action-tools, D053#options, D053#browser-interface
- **[ONLY HERE]** The [config](/reference/config) sets each member's budget:
- **[ONLY HERE]** - `goto`, `reload`, `back`, and `forward`: [`timeout`](/reference/config#timeout), the same budget `app.open()` uses.
    term `goto` also in 8: D005#mock-an-api, D016#limits, D027#start-every-test-signed-in, D033#browser-timeouts-and-artifacts, D033#rewrite-one-spec, D033#map-each-api, D051#navigation, D053#browser-interface
    term `reload` also in 10: D006#what-the-agent-does, D012#ios-and-android, D027#what-differs-from-a-local-browser, D031#map-each-detox-call, D033#map-each-api, D034#map-each-webdriver-call, D046#reference-mcp, D050#queries, D053#options, D053#browser-interface
    term `back` also in 77
    term `forward` also in 5: D027#what-differs-from-a-local-browser, D033#map-each-api, D035#physical-devices, D047#device-fixture, D053#browser-interface
    term `timeout` also in 99
    term `app.open()` also in 36
- **[ONLY HERE]** - `waitForURL`: [`assertionTimeout`](/reference/config#assertiontimeout).
    term `waitForURL` also in 4: D007#when-a-recording-is-written, D027#start-every-test-signed-in, D033#map-each-api, D053#browser-interface
    term `assertionTimeout` also in 10: D033#browser-timeouts-and-artifacts, D033#defaults-that-differ, D034#port-the-config, D041#top-level, D041#e2econfig, D045#screenshot-matchers, D045#polling-a-value, D045#timeouts-and-failures, D058#when-it-fails, D058#tolerance-and-masks
- **[ONLY HERE]** - Every other member: [`actionTimeout`](/reference/config#actiontimeout).
    term `actionTimeout` also in 16
- **[ONLY HERE]** `locator` and `frameLocator` touch no page and take none.
    term `locator` also in 110
    term `frameLocator` also in 8: D005#reach-into-an-iframe, D005#shadow-dom, D015#common-errors, D025#what-does-not-work, D033#map-each-api, D034#map-each-webdriver-call, D050#locator-reads, D053#browser-interface
- **[ALSO: D045#polling-a-value]** A `{ timeout }` option overrides the budget on `goto`, `reload`, `back`, `forward`, `waitForResponse`, and `waitForDownload`, capped by the test deadline.
    term `{ timeout }` also in 7: D015#common-errors, D032#map-each-command, D033#browser-timeouts-and-artifacts, D033#map-each-api, D045#timeouts-and-failures, D045#negation, D050#locator-actions
    term `goto` also in 8: D005#mock-an-api, D016#limits, D027#start-every-test-signed-in, D033#browser-timeouts-and-artifacts, D033#rewrite-one-spec, D033#map-each-api, D051#navigation, D053#browser-interface
    term `reload` also in 10: D006#what-the-agent-does, D012#ios-and-android, D027#what-differs-from-a-local-browser, D031#map-each-detox-call, D033#map-each-api, D034#map-each-webdriver-call, D046#reference-mcp, D050#queries, D053#options, D053#browser-interface
    term `back` also in 77
    term `forward` also in 5: D027#what-differs-from-a-local-browser, D033#map-each-api, D035#physical-devices, D047#device-fixture, D053#browser-interface
    term `waitForResponse` also in 4: D005#mock-an-api, D030#map-each-command, D033#map-each-api, D053#browser-interface
    term `waitForDownload` also in 9: D005#download-a-file, D005#write-a-provider, D005#downloads-on-the-provider, D015#artifacts, D024#downloads, D025#what-does-not-work, D027#what-differs-from-a-local-browser, D033#map-each-api, D053#browser-interface
- **[ONLY HERE]** `url`, `title`, `evaluate`, `addInitScript`, `route`, `unroute`, `cookies`, `setCookies`, `setViewport`, `emulateMedia`, `onDialog`, `keyboard.*`, and `mouse.*` take no override.
    term `url` also in 140
    term `title` also in 37
    term `evaluate` also in 17
    term `addInitScript` also in 4: D005#run-a-script-before-the-page, D033#map-each-api, D053#options, D053#browser-interface
    term `route` also in 33
    term `unroute` also in 2: D033#map-each-api, D053#browser-interface
    term `cookies` also in 20
    term `setCookies` also in 10: D005#cookies, D025#what-works, D025#what-does-not-work, D030#map-each-command, D033#browser-timeouts-and-artifacts, D033#map-each-api, D034#map-each-webdriver-call, D051#policy-denials, D051#screenshots-after-a-secret-fill, D053#browser-interface
    term `setViewport` also in 9: D025#what-does-not-work, D030#map-each-command, D033#map-each-api, D053#options, D053#weboptions, D053#browser-interface, D059#viewports, D059#fill-the-window, D059#resize-inside-a-test
    term `emulateMedia` also in 5: D005#emulate-dark-mode-and-reduced-motion, D025#what-does-not-work, D033#map-each-api, D053#options, D053#browser-interface
    term `onDialog` also in 7: D005#handle-a-dialog, D025#what-does-not-work, D030#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D051#navigation, D053#browser-interface
    term `mouse.*` also in 1: D033#map-each-api
- **[ONLY HERE]** Navigates the active tab to a URL.
- **[ONLY HERE]** `waitUntil` is `'load'`, `'domcontentloaded'`, or `'networkidle'`.
    term `waitUntil` also in 3: D032#map-each-command, D033#map-each-api, D053#browser-interface
    term `'load'` also in 1: D053#browser-interface
    term `'domcontentloaded'` also in 1: D053#browser-interface
    term `'networkidle'` also in 1: D053#browser-interface
- **[ALSO: D039#open]** | `POLICY_DENIED` | A URL whose scheme is not `http:` or `https:`. `about:blank` is admitted. |
    term `POLICY_DENIED` also in 27
    term `http:` also in 42
    term `https:` also in 70
    term `about:blank` also in 7: D005#cookies, D039#open, D041#the-app-under-test, D042#contributed-fixtures, D051#policy-denials, D051#navigation, D053#options
- **[ALSO: D039#baseurl, D039#open, D039#types, D042#app, D042#contributed-fixtures, D044#runner-codes]** | `APP_URL_REQUIRED` | A relative URL, on a target that declares no `app.url`. |
    term `APP_URL_REQUIRED` also in 6: D039#open, D041#the-app-under-test, D041#resolution-order, D042#errors, D042#contributed-fixtures, D044#runner-codes
    term `app.url` also in 19
- **[ONLY HERE]** | `ACTION_FAILED` | The navigation failed. |
    term `ACTION_FAILED` also in 13
- **[ONLY HERE]** `reload` reloads the current document.
    term `reload` also in 10: D006#what-the-agent-does, D012#ios-and-android, D027#what-differs-from-a-local-browser, D031#map-each-detox-call, D033#map-each-api, D034#map-each-webdriver-call, D046#reference-mcp, D050#queries, D053#options, D053#browser-interface
- **[ONLY HERE]** `back` and `forward` navigate browser history once.
    term `back` also in 77
    term `forward` also in 5: D027#what-differs-from-a-local-browser, D033#map-each-api, D035#physical-devices, D047#device-fixture, D053#browser-interface
- **[ONLY HERE]** | `ACTION_FAILED` | The navigation failed. |
    term `ACTION_FAILED` also in 13
- **[ONLY HERE]** Return the active tab's current URL and title.
- **[ALSO: D045#browser-matchers, D045#browserexpectation, D053#browser-interface]** Waits for the current URL to match, polling every 100 ms.
- **[ONLY HERE]** It is the same poll as `expect(browser).toHaveURL`.
    term `expect(browser).toHaveURL` also in 12
- **[ALSO: D042#session, D045#browser-matchers]** - A relative string resolves against the base URL and matches exactly after normalization.
- **[ALSO: D045#browser-matchers]** - A `RegExp` tests the full URL.
    term `RegExp` also in 20
- **[ALSO: D041#the-app-under-test, D044#runner-codes, D049#host]** | `INVALID_ARGUMENT` | A pattern that is not a string or `RegExp` (a predicate function, say), or an option other than `timeout`, such as Playwright's `waitUntil`. |
    term `INVALID_ARGUMENT` also in 29
    term `RegExp` also in 20
    term `timeout` also in 99
    term `waitUntil` also in 3: D032#map-each-command, D033#map-each-api, D053#browser-interface
- **[ONLY HERE]** | `ASSERTION_FAILED` | The URL did not match before the timeout. |
    term `ASSERTION_FAILED` also in 15
- **[ONLY HERE]** Creates a web-only locator from a Playwright selector.
- **[ALSO: D033#map-each-api]** - The selector is CSS by default, XPath with `xpath=` or a leading `//`, and takes `>>` chains, so the example scopes CSS to one row.
    term `xpath=` also in 1: D033#map-each-api
- **[ONLY HERE]** - Use `filter({ has })` for an element that contains another.
    term `filter({ has })` also in 1: D035#known-device-limitations
- **[ONLY HERE]** | `INVALID_LOCATOR` | An empty selector, or a `*` capture before the last part (`*css=article >> text=Hello`). |
    term `INVALID_LOCATOR` also in 8: D033#map-each-api, D042#errors, D042#shared-semantics, D044#runner-codes, D050#queries, D050#refinement, D050#screen-actions, D050#locator-actions
- **[ONLY HERE]** **Note** Every `screen` query searches its scope and each closed shadow root the page attached under it, with Playwright's own role, name, text, label, and attribute matching and each node found once.
    term `screen` also in 214
- **[ONLY HERE]** A control the observed tree lists inside a closed root resolves and takes actions and reads.
- **[ALSO: D005#shadow-dom]** `locator`, `frameLocator`, and `filter({ hasText })` keep Playwright's reach and stop at a closed root; the [browser guide](/browser#shadow-dom) has the details.
    term `locator` also in 110
    term `frameLocator` also in 8: D005#reach-into-an-iframe, D005#shadow-dom, D015#common-errors, D025#what-does-not-work, D033#map-each-api, D034#map-each-webdriver-call, D050#locator-reads, D053#browser-interface
    term `filter({ hasText })` also in 2: D005#shadow-dom, D046#the-catalog
- **[ALSO: D053#browser-interface]** Creates a screen query scope inside one iframe.
- **[ONLY HERE]** It returns a `FrameScreen`, a `Screen` whose queries answer from inside the frame.
    term `FrameScreen` also in 2: D053#types, D053#browser-interface
    term `Screen` also in 214
- **[ONLY HERE]** Use the frame's `locator` only when the control has no accessible name, label, placeholder, or test id.
    term `locator` also in 110
- **[ONLY HERE]** The [browser guide](/browser#reach-into-an-iframe) shows when that applies.
- **[ONLY HERE]** The errors are the same at the page and inside a frame:
- **[ONLY HERE]** | `INVALID_LOCATOR` | An empty selector, here or in the frame's `locator`. |
    term `INVALID_LOCATOR` also in 8: D033#map-each-api, D042#errors, D042#shared-semantics, D044#runner-codes, D050#queries, D050#refinement, D050#screen-actions, D050#locator-actions
    term `locator` also in 110
- **[ONLY HERE]** | `LOCATOR_NOT_FOUND` | No frame matches. |
    term `LOCATOR_NOT_FOUND` also in 14
- **[ONLY HERE]** | `LOCATOR_AMBIGUOUS` | Several frames match. |
    term `LOCATOR_AMBIGUOUS` also in 16
- **[ALSO: D053#browser-interface]** Evaluates trusted test code in the page and returns its result.
- **[ONLY HERE]** - The function runs in the page and cannot access variables from the test. e2e serializes it by its source and inlines it into the page, so it must not close over anything outside its own body.
- **[ONLY HERE]** Helpers declared inside the body work.
- **[ONLY HERE]** Pass outside values through `arg`.
    term `arg` also in 224
- **[ONLY HERE]** - A string is evaluated as a single expression, not as statements.
- **[ONLY HERE]** If it evaluates to a function, that function is called with `arg`.
    term `arg` also in 224
- **[ONLY HERE]** Else its value is the result.
- **[ONLY HERE]** - A promise, from either, is awaited.
- **[ONLY HERE]** | `INVALID_ARGUMENT` | `arg` or the return value is not a [`JsonValue`](#jsonvalue). |
    term `INVALID_ARGUMENT` also in 29
    term `arg` also in 224
    term `JsonValue` also in 4: D042#shared-semantics, D042#exported-names, D053#browser-interface, D053#jsonvalue
- **[ONLY HERE]** | `EVALUATE_FAILED` | The evaluated code threw. The error carries its message. |
    term `EVALUATE_FAILED` also in 1: D044#runner-codes
- **[ONLY HERE]** | `ACTION_FAILED` | A Playwright timeout. |
    term `ACTION_FAILED` also in 13
- **[ONLY HERE]** | `ENGINE_FAILURE` | The page closed or the context was lost. |
    term `ENGINE_FAILURE` also in 13
- **[ALSO: D053#browser-interface]** Adds an attempt-scoped network route.
- **[ALSO: D047#engine, D050#queries]** - The pattern is a string or a `RegExp`, both tested against the full URL.
    term `RegExp` also in 20
- **[ONLY HERE]** In a string, `*` matches within a path segment, `**` across `/`, `?` any one character, and `\` escapes the next.
- **[ONLY HERE]** `unroute` and `waitForResponse` take the same patterns.
    term `unroute` also in 2: D033#map-each-api, D053#browser-interface
    term `waitForResponse` also in 4: D005#mock-an-api, D030#map-each-command, D033#map-each-api, D053#browser-interface
- **[ONLY HERE]** - A route survives `app.restart()`, `app.clearState()`, and session restore.
    term `app.restart()` also in 14
    term `app.clearState()` also in 20
- **[ONLY HERE]** - Routes run newest first.
- **[ALSO: D005#mock-an-api]** - The handler must decide exactly once, with `fulfill`, `continue`, `fallback`, or `abort`, each described on `WebRoute` below.
    term `fulfill` also in 4: D005#mock-an-api, D030#map-each-command, D033#map-each-api, D053#types
    term `continue` also in 10: D005#mock-an-api, D007#how-a-replay-works, D018#replay-cache, D032#rewrite-one-flow, D033#map-each-api, D035#the-device-fixture, D045#soft-assertions, D047#device, D053#options, D053#types
    term `fallback` also in 11
    term `abort` also in 19
    term `WebRoute` also in 2: D053#types, D053#browser-interface
- **[ONLY HERE]** - A `continue` URL goes through the same rule as `goto`.
    term `continue` also in 10: D005#mock-an-api, D007#how-a-replay-works, D018#replay-cache, D032#rewrite-one-flow, D033#map-each-api, D035#the-device-fixture, D045#soft-assertions, D047#device, D053#options, D053#types
    term `goto` also in 8: D005#mock-an-api, D016#limits, D027#start-every-test-signed-in, D033#browser-timeouts-and-artifacts, D033#rewrite-one-spec, D033#map-each-api, D051#navigation, D053#browser-interface
- **[ONLY HERE]** - A handler that throws (a failed `expect` on the request, say) fails the next step with that error, or the attempt at its end when no step follows.
    term `expect` also in 102
- **[ONLY HERE]** A handler still running then gets the cleanup budget to finish.
- **[ONLY HERE]** Whatever it throws after the budget is dropped.
- **[ONLY HERE]** | `INVALID_ARGUMENT` | A predicate function as the pattern. Also an option a decision does not take (Playwright's `abort(errorCode)`, a misspelled key): the request is aborted and the next step fails. |
    term `INVALID_ARGUMENT` also in 29
- **[ONLY HERE]** | `ACTION_FAILED` | The handler decided twice or not at all. |
    term `ACTION_FAILED` also in 13
- **[ONLY HERE]** | `POLICY_DENIED` | A `continue` URL with a forbidden scheme. |
    term `POLICY_DENIED` also in 27
    term `continue` also in 10: D005#mock-an-api, D007#how-a-replay-works, D018#replay-cache, D032#rewrite-one-flow, D033#map-each-api, D035#the-device-fixture, D045#soft-assertions, D047#device, D053#options, D053#types
- **[ONLY HERE]** | `CLEANUP_TIMEOUT` | A handler outlived the cleanup budget. It fails the attempt. |
    term `CLEANUP_TIMEOUT` also in 1: D044#runner-codes
- **[ONLY HERE]** Removes the attempt-scoped routes that match a pattern, in the [`route`](#route) pattern syntax.
    term `route` also in 33
- **[ONLY HERE]** | `INVALID_ARGUMENT` | A predicate function as the pattern. |
    term `INVALID_ARGUMENT` also in 29
- **[ONLY HERE]** Waits for a response that matches a pattern, in the [`route`](#route) pattern syntax.
    term `route` also in 33
- **[ONLY HERE]** - The deadline bounds the match: the response resolves as soon as its headers arrive.
- **[ALSO: D045#polling-a-value]** - `text()` and `json()` wait for the body on a budget of their own, `config.actionTimeout` capped by the test deadline.
    term `text()` also in 6: D031#map-each-detox-call, D033#map-each-api, D034#rewrite-one-flow, D034#map-each-webdriver-call, D053#surfaceof, D057#add-a-tool
    term `json()` also in 9: D003#api-testing, D005#write-a-provider, D005#recording-on-the-provider, D032#map-each-command, D033#map-each-api, D035#hosted-devices, D045#value-matchers, D045#valueexpectation, D048#custom-reporters
    term `config.actionTimeout` also in 5: D047#device, D050#screen-actions, D050#locator-actions, D050#locator-reads, D050#types
- **[ONLY HERE]** - `url`, `status`, and `headers` are always readable.
    term `url` also in 140
    term `status` also in 57
    term `headers` also in 23
- **[ONLY HERE]** - A genuinely empty body reads as `''`.
- **[ONLY HERE]** | `INVALID_ARGUMENT` | A predicate function as the pattern. |
    term `INVALID_ARGUMENT` also in 29
- **[ONLY HERE]** | `ACTION_FAILED` | Nothing matches inside the deadline. From `text()` and `json()`: a body still streaming when their budget runs out, or a body the browser could not read (a connection reset short of the declared `Content-Length`, a request the page aborted, or a redirect, whose body the browser never keeps), instead of an empty string. |
    term `ACTION_FAILED` also in 13
    term `text()` also in 6: D031#map-each-detox-call, D033#map-each-api, D034#rewrite-one-flow, D034#map-each-webdriver-call, D053#surfaceof, D057#add-a-tool
    term `json()` also in 9: D003#api-testing, D005#write-a-provider, D005#recording-on-the-provider, D032#map-each-command, D033#map-each-api, D035#hosted-devices, D045#value-matchers, D045#valueexpectation, D048#custom-reporters
- **[ALSO: D053#browser-interface]** Returns the cookies visible to the current context.
- **[ONLY HERE]** Validates every cookie, then sets them.
- **[ALSO: D045#browser-matchers]** - A relative `url` resolves against the base URL, as `goto` resolves it.
    term `url` also in 140
    term `goto` also in 8: D005#mock-an-api, D016#limits, D027#start-every-test-signed-in, D033#browser-timeouts-and-artifacts, D033#rewrite-one-spec, D033#map-each-api, D051#navigation, D053#browser-interface
- **[ONLY HERE]** - For the `domain` form the scheme follows the base URL, and a leading `.` is stripped.
    term `domain` also in 10: D002#instructions-and-vocabulary, D005#cookies, D041#the-app-under-test, D042#app, D042#shared-semantics, D051#site-check, D053#options, D053#weboptions, D054#what-can-still-leak, D059#protected-previews
- **[ONLY HERE]** | `POLICY_DENIED` | An unparseable target or a forbidden scheme. Nothing is set. |
    term `POLICY_DENIED` also in 27
- **[ONLY HERE]** Sets the viewport size and records the new size on the report.
- **[ALSO: D053#options]** - It works before the first navigation too, as Playwright's `setViewportSize` does.
    term `setViewportSize` also in 1: D033#map-each-api
- **[ONLY HERE]** The next `app.open` loads at that size, so a phone-sized test never renders the desktop layout first.
    term `app.open` also in 71
- **[ALSO: D004#the-password-is-a-handle, D005#emulate-dark-mode-and-reduced-motion, D005#mock-an-api, D015#artifacts, D039#screenshot, D046#sessions, D048#custom-reporters, D051#screenshots-after-a-secret-fill, D052#options, D053#options, D053#weboptions, D054#how-secrets-stay-out-of-the-model, D059#resize-inside-a-test]** - The size holds for the rest of the attempt, through `app.restart()` and `app.clearState()`.
    term `app.restart()` also in 14
    term `app.clearState()` also in 20
- **[ALSO: D053#browser-interface]** Registers an attempt-scoped handler for native dialogs and returns an unsubscribe function.
- **[ONLY HERE]** - The handler is `'accept'`, `'dismiss'`, or a function that receives the `Dialog`.
    term `'accept'` also in 6: D005#handle-a-dialog, D030#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D047#device, D050#screen-actions
    term `'dismiss'` also in 1: D047#device
    term `Dialog` also in 23
- **[ONLY HERE]** - A function handler must call `accept` or `dismiss`.
    term `accept` also in 36
    term `dismiss` also in 14
- **[ONLY HERE]** One that does neither has the dialog dismissed, as an unhandled dialog does.
- **[ONLY HERE]** - A handler that throws fails the next step with its error, or the attempt at its end when no step follows.
- **[ONLY HERE]** One that throws before answering has its dialog dismissed.
- **[ONLY HERE]** The errors surface on the next step, not on `onDialog`:
    term `onDialog` also in 7: D005#handle-a-dialog, D025#what-does-not-work, D030#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D051#navigation, D053#browser-interface
- **[ONLY HERE]** | `APP_NOT_OPEN` | A function handler answered neither way, or no handler took the dialog. |
    term `APP_NOT_OPEN` also in 6: D038#agent-act, D039#back, D042#errors, D044#agenterror, D047#device, D060#errors
- **[ONLY HERE]** | `ASSERTION_FAILED` | The handler's `expect` failed. |
    term `ASSERTION_FAILED` also in 15
    term `expect` also in 102
- **[ONLY HERE]** | `ENGINE_FAILURE` | The handler threw an unclassified error. |
    term `ENGINE_FAILURE` also in 13
- **[ALSO: D053#browser-interface]** Runs a trigger and waits for the download it starts.
- **[ALSO: D005#download-a-file]** - It registers the file as a `download` artifact and returns its relative `path`, the runner-side `absolutePath`, and `suggestedFilename`.
    term `download` also in 44
    term `path` also in 116
    term `absolutePath` also in 2: D005#download-a-file, D053#browser-interface
    term `suggestedFilename` also in 1: D053#browser-interface
- **[ONLY HERE]** - Use `absolutePath` with file APIs to inspect the contents, including on a hosted browser.
    term `absolutePath` also in 2: D005#download-a-file, D053#browser-interface
- **[ONLY HERE]** - On a hosted browser the file comes back through the provider's [`downloads`](/browser#downloads-on-the-provider).
    term `downloads` also in 29
- **[ONLY HERE]** - The wait includes the trigger's own time.
- **[ONLY HERE]** | `ACTION_FAILED` | The download did not complete in time. A trigger that resolved in time but started no download fails with `no download started within <n>ms; the trigger resolved after <m>ms`. |
    term `ACTION_FAILED` also in 13
- **[ONLY HERE]** A trigger still running at the timeout fails with the step timeout.
- **[ONLY HERE]** One that throws fails with its own error.
- **[ONLY HERE]** Viewport-level keyboard input, for whatever has focus.
- **[ALSO: D033#map-each-api]** - `type(text)` types plain text only, never a `Secret`.
    term `Secret` also in 123
- **[ONLY HERE]** - Prefer `locator.press` and `locator.fill` when a target exists.
    term `locator.press` also in 3: D026#check-app-compatibility, D042#capabilities, D060#keyboard
    term `locator.fill` also in 3: D038#agent-act, D041#credentials, D041#secrets
- **[ONLY HERE]** - [`Browser`](#browser-interface) describes each method.
    term `Browser` also in 146
- **[ALSO: D053#browser-interface]** Viewport-level pointer input from test code, independent of agent observations.
- **[ONLY HERE]** [`Browser`](#browser-interface) describes each method, `wheel` included.
    term `Browser` also in 146
    term `wheel` also in 3: D033#map-each-api, D047#engine, D053#browser-interface

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D003#signed-in-requests: Both mention browser.cookies() returning cookies of the current context.
- D005#mock-an-api: Both describe browser.route handlers calling exactly one of fulfill, continue, fallback or abort, newest first, surviving restarts.
- D005#handle-a-dialog: Both describe onDialog handlers 'accept', 'dismiss' or a function that must call accept or dismiss.
- D005#download-a-file: Both say waitForDownload saves a download artifact and absolutePath reads it, including on hosted browsers.
- D005#reach-into-an-iframe: Both describe frameLocator scoping queries to a frame and locator inside a frame taking CSS or XPath.
- D005#read-from-the-page: Both say evaluate cannot use test variables and takes data as an argument.
- D005#run-a-script-before-the-page: Both describe addInitScript running before the page's own scripts.
- D005#emulate-dark-mode-and-reduced-motion: Both describe emulateMedia before the page opens for colorScheme and reducedMotion.
- D005#cookies: Both say a cookie URL that does not parse or has a scheme other than http or https is POLICY_DENIED.
- D005#downloads-on-the-provider: Both say a hosted browser's download comes back through the provider's downloads option.
- D005#shadow-dom: Both say locator and filter({ hasText }) stop at a closed shadow root while screen queries reach into it.
- D015#common-errors: Both point to browser.frameLocator for elements inside an iframe.
- D024#downloads: Both say waitForDownload works as it does locally on Kernel browsers.
- D030#map-each-command: Both map Cypress intercept, visit and cookie commands to browser.route, goto and setCookies.
- D033#map-each-api: Both map page.route, waitForResponse, onDialog, waitForDownload, evaluate, cookies and setViewport to the browser fixture.
- D033#port-page-objects: Both say browser.keyboard types plain text only and requires: ['browser'] guards other targets.
- D034#map-each-webdriver-call: Both map WebDriver navigation, frame and dialog calls to browser.goto, frameLocator and onDialog.
- D039#open: Both say a relative URL needs the target's app.url, else APP_URL_REQUIRED, and a non-http scheme is POLICY_DENIED.
- D044#runner-codes: Both define EVALUATE_FAILED and APP_URL_REQUIRED.
- D045#browser-matchers: Both describe expect(browser) matchers toHaveURL, toHaveTitle and toHaveClass.
- D050#locator-reads: Both mention frame and locator errors such as LOCATOR_NOT_FOUND and LOCATOR_AMBIGUOUS.
- D051#navigation: Both say browser.goto allows only http, https and about:blank.
- D053#browser-interface: Both describe the Browser methods, active tab scope, keyboard and mouse input and evaluate.
- D059#resize-inside-a-test: Both say setViewport resizes the page for the rest of the attempt.

## S42 · multi-section · D047#device  (Mobile › Reference › Device; page title: Mobile)

Regel: mindestens zwei Abschnitte, jeder liefert einen nötigen Teil; enthaltene oder umschließende Abschnitte zählen nicht als zweiter; H1 nur mit Grund in `notes`.

**Typ-Eignung:** Ziel `conceptual`: warum Berechtigungen vor dem Start der App gesetzt werden. Hier: `setPermission` „A change terminates a running app on iOS, a revoke one on Android, so it goes before the `app.open()` a test starts with“. Zweiter Abschnitt mit eigenem Teil: D047#engine (Launch arguments and permissions): `app.permissions` „ride every fresh launch of the pinned app: `app.open()`, `app.restart()`, and `app.clearState()`“ (`find "ride every"`: nur dort) und dieselbe Begründung („since iOS terminates a running app whose permission changed and Android one whose permission was revoked“; `find "terminates a running app"`: nur diese beiden). Vorsicht: D041#the-app-under-test sagt „Permissions the app holds on every fresh launch“ und ist dann relevant, wenn die Antwort diesen Teil nennt. Verworfen: der Grund für `offline` auf iOS (Simulator teilt das Netz des Mac) steht auch in D035#the-device-fixture; `clearKeychain` ebenso (D035#the-device-fixture, D035#physical-devices); die `transition`-Begründung steht ganz in D047#engine, das die betroffenen `device`-Methoden selbst aufzählt, so dass D047#device keinen eigenen Teil liefert.

- **[ONLY HERE]** The `device` fixture is deterministic device management.
    term `device` also in 122
- **[ONLY HERE]** A test calls it directly to arrange or assert device state.
- **[ONLY HERE]** | [`locator`](#locator) | `Locator` |
    term `locator` also in 110
    term `Locator` also in 110
- **[ONLY HERE]** | [`setNetwork`](#setnetwork) | `Promise<void>` |
    term `setNetwork` also in 2: D035#the-device-fixture, D060#contributed-fixtures
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`setAirplaneMode`](#setairplanemode) | `Promise<void>` |
    term `setAirplaneMode` also in 2: D032#map-each-command, D035#the-device-fixture
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`setPermission`](#setpermission) | `Promise<void>` |
    term `setPermission` also in 2: D032#map-each-command, D035#physical-devices
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`setLocation`](#setlocation) | `Promise<void>` |
    term `setLocation` also in 3: D031#map-each-detox-call, D032#map-each-command, D035#physical-devices
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`clearLocation`](#clearlocation) | `Promise<void>` |
    term `clearLocation` also in 1: D035#physical-devices
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`setAppearance`](#setappearance) | `Promise<void>` |
    term `setAppearance` also in 3: D032#map-each-command, D035#write-a-device-test, D035#physical-devices
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`setOrientation`](#setorientation) | `Promise<void>` |
    term `setOrientation` also in 4: D031#map-each-detox-call, D032#map-each-command, D047#engine, D047#device-fixture
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`fold`](#fold) | `Promise<void>` |
    term `fold` also in 22
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`setBiometrics`](#setbiometrics) | `Promise<void>` |
    term `setBiometrics` also in 3: D031#map-each-detox-call, D035#physical-devices, D047#device-fixture
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`enrollBiometrics`](#enrollbiometrics) | `Promise<void>` |
    term `enrollBiometrics` also in 1: D031#map-each-detox-call
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`installApp`](#installapp) | `Promise<InstalledApp>` |
    term `installApp` also in 10: D008#mobile-jobs, D022#install-the-app, D031#port-the-config, D035#point-at-your-app, D035#the-device-fixture, D035#physical-devices, D035#troubleshooting, D047#engine, D047#device-fixture, D047#exported-types
- **[ONLY HERE]** | [`openApp`](#openapp) | `Promise<void>` |
    term `openApp` also in 10: D031#port-the-config, D032#port-the-config, D032#map-each-command, D035#launch-arguments-and-permissions, D035#the-device-fixture, D047#engine, D047#agent-tools, D047#device-fixture, D047#exported-types, D051#navigation
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`openLink`](#openlink) | `Promise<void>` |
    term `openLink` also in 9: D032#map-each-command, D035#expo-development-builds, D035#the-device-fixture, D035#physical-devices, D035#what-differs-from-the-web, D041#the-app-under-test, D047#engine, D047#replay-cache-on-a-device, D051#navigation
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`closeApp`](#closeapp) | `Promise<void>` |
    term `closeApp` also in 2: D032#map-each-command, D047#engine
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`clearKeychain`](#clearkeychain) | `Promise<void>` |
    term `clearKeychain` also in 3: D032#map-each-command, D035#the-device-fixture, D035#physical-devices
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`foregroundApp`](#foregroundapp) | `Promise<ForegroundApp>` |
    term `foregroundApp` also in 3: D035#known-device-limitations, D047#device-fixture, D047#exported-types
- **[ONLY HERE]** | [`home`](#home) | `Promise<void>` |
    term `home` also in 25
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`back`](#back) | `Promise<void>` |
    term `back` also in 77
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`alert`](#alert) | `Promise<void>` |
    term `alert` also in 15
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`dismissKeyboard`](#dismisskeyboard) | `Promise<void>` |
    term `dismissKeyboard` also in 3: D018#what-the-context-holds, D032#map-each-command, D047#engine
    term `Promise<void>` also in 26
- **[ONLY HERE]** | [`clipboard`](#clipboard) | `Promise<string>` |
    term `clipboard` also in 2: D032#map-each-command, D035#physical-devices
    term `Promise<string>` also in 9: D039#reference, D039#types, D041#credentialconfig, D042#lifecycle, D042#artifacts, D050#locator-reads, D053#options, D053#the-browser-fixture, D053#browser-interface
- **[ONLY HERE]** | [`setClipboard`](#setclipboard) | `Promise<void>` |
    term `setClipboard` also in 2: D032#map-each-command, D035#physical-devices
    term `Promise<void>` also in 26
- **[ONLY HERE]** Every async method is a recorded step named `device.<method>`, bounded by `config.actionTimeout`.
    term `device.<method>` also in 1: D035#the-device-fixture
    term `config.actionTimeout` also in 5: D050#screen-actions, D050#locator-actions, D050#locator-reads, D050#types, D053#the-browser-fixture
- **[ALSO: D047#engine]** `back`, `home`, `alert`, `dismissKeyboard`, `setOrientation`, and `fold` count as actions for the [`transition`](#transition) budget.
    term `back` also in 77
    term `home` also in 25
    term `alert` also in 15
    term `dismissKeyboard` also in 3: D018#what-the-context-holds, D032#map-each-command, D047#engine
    term `setOrientation` also in 4: D031#map-each-detox-call, D032#map-each-command, D047#engine, D047#device-fixture
    term `fold` also in 22
    term `transition` also in 4: D031#rewrite-one-spec, D032#map-each-command, D042#engine, D047#engine
- **[ALSO: D047#engine]** Each entry below shows its member's declaration; the types they use are under [Types](#device-fixture).
- **[ONLY HERE]** | `APP_NOT_OPEN` | The session is lost. |
    term `APP_NOT_OPEN` also in 6: D038#agent-act, D039#back, D042#errors, D044#agenterror, D053#the-browser-fixture, D060#errors
- **[ONLY HERE]** | `ACTION_FAILED` | `actionTimeout` expires. |
    term `ACTION_FAILED` also in 13
    term `actionTimeout` also in 16
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | The platform cannot run the command. |
    term `UNSUPPORTED_CAPABILITY` also in 32
- **[ALSO: D044#agenterror]** | `ENGINE_FAILURE` | Anything else, with agent-device's message. A timeout the device itself reports (a boot, the runner connecting) keeps its text and hint there. A busy or wedged iOS automation runner names itself and the recovery (see [Troubleshooting](/mobile#troubleshooting)). |
    term `ENGINE_FAILURE` also in 13
- **[ONLY HERE]** Selector terms and their rules are agent-device's, the ones `agent-device find ... list` applies:
- **[ONLY HERE]** - Terms: `id`, `role`, `text`, `label`, `value`, `appname`, `windowtitle`, and the flags `visible`, `hidden`, `editable`, `selected`, `focused`, `enabled`, `hittable`.
    term `role` also in 69
    term `text` also in 190
    term `label` also in 76
    term `value` also in 141
    term `visible` also in 62
    term `hidden` also in 25
    term `editable` also in 11
    term `selected` also in 24
    term `focused` also in 16
    term `enabled` also in 13
- **[ONLY HERE]** - `role` takes agent-device's kind, the role `agent-device snapshot` prints: `button`, `text`, `text-field`, `navigation-bar`, `scroll-area`, `switch`, `image`.
    term `role` also in 69
    term `button` also in 49
    term `text` also in 190
    term `navigation-bar` also in 2: D035#write-a-device-test, D037#add-an-agent-step
    term `scroll-area` also in 1: D035#known-device-limitations
    term `switch` also in 22
    term `image` also in 37
- **[ONLY HERE]** It is not the `getByRole` role (`textbox`).
    term `getByRole` also in 53
    term `textbox` also in 8: D015#traces, D033#map-each-api, D035#write-a-device-test, D047#engine, D050#queries, D050#locator-actions, D050#types, D051#policy-denials
- **[ONLY HERE]** - Text terms compare case-insensitively after collapsing whitespace.
- **[ONLY HERE]** - `visible` means the node is hittable or has a non-empty frame; `hidden` is its opposite.
    term `visible` also in 62
    term `hidden` also in 25
- **[ONLY HERE]** - `text` reads the first non-empty label, value, or identifier.
    term `text` also in 190
- **[ONLY HERE]** **Note** An action on a selector that matches several nodes fails, where an agent-device action skips an ambiguous `||` alternative.
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | `offline` on iOS. |
    term `UNSUPPORTED_CAPABILITY` also in 32
    term `offline` also in 4: D013#install-the-skill, D033#browser-timeouts-and-artifacts, D035#the-device-fixture, D060#contributed-fixtures
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | `true` on iOS. |
    term `UNSUPPORTED_CAPABILITY` also in 32
    term `true` also in 86
- **[ALSO: D041#the-app-under-test, D047#engine]** - `permission` is a [`DevicePermission`](#device-fixture); `state` is `grant`, `deny`, or `reset`.
    term `permission` also in 30
    term `DevicePermission` also in 4: D047#engine, D047#engine-options, D047#device-fixture, D047#exported-types
    term `state` also in 93
    term `grant` also in 12
    term `deny` also in 8: D031#port-the-config, D032#map-each-command, D035#launch-arguments-and-permissions, D041#the-app-under-test, D042#app, D047#engine, D047#engine-options, D047#device-fixture
    term `reset` also in 24
- **[ONLY HERE]** - `'portrait'`, `'portrait-upside-down'`, `'landscape-left'`, or `'landscape-right'`.
    term `'portrait'` also in 2: D028#options, D047#device-fixture
    term `'portrait-upside-down'` also in 1: D047#device-fixture
    term `'landscape-left'` also in 3: D031#map-each-detox-call, D032#map-each-command, D047#device-fixture
    term `'landscape-right'` also in 1: D047#device-fixture
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | The device has no hinge. |
    term `UNSUPPORTED_CAPABILITY` also in 32
- **[ONLY HERE]** - `sensor` is `'faceid'`, `'touchid'`, or `'fingerprint'`.
    term `sensor` also in 2: D047#device-fixture, D047#exported-types
    term `'faceid'` also in 2: D031#map-each-detox-call, D047#device-fixture
    term `'touchid'` also in 1: D047#device-fixture
    term `'fingerprint'` also in 2: D035#physical-devices, D047#device-fixture
- **[ONLY HERE]** - Use it for the run's build, or for another build on an upgrade path.
- **[ALSO: D035#troubleshooting, D047#device-fixture]** - The resolved id is the bundle id or package agent-device read from the build, else the `app` passed in.
    term `app` also in 306
- **[ONLY HERE]** | `ENGINE_FAILURE` | agent-device reported no id and no `app` was passed, instead of a file path posing as an id. See [Troubleshooting](/mobile#troubleshooting). |
    term `ENGINE_FAILURE` also in 13
    term `app` also in 306
- **[ONLY HERE]** - A link is refused before the device sees it, since agent-device opens any `scheme:rest` string as a URL.
- **[ALSO: D041#the-app-under-test, D051#navigation]** | `POLICY_DENIED` | A `file:`, `data:`, `javascript:`, `view-source:`, `blob:`, or `filesystem:` link. |
    term `POLICY_DENIED` also in 27
    term `file:` also in 13
    term `data:` also in 7: D041#the-app-under-test, D042#state, D046#the-catalog, D051#policy-denials, D051#navigation, D051#site-check, D056#telemetry
    term `javascript:` also in 4: D041#the-app-under-test, D046#the-catalog, D051#policy-denials, D051#navigation
    term `view-source:` also in 3: D041#the-app-under-test, D051#policy-denials, D051#navigation
    term `blob:` also in 3: D041#the-app-under-test, D046#the-catalog, D051#navigation
    term `filesystem:` also in 1: D051#navigation
- **[ONLY HERE]** | `INVALID_ARGUMENT` | Any other link, with a message pointing at `openLink`; or an invalid permission name or state (see [Launch arguments and permissions](#launch-arguments-and-permissions)). |
    term `INVALID_ARGUMENT` also in 29
    term `openLink` also in 9: D032#map-each-command, D035#expo-development-builds, D035#the-device-fixture, D035#physical-devices, D035#what-differs-from-the-web, D041#the-app-under-test, D047#engine, D047#replay-cache-on-a-device, D051#navigation
- **[ALSO: D035#the-device-fixture]** - Use it for magic-link sign-in and deep-link routes.
- **[ONLY HERE]** - Without an app, Android routes the link to a verified app link owner or the browser, and the session follows the package that took it.
- **[ONLY HERE]** - A device link may use any app's custom scheme, so the rule refuses the schemes below rather than admitting http(s) alone as the web does.
- **[ONLY HERE]** - The report shows the link cut before its query and fragment, where a magic link carries its token.
- **[ALSO: D035#what-differs-from-the-web, D047#replay-cache-on-a-device]** - The replay cache anchors on the location the link lands on; see [Replay cache on a device](#replay-cache-on-a-device).
- **[ALSO: D041#the-app-under-test, D051#navigation]** | `POLICY_DENIED` | A `file:`, `data:`, `javascript:`, `view-source:`, `blob:`, or `filesystem:` link. |
    term `POLICY_DENIED` also in 27
    term `file:` also in 13
    term `data:` also in 7: D041#the-app-under-test, D042#state, D046#the-catalog, D051#policy-denials, D051#navigation, D051#site-check, D056#telemetry
    term `javascript:` also in 4: D041#the-app-under-test, D046#the-catalog, D051#policy-denials, D051#navigation
    term `view-source:` also in 3: D041#the-app-under-test, D051#policy-denials, D051#navigation
    term `blob:` also in 3: D041#the-app-under-test, D046#the-catalog, D051#navigation
    term `filesystem:` also in 1: D051#navigation
- **[ONLY HERE]** | `INVALID_ARGUMENT` | No app on iOS: an open bound to none leaves no app session to observe. |
    term `INVALID_ARGUMENT` also in 29
- **[ONLY HERE]** | `INVALID_ARGUMENT` | A string that does not parse as an absolute URL. The message names no part of the input, which may carry a magic-link token in its query, path, or userinfo. |
    term `INVALID_ARGUMENT` also in 29
- **[ONLY HERE]** - A screen query before the next `openApp` is `APP_NOT_OPEN` too.
    term `openApp` also in 10: D031#port-the-config, D032#port-the-config, D032#map-each-command, D035#launch-arguments-and-permissions, D035#the-device-fixture, D047#engine, D047#agent-tools, D047#device-fixture, D047#exported-types, D051#navigation
    term `APP_NOT_OPEN` also in 6: D038#agent-act, D039#back, D042#errors, D044#agenterror, D053#the-browser-fixture, D060#errors
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | On Android, before any device command. |
    term `UNSUPPORTED_CAPABILITY` also in 32
- **[ONLY HERE]** - On iOS, agent-device's `appstate` has no device-level answer.
- **[ONLY HERE]** | `APP_NOT_OPEN` | `closeApp` ended the session. |
    term `APP_NOT_OPEN` also in 6: D038#agent-act, D039#back, D042#errors, D044#agenterror, D053#the-browser-fixture, D060#errors
    term `closeApp` also in 2: D032#map-each-command, D047#engine
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | The keyboard outlives both drags. |
    term `UNSUPPORTED_CAPABILITY` also in 32

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D031#map-each-detox-call: Both give device.setLocation, setOrientation, enrollBiometrics, setBiometrics, home, back, and locator forms.
- D032#map-each-command: Both map device.openApp, closeApp, clearKeychain (iOS only), openLink and locator, with launch arguments and permissions.
- D035#launch-arguments-and-permissions: Both describe device.openApp with relaunch, launchArguments and permissions for one launch.
- D035#expo-development-builds: Both describe opening an Expo build with device.openLink.
- D035#write-a-device-test: Both show device.setAppearance and device.locator inside a device test.
- D035#the-device-fixture: Both describe the device fixture: locator with agent-device selectors, installApp reinstall, openApp taking an app id not a link.
- D035#physical-devices: Both state which device methods (setPermission, setLocation, setAppearance, biometrics, clearKeychain, clipboard, fold) work or not on physical devices.
- D035#what-differs-from-the-web: Both mention device.openLink opening a link into the app and foregroundApp/home/fold behaviour.
- D035#known-device-limitations: Both note device.foregroundApp still naming the app after home on iOS, fold, and locator for scroll-area.
- D035#troubleshooting: Both describe device.installApp on Android failing to report a bundle id or package.
- D047#engine: Both describe device.openApp with relaunch, launchArguments and permissions, openLink, installApp, and closeApp ending the session.
- D047#agent-tools: Both state open_app / device.openApp take an app id and refuse a link.
- D047#replay-cache-on-a-device: Both state a step recorded after device.openLink replays when the link matches.
- D047#device-fixture: Both define the device fixture's method signatures and types (fold, installApp, openApp, biometrics).
- D051#navigation: Both state device.openLink takes any absolute URL and device.openApp an app id, never a link.

## S43 · paraphrase · D047#engine  (Mobile › Reference › Engine; page title: Mobile)

Regel: genau ein Abschnitt; die Frage teilt kein Inhaltswort mit der Abschnittsüberschrift oder dem Seitentitel (auch keine Wortformen).

**Typ-Eignung:** Ziel `limitation`: Note „agent-device commands take no abort signal, so a timed-out command keeps running on the device. The next attempt waits for it to settle.“ (`find "no abort signal"`: nur hier). Für `paraphrase` darf die Frage nicht engine, mobile oder reference enthalten (Überschrift „Engine“, Seitentitel „Mobile“), auch keine Wortformen. Alternative `comparative`: `snapshot` `full` gegen `interactive` („`full` (default) includes static text, so judgments can read values; `interactive` keeps only actionable nodes and is cheaper on screens with long lists“); `snapshot` als Wort steht in vielen Abschnitten, die beiden Modi mit Begründung habe ich nur hier gefunden. Verworfen: Boot in `prepare` („never charged against `launchTimeout`“) steht auch in D035#set-up („doesn't count toward `launchTimeout`“).

- **[ONLY HERE]** `mobile(options)` creates an engine for one platform.
- **[ALSO: D035#several-devices]** Create one for each platform you test, and use `platforms: ['ios']` or `platforms: ['android']` on tests with platform-specific labels or operations.
    term `platforms: ['ios']` also in 3: D031#map-each-detox-call, D035#several-devices, D052#options
    term `platforms: ['android']` also in 3: D035#the-device-fixture, D035#several-devices, D047#device
- **[ONLY HERE]** **e2e.config.ts**
- **[ONLY HERE]** `mobile()` takes `MobileOptions`: which devices the engine drives and how.
    term `mobile()` also in 3: D008#mobile-jobs, D041#the-app-under-test, D044#runner-codes
    term `MobileOptions` also in 2: D047#engine-options, D047#exported-types
- **[ALSO: D042#app, D060#the-shape-of-an-engine]** The app under test is the target's `app`, not an engine option; see [The app under test](#the-app-under-test).
    term `app` also in 306
- **[ONLY HERE]** | [`platform`](#platform) | `'ios' \| 'android'` | required |
    term `platform` also in 82
- **[ONLY HERE]** | [`device`](#device-option) | `string \| readonly string[] \| DeviceProvider` | every booted device |
    term `device` also in 122
- **[ONLY HERE]** | [`session`](#session) | `string` | `e2e-<target name>` |
    term `session` also in 126
    term `string` also in 111
- **[ONLY HERE]** | [`snapshot`](#snapshot) | `'full' \| 'interactive'` | `'full'` |
    term `snapshot` also in 28
- **[ONLY HERE]** | [`settle`](#settle) | `number \| false` | `150` |
    term `settle` also in 14
    term `150` also in 1: D040#commands
- **[ONLY HERE]** | [`transition`](#transition) | `number` | `500` |
    term `transition` also in 4: D031#rewrite-one-spec, D032#map-each-command, D042#engine, D047#device
    term `number` also in 60
    term `500` also in 9: D015#traces, D038#agent-waitfor, D040#commands, D041#top-level, D041#e2econfig, D042#lifecycle, D045#polling-a-value, D045#polloptions-and-pollexpectation, D050#locator-actions
- **[ONLY HERE]** | [`videoTouches`](#videotouches) | `boolean` | `true` |
    term `videoTouches` also in 3: D022#setup, D022#recordings, D035#what-differs-from-the-web
    term `boolean` also in 39
    term `true` also in 86
- **[ONLY HERE]** Every optional value also accepts `undefined`, so values read straight from `process.env` need no conditional spread.
    term `undefined` also in 30
    term `process.env` also in 26
- **[ALSO: D047#device]** Each entry below shows its member's declaration.
- **[ONLY HERE]** | `INVALID_CONFIG` | An empty `device` list. |
    term `INVALID_CONFIG` also in 42
    term `device` also in 122
- **[ALSO: D042#shared-semantics, D044#runner-codes, D053#options]** | `INVALID_CONFIG` | An option `mobile()` does not take, such as `mobile({ app })` and the other old app options. The message names the nearest known option for a likely typo, else every option. |
    term `INVALID_CONFIG` also in 42
    term `mobile()` also in 3: D008#mobile-jobs, D041#the-app-under-test, D044#runner-codes
    term `mobile({ app })` also in 1: D041#the-app-under-test
- **[ONLY HERE]** | `INVALID_CONFIG` | `settle` or `transition` is not a non-negative integer of milliseconds (`settle` may also be `false`). |
    term `INVALID_CONFIG` also in 42
    term `settle` also in 14
    term `transition` also in 4: D031#rewrite-one-spec, D032#map-each-command, D042#engine, D047#device
    term `false` also in 60
- **[ONLY HERE]** - `'ios'` or `'android'`.
    term `'ios'` also in 17
    term `'android'` also in 11
- **[ONLY HERE]** Required.
- **[ALSO: D035#several-devices]** - Two workers never drive the same device, as long as each `device` entry names a different one.
    term `device` also in 122
- **[ALSO: D053#options]** - [Hosted devices](/mobile#hosted-devices) has the `DeviceProvider` contract and an example provider.
    term `DeviceProvider` also in 5: D023#use-a-service-with-no-integration, D035#hosted-devices, D041#recording, D042#artifacts, D047#exported-types
- **[ONLY HERE]** **e2e.config.ts**
- **[ALSO: D047#device]** `back`, `home`, `alert`, `dismissKeyboard`, `setOrientation`, and `fold` on [`device`](#device) change the screen, so they count as actions for this budget the way a tap does.
    term `back` also in 77
    term `home` also in 25
    term `alert` also in 15
    term `dismissKeyboard` also in 3: D018#what-the-context-holds, D032#map-each-command, D047#device
    term `setOrientation` also in 4: D031#map-each-detox-call, D032#map-each-command, D047#device, D047#device-fixture
    term `fold` also in 22
    term `device` also in 122
- **[ONLY HERE]** A control that arrives with the screen they reveal waits out the budget before the next action lands on it.
- **[ALSO: D042#app, D053#options]** The app is the target's `app`: `bundleId`, `appPath`, `launchArguments`, `permissions`, `identity`, and `environment` are documented under [the app under test](/reference/config#the-app-under-test).
    term `app` also in 306
    term `bundleId` also in 32
    term `appPath` also in 16
    term `launchArguments` also in 10: D031#port-the-config, D032#map-each-command, D035#launch-arguments-and-permissions, D035#expo-development-builds, D035#physical-devices, D041#the-app-under-test, D042#app, D047#device, D047#device-fixture, D053#options
    term `permissions` also in 22
    term `identity` also in 24
    term `environment` also in 52
- **[ONLY HERE]** **e2e.config.ts**
- **[ALSO: D041#the-app-under-test]** - A device target needs `app.bundleId` or `app.appPath`.
    term `app.bundleId` also in 14
    term `app.appPath` also in 10: D008#mobile-jobs, D028#setup, D035#point-at-your-app, D035#physical-devices, D035#hosted-devices, D041#the-app-under-test, D042#capabilities, D044#runner-codes, D047#device, D052#options
- **[ONLY HERE]** - `app.open()` launches the target's app fresh.
    term `app.open()` also in 35
- **[ALSO: D037#add-an-agent-step, D047#device]** An attempt launches nothing on its own, so a test starts where the previous one left the app.
- **[ONLY HERE]** - `app.open` takes no path on a device: a link goes through [`device.openLink`](#openlink).
    term `app.open` also in 71
    term `device.openLink` also in 9: D032#map-each-command, D035#expo-development-builds, D035#the-device-fixture, D035#physical-devices, D035#what-differs-from-the-web, D041#the-app-under-test, D047#device, D047#replay-cache-on-a-device, D051#navigation
- **[ALSO: D041#the-app-under-test]** - `app.appPath` is the build the suite runs against.
    term `app.appPath` also in 10: D008#mobile-jobs, D028#setup, D035#point-at-your-app, D035#physical-devices, D035#hosted-devices, D041#the-app-under-test, D042#capabilities, D044#runner-codes, D047#device, D052#options
- **[ALSO: D031#port-the-config, D035#point-at-your-app, D047#device]** The engine installs nothing on its own: [`device.installApp()`](#installapp) installs it where the suite says so.
    term `device.installApp()` also in 6: D008#mobile-jobs, D022#install-the-app, D031#port-the-config, D035#point-at-your-app, D035#troubleshooting, D047#device
- **[ONLY HERE]** A device provider installs it on the device it leases.
- **[ALSO: D047#device]** - Without `bundleId`, the installed bundle id or package becomes the app `app.open()` launches.
    term `bundleId` also in 32
    term `app.open()` also in 35
- **[ONLY HERE]** - Declare an `identity` when the build path changes per run (a version in it), so recordings survive the rename.
    term `identity` also in 24
- **[ALSO: D041#the-app-under-test]** | `INVALID_CONFIG` | At config load: no `app.bundleId` and no `app.appPath`; an `app.url` (not supported yet); a link in `bundleId` (a test opens one with `device.openLink`); an unknown permission name. |
    term `INVALID_CONFIG` also in 42
    term `app.bundleId` also in 14
    term `app.appPath` also in 10: D008#mobile-jobs, D028#setup, D035#point-at-your-app, D035#physical-devices, D035#hosted-devices, D041#the-app-under-test, D042#capabilities, D044#runner-codes, D047#device, D052#options
    term `app.url` also in 19
    term `bundleId` also in 32
    term `device.openLink` also in 9: D032#map-each-command, D035#expo-development-builds, D035#the-device-fixture, D035#physical-devices, D035#what-differs-from-the-web, D041#the-app-under-test, D047#device, D047#replay-cache-on-a-device, D051#navigation
- **[ALSO: D041#the-app-under-test]** `app.launchArguments` and `app.permissions` ride every fresh launch of the pinned app: `app.open()`, `app.restart()`, and `app.clearState()`, which resets the permissions with the data.
    term `app.launchArguments` also in 5: D031#port-the-config, D032#map-each-command, D035#launch-arguments-and-permissions, D035#physical-devices, D047#device-fixture
    term `app.permissions` also in 5: D031#port-the-config, D032#map-each-command, D035#launch-arguments-and-permissions, D035#physical-devices, D047#device-fixture
    term `app.open()` also in 35
    term `app.restart()` also in 14
    term `app.clearState()` also in 20
- **[ONLY HERE]** **e2e.config.ts**
- **[ONLY HERE]** - iOS hands the arguments to the app process (`ProcessInfo.processInfo.arguments`).
- **[ONLY HERE]** Android appends them to `am start`, so `['--ez', 'e2e', 'true']` is a boolean intent extra.
    term `am start` also in 2: D035#launch-arguments-and-permissions, D047#device-fixture
- **[ALSO: D041#the-app-under-test, D047#device]** - Each permission is `grant`, `deny`, or `reset`.
    term `grant` also in 12
    term `deny` also in 8: D031#port-the-config, D032#map-each-command, D035#launch-arguments-and-permissions, D041#the-app-under-test, D042#app, D047#device, D047#engine-options, D047#device-fixture
    term `reset` also in 24
- **[ONLY HERE]** `deny` is a recorded refusal on iOS, where the app is told no without a prompt, and a revocation on Android, where the OS asks again when the app requests the permission.
    term `deny` also in 8: D031#port-the-config, D032#map-each-command, D035#launch-arguments-and-permissions, D041#the-app-under-test, D042#app, D047#device, D047#engine-options, D047#device-fixture
- **[ONLY HERE]** - The permissions are set on the app by name before it starts, with no open first, since iOS terminates a running app whose permission changed and Android one whose permission was revoked.
- **[ONLY HERE]** - The warm-up passes no launch argument and touches no permission.
- **[ALSO: D031#port-the-config, D032#map-each-command]** - [`device.openApp(app, { relaunch: true, launchArguments, permissions })`](#openapp) does the same for one launch of any app.
- **[ALSO: D052#options]** | `INVALID_CONFIG` | In `app.permissions`: a permission name outside `DevicePermission` (naming the nearest one when it is a likely typo), or a state other than `grant`, `deny`, or `reset`. Fails before any device command. |
    term `INVALID_CONFIG` also in 42
    term `app.permissions` also in 5: D031#port-the-config, D032#map-each-command, D035#launch-arguments-and-permissions, D035#physical-devices, D047#device-fixture
    term `DevicePermission` also in 4: D047#device, D047#engine-options, D047#device-fixture, D047#exported-types
    term `grant` also in 12
    term `deny` also in 8: D031#port-the-config, D032#map-each-command, D035#launch-arguments-and-permissions, D041#the-app-under-test, D042#app, D047#device, D047#engine-options, D047#device-fixture
    term `reset` also in 24
- **[ONLY HERE]** | `INVALID_ARGUMENT` | The same, in `device.openApp`. |
    term `INVALID_ARGUMENT` also in 29
    term `device.openApp` also in 9: D031#port-the-config, D032#port-the-config, D032#map-each-command, D035#launch-arguments-and-permissions, D035#the-device-fixture, D047#device, D047#agent-tools, D047#device-fixture, D051#navigation
- **[ALSO: D022#sessions, D042#lifecycle, D053#installing-browsers]** Devices boot in `prepare`, once per run and before the run's clock starts, so a cold boot on CI is never charged against `launchTimeout`.
    term `prepare` also in 19
    term `launchTimeout` also in 5: D035#set-up, D041#top-level, D041#e2econfig, D042#lifecycle, D044#runner-codes
- **[ONLY HERE]** - [`device`](#device-option) says which devices `prepare` uses and how many workers the engine declares.
    term `device` also in 122
    term `prepare` also in 19
- **[ONLY HERE]** - On iOS, `prepare` starts the automation runner on every device with agent-device's `prepare ios-runner`, so its first launch is paid before the first test.
    term `prepare` also in 19
- **[ONLY HERE]** Then it brings the target's `app.bundleId` up once per device when it is installed.
    term `app.bundleId` also in 14
- **[ONLY HERE]** A build the suite installs itself comes up with the first `app.open()`, which relaunches it fresh whenever a test asks.
    term `app.open()` also in 35
- **[ONLY HERE]** - A device that cannot boot, or a runner that is busy, wedged, or past its watchdog, ends the run in `prepare`.
    term `prepare` also in 19
- **[ONLY HERE]** - A runner that does not start for another reason is logged and left to the first attempt, and that device's app is not opened there.
- **[ONLY HERE]** **Note** agent-device commands take no abort signal, so a timed-out command keeps running on the device.
- **[ONLY HERE]** The next attempt waits for it to settle.
- **[ONLY HERE]** | `observe` | The accessibility tree with rects. iOS: `Button` is `button`, `TextField` and `SearchField` are `textbox`, `SecureTextField` is a secure `textbox`, `Cell` is `listitem`, `StaticText` is `text`, `Switch` is `switch` with `checked`, `TabBar` and `SegmentedControl` are `tablist` and the buttons inside them `tab`, `ProgressIndicator` is `progressbar`, `ActivityIndicator` is `status`, `Stepper` is `spinbutton`, `Toolbar`, `Menu`, and `RadioGroup` are `toolbar`, `menu`, and `radiogroup`. Android: `TextView` is `text`, `EditText` is `textbox` and one UIAutomator flags as `password` is a secure `textbox` like `SecureTextField`, `Switch` and `CheckBox` keep their roles and `RadioButton` is `radio`, each with the `checked` state the device reports, layouts are `group`, `RecyclerView` and `AbsListView` (React Native's `FlatList`) are `list`, `TabLayout` and `BottomNavigationView` are `tablist` with their items as `tab`, `ProgressBar` is `progressbar`, `NumberPicker` is `spinbutton`, `Toolbar` and `RadioGroup` keep their names. Any other type is kept verbatim in lower case (`picker-wheel`), so it answers no vocabulary role, unless the platform reports it editable, which makes it a `textbox`. React Native on iOS has no trait for `checkbox`, `radio`, and a few other roles and spells the role and state into the accessibility value instead (`checkbox, unchecked`, `radio button, checked`); such a node takes that role, `checked` and `expanded` from the state words, and reports only what follows them as its value. An iOS field keeps a value equal to its label (an unlabeled field is named by its text); Android's echo of a text view's label as its value is dropped. The accessibility identifier (iOS) or resource id (Android) is the node's `testId`. An Android node is named by the content description its app set (React Native's `accessibilityLabel`), else by its text, and its `text` is what it shows, so a labeled text view or a filled field answers `getByLabel` by its label and `getByText` by its text; a view flagged as a heading is a `heading`, and the role description React Native writes for a role Android has no class for (`Tab`, `Tab List`, `Radio Group`) gives the node that role. A field's hint is its `placeholder` attribute, showing or not. One Android fact is agent-device's, not the platform's: `rect` and every point are the screen's physical pixels; the display density it reports is not applied yet. Android's status bar and navigation bar, the full-width `com.android.systemui` windows along the screen's edges and the narrow status icons (clock, signal, battery) agent-device reports on their own inside that edge band, are left out; the notification shade, system dialogs, and a heads-up notification or other popup inset from the sides stay. Pixels on request, with every secure node's bounds painted black. |
    term `observe` also in 42
    term `Button` also in 49
    term `button` also in 49
    term `textbox` also in 8: D015#traces, D033#map-each-api, D035#write-a-device-test, D047#device, D050#queries, D050#locator-actions, D050#types, D051#policy-denials
    term `Cell` also in 37
    term `listitem` also in 10: D014#locators, D015#traces, D030#map-each-command, D035#write-a-device-test, D046#the-catalog, D050#reference-screen, D050#queries, D050#refinement, D050#locator-reads, D050#types
    term `StaticText` also in 1: D050#queries
    term `text` also in 190
    term `Switch` also in 22
    term `switch` also in 22
    term `checked` also in 25
    term `tablist` also in 2: D050#queries, D050#types
    term `tab` also in 79
    term `progressbar` also in 2: D050#queries, D050#types
    term `status` also in 57
    term `Stepper` also in 1: D050#queries
    term `spinbutton` also in 2: D050#queries, D050#types
    term `Toolbar` also in 2: D035#what-differs-from-the-web, D050#types
    term `Menu` also in 9: D002#instructions-and-vocabulary, D014#goals, D016#what-the-model-can-do, D025#what-works, D035#expo-development-builds, D038#action-tools, D050#queries, D050#types, D059#resize-inside-a-test
    term `RadioGroup` also in 1: D050#types
    term `toolbar` also in 2: D035#what-differs-from-the-web, D050#types
    term `menu` also in 9: D002#instructions-and-vocabulary, D014#goals, D016#what-the-model-can-do, D025#what-works, D035#expo-development-builds, D038#action-tools, D050#queries, D050#types, D059#resize-inside-a-test
    term `radiogroup` also in 1: D050#types
    term `password` also in 51
    term `CheckBox` also in 11
    term `radio` also in 6: D033#map-each-api, D035#known-device-limitations, D038#action-tools, D050#queries, D050#locator-reads, D050#types
    term `group` also in 42
    term `list` also in 123
    term `ProgressBar` also in 2: D050#queries, D050#types
    term `checkbox` also in 11
    term `expanded` also in 7: D007#how-a-replay-works, D033#map-each-api, D042#semanticnode, D045#locator-matchers, D045#asyncexpectation-and-textmatcheroptions, D049#functions, D050#types
    term `testId` also in 41
    term `getByLabel` also in 27
    term `getByText` also in 27
    term `heading` also in 19
    term `Tab` also in 79
    term `placeholder` also in 16
    term `rect` also in 94
- **[ALSO: D050#locator-actions]** | `perform` | `tap`, `doubleTap`, `longPress`, `fill`, `clear`, `hover`, `check`, `uncheck`, `press` (`Enter`, `Space`, or one character), `swipe`, `dragTo`, and `focus` on editable fields. A tap on a `switch` or `checkbox` lands on its innermost control, since UIKit reports a settings row as one labelled switch with the real toggle as a child. `check` and `uncheck` need a `checked` state, which Android switches lack and a React Native checkbox or radio on iOS has. `doubleTap` is two presses, 284 to 285 ms apart on iOS (the cadence of agent-device's XCTest tap): agent-device's own double-tap gesture reaches a React Native `Pressable` as one press. A detector with a window of 300 ms or less can read the pair as two single taps. `longPress` holds for one second unless the test passes `duration`, past a React Native `Pressable`'s `delayLongPress` of 500 ms and the longer thresholds apps set; agent-device's own default hold is shorter and registers as a tap on those. `selectOption`, `setInputFiles`, `scrollIntoView`, and `secondaryTap` are not declared, and neither is `tapModifiers`, so `tap` or `doubleTap` with `modifiers` is `UNSUPPORTED_CAPABILITY`. |
    term `perform` also in 25
    term `tap` also in 72
    term `doubleTap` also in 13
    term `longPress` also in 9: D018#what-the-context-holds, D031#map-each-detox-call, D032#map-each-command, D035#troubleshooting, D038#action-tools, D042#capabilities, D042#actions, D050#locator-actions, D050#types
    term `fill` also in 93
    term `clear` also in 41
    term `hover` also in 14
    term `check` also in 156
    term `uncheck` also in 7: D033#map-each-api, D033#what-differs-on-purpose, D038#action-tools, D042#capabilities, D042#actions, D045#asyncexpectation-and-textmatcheroptions, D050#locator-actions
    term `press` also in 42
    term `Enter` also in 35
    term `Space` also in 41
    term `swipe` also in 25
    term `dragTo` also in 6: D033#map-each-api, D034#map-each-webdriver-call, D038#action-tools, D042#capabilities, D042#actions, D050#locator-actions
    term `focus` also in 28
    term `switch` also in 22
    term `checkbox` also in 11
    term `checked` also in 25
    term `Pressable` also in 1: D050#locator-actions
    term `duration` also in 27
    term `delayLongPress` also in 1: D050#locator-actions
    term `selectOption` also in 10: D030#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D035#write-a-device-test, D038#action-tools, D042#capabilities, D042#actions, D042#exported-names, D050#locator-actions, D050#types
    term `setInputFiles` also in 8: D005#reach-into-an-iframe, D030#map-each-command, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#capabilities, D042#actions, D050#locator-actions
    term `scrollIntoView` also in 7: D025#what-does-not-work, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#capabilities, D042#actions, D050#locator-actions
    term `secondaryTap` also in 10: D018#what-the-context-holds, D030#map-each-command, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#engine, D042#capabilities, D042#actions, D050#locator-actions, D050#types
    term `tapModifiers` also in 9: D018#what-the-context-holds, D038#action-tools, D042#defineengine, D042#engine, D042#capabilities, D042#actions, D046#the-catalog, D050#locator-actions, D050#types
    term `modifiers` also in 12
    term `UNSUPPORTED_CAPABILITY` also in 32
- **[ALSO: D050#screen-actions]** | `performAt` | `tap`, `doubleTap`, `longPress`, and `swipeTo` at a bare screen point, so `screen.tapAt`, `tap({ position })`, `screen.swipe({ from, to })`, and the agent's `tap_at` reach a control the tree does not list. No `hover`, `secondaryTap`, or `dragTo` at a point: touch has none without a node, so `hover_at` needs a listed control. |
    term `performAt` also in 6: D042#defineengine, D042#engine, D042#capabilities, D042#actions, D046#the-catalog, D060#vision-only-surfaces
    term `tap` also in 72
    term `doubleTap` also in 13
    term `longPress` also in 9: D018#what-the-context-holds, D031#map-each-detox-call, D032#map-each-command, D035#troubleshooting, D038#action-tools, D042#capabilities, D042#actions, D050#locator-actions, D050#types
    term `swipeTo` also in 4: D025#what-does-not-work, D042#capabilities, D042#actions, D050#screen-actions
    term `screen.tapAt` also in 6: D032#map-each-command, D033#map-each-api, D042#engine, D042#capabilities, D050#screen-actions, D050#types
    term `tap({ position })` also in 5: D033#map-each-api, D042#engine, D042#capabilities, D050#screen-actions, D050#types
    term `screen.swipe({ from, to })` also in 3: D033#map-each-api, D042#engine, D042#capabilities
    term `tap_at` also in 9: D016#how-text-gets-typed, D016#vision, D025#what-does-not-work, D038#pixel-tools-screenshot-and-the-point-verbs, D042#engine, D042#capabilities, D046#the-catalog, D047#agent-tools, D060#vision-only-surfaces
    term `hover` also in 14
    term `secondaryTap` also in 10: D018#what-the-context-holds, D030#map-each-command, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#engine, D042#capabilities, D042#actions, D050#locator-actions, D050#types
    term `dragTo` also in 6: D033#map-each-api, D034#map-each-webdriver-call, D038#action-tools, D042#capabilities, D042#actions, D050#locator-actions
    term `hover_at` also in 4: D038#pixel-tools-screenshot-and-the-point-verbs, D042#capabilities, D046#the-catalog, D047#agent-tools
- **[ALSO: D042#capabilities]** | `keyboard` | `type` and `press` into the focused field, the agent's `type` and `press` without a target and the fallback of `type_at` and `press_at`, and `dismiss`, the agent's `dismiss_keyboard`. |
    term `keyboard` also in 25
    term `type` also in 182
    term `press` also in 42
    term `type_at` also in 8: D016#how-text-gets-typed, D016#vision, D016#limits, D025#what-does-not-work, D038#pixel-tools-screenshot-and-the-point-verbs, D042#capabilities, D046#the-catalog, D047#agent-tools
    term `press_at` also in 4: D038#pixel-tools-screenshot-and-the-point-verbs, D042#capabilities, D046#the-catalog, D047#agent-tools
    term `dismiss` also in 14
    term `dismiss_keyboard` also in 5: D016#what-the-model-can-do, D038#action-tools, D042#capabilities, D046#the-catalog, D047#agent-tools
- **[ALSO: D042#shared-semantics, D050#queries, D053#the-browser-fixture]** | `locate` | Every `screen` query. Text and label queries answer with the innermost match, since a device echoes both up the tree (a React Native input is a host view and the field inside it, both labelled). On Android a test id query, a string or a RegExp, also matches a resource id without its `<package>:id/` prefix, for any package but the framework's `android`, when nothing on the screen matches the full id. `screen.locator('id=…')` is agent-device's selector and takes the full id. |
    term `locate` also in 24
    term `screen` also in 214
    term `<package>:id/` also in 1: D035#test-ids-by-framework
    term `android` also in 60
- **[ONLY HERE]** | `validateApp` | Requires `app.bundleId` or `app.appPath` and refuses `app.url` for now, with a note on reaching this machine from the platform's device. A target with either is a `native-app` target, so `requires: ['native-app']` selects device targets. |
    term `validateApp` also in 6: D042#defineengine, D042#engine, D042#capabilities, D042#app, D060#the-shape-of-an-engine, D060#capabilities
    term `app.bundleId` also in 14
    term `app.appPath` also in 10: D008#mobile-jobs, D028#setup, D035#point-at-your-app, D035#physical-devices, D035#hosted-devices, D041#the-app-under-test, D042#capabilities, D044#runner-codes, D047#device, D052#options
    term `app.url` also in 19
    term `native-app` also in 2: D042#capabilities, D052#options
    term `requires: ['native-app']` also in 2: D042#capabilities, D052#options
- **[ALSO: D032#map-each-command, D035#the-device-fixture, D035#what-differs-from-the-web]** | `session` | `back`, `restart`, and `reset`. No `open`: `app.open()` takes no path and the runner serves it with `restart`, the fresh launch of the pinned app; the agent's `navigate` verb is unavailable, and `device.openLink(url)` opens a deep link or web link. |
    term `session` also in 126
    term `back` also in 77
    term `restart` also in 26
    term `reset` also in 24
    term `open` also in 169
    term `app.open()` also in 35
    term `navigate` also in 23
    term `device.openLink(url)` also in 1: D035#what-differs-from-the-web
- **[ALSO: D035#what-differs-from-the-web, D042#artifacts]** | `artifacts` | Redacted screenshots under `screenshots/NNN-<label>.png`; a screenshot that cannot be redacted fails instead of being written. Video, when the attempt's [video mode](/reference/config#video) records, as `video/video.mp4`, or a device provider's own recording. |
    term `artifacts` also in 44
    term `video/video.mp4` also in 3: D022#recordings, D026#choose-device-options, D041#recording
- **[ALSO: D035#what-differs-from-the-web]** | `location` | `<bundle id> / <screen title>`, the replay cache's anchor. The title is the navigation bar's on iOS and the toolbar's on Android. |
    term `location` also in 31
    term `<bundle id> / <screen title>` also in 2: D035#what-differs-from-the-web, D047#replay-cache-on-a-device
- **[ONLY HERE]** | `state` | Not declared. `test.setup` and `session:` are unavailable. |
    term `state` also in 93
    term `test.setup` also in 19
    term `session:` also in 17

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D007#what-must-match: Both state app.identity keeps one cache identity when the build path changes.
- D008#mobile-jobs: Both state the engine installs nothing on its own and appPath needs device.installApp().
- D022#setup: Both show videoTouches: false with a hosted device provider and workers.
- D022#options: Both describe selecting an iOS device by name or UDID.
- D022#recordings: Both state videoTouches false stops agent-device drawing touches into the recording.
- D031#port-the-config: Both state appPath plus one device.installApp() per device, launchArguments, and workers per device.
- D032#port-the-config: Both state a device list is a pool, one worker per device, with workers.
- D035#set-up: Both state device boot happens before test timing and is not charged to launch timeout.
- D035#point-at-your-app: Both state a device target needs bundleId or appPath, the engine installs only via device.installApp, and launch arguments apply to every fresh launch.
- D035#launch-arguments-and-permissions: Both describe app.launchArguments and app.permissions on every fresh launch, identity, and device.openApp for one launch.
- D035#several-devices: Both describe a device list as a pool with one worker each, booted devices used when device is omitted, and no two workers on one device.
- D035#physical-devices: Both describe device selection by name, UDID or serial, and appPath for physical devices.
- D035#hosted-devices: Both describe a DeviceProvider leasing hosted devices, one per worker slot.
- D035#what-differs-from-the-web: Both state videoTouches false hides touches in the MP4 and no test.setup sessions on devices.
- D035#troubleshooting: Both describe boot, runner timeouts and wedged iOS automation runner recovery.
- D041#the-app-under-test: Both describe bundleId, appPath, launchArguments, permissions, identity for mobile targets.
- D042#capabilities: Both describe native-app targets and which capabilities the mobile engine declares.
- D047#device: Both describe device.openApp, installApp and openLink behaviour.
- D047#agent-tools: Both describe the agent tools the mobile engine supports and open_app.
- D047#replay-cache-on-a-device: Both describe the location anchor and replay behaviour on a device.
- D047#engine-options: Both reference LaunchPermissions and permission state grant, deny or reset.
- D047#device-fixture: Both describe OpenAppOptions relaunch, launchArguments and permissions.
- D051#navigation: Both state device.openLink takes any absolute URL and device.openApp takes an app id, never a link.

## S44 · paraphrase · D042#errors  (e2e/engine › Reference › Errors; page title: e2e/engine)

Regel: genau ein Abschnitt; die Frage teilt kein Inhaltswort mit der Abschnittsüberschrift oder dem Seitentitel (auch keine Wortformen).

**Typ-Eignung:** Ziel `conceptual`: warum nur zwei Codes wiederholbar sein dürfen: „The only codes that may be retryable: both describe a repeatable read. Any other retryable claim … is coerced to a non-retryable `ENGINE_FAILURE`.“ (`find "repeatable read"` und `find "coerced"`: nur hier). Vorsicht: Dass nur `NODE_STALE` und `FRAME_NOT_FOUND` wiederholbar sind, steht auch in D060#errors, und D060#nodes-and-refs und D042#engine beschreiben, wann `NODE_STALE` geworfen wird. Die Antwort darf also nur die Begründung (und die Umdeutung) tragen, nicht die Liste der zwei Codes. Für `paraphrase` darf die Frage nicht errors/error, reference, e2e oder engine enthalten (Überschrift „Errors“, Seitentitel „e2e/engine“); bitte mit `shared_words` prüfen.

- **[ONLY HERE]** An engine throws `EngineError` with one code of a closed set.
    term `EngineError` also in 3: D042#lifecycle, D042#actions, D060#errors
- **[ONLY HERE]** The runner maps each code to the error a test sees.
- **[ONLY HERE]** | `NODE_STALE` | re-resolve, then `LOCATOR_NOT_FOUND` | yes |
    term `NODE_STALE` also in 3: D042#engine, D060#nodes-and-refs, D060#errors
    term `LOCATOR_NOT_FOUND` also in 14
- **[ONLY HERE]** | `FRAME_NOT_FOUND` | re-resolve, then `LOCATOR_NOT_FOUND` | yes |
    term `FRAME_NOT_FOUND` also in 2: D042#shared-semantics, D060#errors
    term `LOCATOR_NOT_FOUND` also in 14
- **[ONLY HERE]** | `FRAME_AMBIGUOUS` | `LOCATOR_AMBIGUOUS` | no |
    term `LOCATOR_AMBIGUOUS` also in 16
- **[ONLY HERE]** | `NOT_ACTIONABLE`, `ACTION_MAY_HAVE_COMMITTED`, `OPERATION_TIMEOUT` | `ACTION_FAILED` | no |
    term `NOT_ACTIONABLE` also in 2: D042#capabilities, D060#keyboard
    term `ACTION_MAY_HAVE_COMMITTED` also in 2: D042#engine, D060#errors
    term `OPERATION_TIMEOUT` also in 2: D042#shared-semantics, D053#options
    term `ACTION_FAILED` also in 13
- **[ONLY HERE]** | `CANCELLED` | infrastructure `CANCELLED` | no |
    term `CANCELLED` also in 23
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | configuration `UNSUPPORTED_CAPABILITY` | no |
    term `UNSUPPORTED_CAPABILITY` also in 32
- **[ONLY HERE]** | `INVALID_STATE` | `APP_NOT_OPEN` | no |
    term `INVALID_STATE` also in 4: D018#driving-the-page-yourself, D042#observation, D053#surfaceof, D060#errors
    term `APP_NOT_OPEN` also in 6: D038#agent-act, D039#back, D044#agenterror, D047#device, D053#the-browser-fixture, D060#errors
- **[ONLY HERE]** | `ENGINE_FAILURE`, any non-`EngineError` | infrastructure `ENGINE_FAILURE` | no |
    term `ENGINE_FAILURE` also in 13
    term `EngineError` also in 3: D042#lifecycle, D042#actions, D060#errors
- **[ONLY HERE]** An `OPERATION_TIMEOUT` on a locate or read that started with under 100 ms of a waiting call's deadline left, after one that completed, ends the wait instead:
    term `OPERATION_TIMEOUT` also in 2: D042#shared-semantics, D053#options
- **[ONLY HERE]** | an action, `waitFor` | `LOCATOR_NOT_FOUND`, with the timeout as its cause |
    term `waitFor` also in 47
    term `LOCATOR_NOT_FOUND` also in 14
- **[ONLY HERE]** | an assertion | `ASSERTION_FAILED`, with the timeout as its cause |
    term `ASSERTION_FAILED` also in 15
- **[ONLY HERE]** A negated assertion passes there if its negation had held long enough by the time the read was cut off.
- **[ONLY HERE]** [`pollCondition`](#pollcondition) polls by these rules.
    term `pollCondition` also in 2: D042#shared-semantics, D042#exported-names
- **[ONLY HERE]** An `EngineError` a contributed fixture method throws is mapped by the table above, so a fixture over a session that ended reports `APP_NOT_OPEN` the way an observation would.
    term `EngineError` also in 3: D042#lifecycle, D042#actions, D060#errors
    term `APP_NOT_OPEN` also in 6: D038#agent-act, D039#back, D044#agenterror, D047#device, D053#the-browser-fixture, D060#errors
- **[ONLY HERE]** A method can also fail a step with the runner's own error classes, exported from the same entry.
- **[ONLY HERE]** `E2EError` itself is not exported; construct one of the three.
    term `E2EError` also in 1: D049#functions

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D042#engine: Both explain NODE_STALE as retryable and ACTION_MAY_HAVE_COMMITTED for input that may have reached the app.
- D042#lifecycle: Both map EngineError CANCELLED to a cancellation and other errors to infrastructure ENGINE_FAILURE.
- D042#observation: Both describe INVALID_STATE being thrown by an engine.
- D042#shared-semantics: Both state an OPERATION_TIMEOUT ends a poll under the deadline rules and describe pollCondition and TestError use.
- D042#exported-names: Both name ENGINE_ERROR_CODES and RETRYABLE_ENGINE_ERROR_CODES as exports.
- D060#nodes-and-refs: Both state a retryable NODE_STALE is thrown when a node no longer exists.
- D060#errors: Both list engine error codes, that only NODE_STALE and FRAME_NOT_FOUND can be retryable, and the mapping of INVALID_STATE to APP_NOT_OPEN.

## S45 · detail · D042#capabilities  (e2e/engine › Reference › Capabilities; page title: e2e/engine)

Regel: genau ein Abschnitt, ein einzelnes Faktum, Referenzantwort höchstens 30 Wörter; das Faktum muss nur hier stehen.

**Typ-Eignung:** Ziel `conceptual`, ein Faktum in einem Satz (≤ 30 Wörter). Zwei Stellen stehen nur hier (`find` jeweils ein Treffer): (a) das Agent-Verb `check` braucht `check` und `uncheck`, „since it sets a state rather than flipping one“; (b) `actions` und `location` setzen Beobachtung voraus, „because their refs live in the observation's id space“. Eine davon wählen, nicht beide (sonst zwei Fakten). Verworfen: „setting the value without keystrokes is not a compliant implementation“ steht auch in D060#keyboard.

- **[ALSO: D042#engine]** The members an engine implements set its capabilities.
- **[ONLY HERE]** A `screen`, `Locator`, or `app` call that needs a missing one fails with `UNSUPPORTED_CAPABILITY`.
    term `screen` also in 214
    term `Locator` also in 109
    term `app` also in 307
    term `UNSUPPORTED_CAPABILITY` also in 32
- **[ONLY HERE]** [Test APIs](#test-apis) lists what needs which member.
- **[ONLY HERE]** Three gaps end differently:
- **[ONLY HERE]** - A test that `requires` a fixture the engine lacks is skipped (`capability-unavailable`).
    term `requires` also in 26
- **[ONLY HERE]** - A selected test that uses a `test.setup` session, on an engine without `state`, is a collection error before the setup runs.
    term `test.setup` also in 19
    term `state` also in 93
- **[ONLY HERE]** - A `video` mode on an engine without video recording prints a notice and records no video.
    term `video` also in 56
- **[ONLY HERE]** | `observe` | `observation` | - | The judgment tier, prompt snapshots, trace replay, the viewport swipe's root. |
    term `observe` also in 41
    term `observation` also in 51
- **[ALSO: D060#capabilities]** | `perform` + `actions` | `actions` | `observe` | Node actions of the declared kinds, with platform actionability checks. |
    term `perform` also in 24
    term `actions` also in 88
    term `observe` also in 41
- **[ONLY HERE]** | `locate` | `location` | `observe` | `screen`, `Locator`, `expect(locator)`. |
    term `locate` also in 23
    term `location` also in 31
    term `observe` also in 41
    term `screen` also in 214
    term `Locator` also in 109
    term `expect(locator)` also in 11
- **[ONLY HERE]** | `tapModifiers: true` | - | `perform` | `modifiers` on `tap`, `doubleTap`, and `secondaryTap`. |
    term `perform` also in 24
    term `modifiers` also in 12
    term `tap` also in 72
    term `doubleTap` also in 13
    term `secondaryTap` also in 10: D018#what-the-context-holds, D030#map-each-command, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#engine, D042#actions, D047#engine, D050#locator-actions, D050#types
- **[ALSO: D042#engine, D050#screen-actions]** | `performAt` + `pointerActions` | `pointer` | `observe` | One pointer action at a viewport point, with no node behind it. |
    term `performAt` also in 6: D042#defineengine, D042#engine, D042#actions, D046#the-catalog, D047#engine, D060#vision-only-surfaces
    term `pointerActions` also in 5: D038#pixel-tools-screenshot-and-the-point-verbs, D042#defineengine, D042#engine, D042#actions, D060#vision-only-surfaces
    term `pointer` also in 17
    term `observe` also in 41
- **[ALSO: D042#engine]** | `keyboard.{type,press,dismiss?}` | `keyboard` | `observe` | Input to whatever holds focus. |
    term `keyboard` also in 25
    term `observe` also in 41
- **[ONLY HERE]** | `fixtures.<name>` | `<name>` | - | A contributed fixture. |
    term `<name>` also in 34
- **[ALSO: D004#next, D042#state]** | `state` | `state` | - | `test.setup` sessions and the `session:` option. |
    term `state` also in 93
    term `test.setup` also in 19
    term `session:` also in 17
- **[ONLY HERE]** | `artifacts` | `artifacts` | - | Screenshots and videos. |
    term `artifacts` also in 44
- **[ALSO: D060#capabilities]** | `validateApp` | - | - | A config-load check of the target's `app`. |
    term `validateApp` also in 6: D042#defineengine, D042#engine, D042#app, D047#engine, D060#the-shape-of-an-engine, D060#capabilities
    term `app` also in 307
- **[ALSO: D042#session, D060#capabilities]** | `session` | - | - | The `app` steering methods and the agent's `navigate` and `back` verbs. |
    term `session` also in 126
    term `app` also in 307
    term `navigate` also in 23
    term `back` also in 77
- **[ONLY HERE]** The agent offers the model only the verbs the engine's declarations unlock.
- **[ONLY HERE]** An undeclared verb is absent from the toolset.
- **[ONLY HERE]** | `tap` | the `tap` kind in `actions` |
    term `tap` also in 72
    term `actions` also in 88
- **[ONLY HERE]** | `double_tap` | `doubleTap` |
    term `double_tap` also in 4: D016#what-the-model-can-do, D038#action-tools, D046#the-catalog, D047#agent-tools
    term `doubleTap` also in 13
- **[ONLY HERE]** | `long_press` | `longPress` |
    term `long_press` also in 4: D016#what-the-model-can-do, D038#action-tools, D046#the-catalog, D047#agent-tools
    term `longPress` also in 9: D018#what-the-context-holds, D031#map-each-detox-call, D032#map-each-command, D035#troubleshooting, D038#action-tools, D042#actions, D047#engine, D050#locator-actions, D050#types
- **[ONLY HERE]** | `right_click` | `secondaryTap` |
    term `right_click` also in 3: D038#action-tools, D046#the-catalog, D047#agent-tools
    term `secondaryTap` also in 10: D018#what-the-context-holds, D030#map-each-command, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#engine, D042#actions, D047#engine, D050#locator-actions, D050#types
- **[ONLY HERE]** | `hover` | `hover` |
    term `hover` also in 14
- **[ONLY HERE]** | `type` | `fill`; without a target, `keyboard` |
    term `type` also in 182
    term `fill` also in 93
    term `keyboard` also in 25
- **[ONLY HERE]** | `type_secret` | `fill` |
    term `type_secret` also in 11
    term `fill` also in 93
- **[ONLY HERE]** | `press` | `press`; without a target, `keyboard` |
    term `press` also in 41
    term `keyboard` also in 25
- **[ONLY HERE]** | `select` | `selectOption` |
    term `select` also in 95
    term `selectOption` also in 10: D030#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D035#write-a-device-test, D038#action-tools, D042#actions, D042#exported-names, D047#engine, D050#locator-actions, D050#types
- **[ONLY HERE]** | `check` | both `check` and `uncheck`, since it sets a state rather than flipping one |
    term `check` also in 156
    term `uncheck` also in 7: D033#map-each-api, D033#what-differs-on-purpose, D038#action-tools, D042#actions, D045#asyncexpectation-and-textmatcheroptions, D047#engine, D050#locator-actions
- **[ONLY HERE]** | `scroll`, `scroll_to({ text })` | `swipe` |
    term `scroll` also in 31
    term `scroll_to({ text })` also in 1: D038#action-tools
    term `swipe` also in 25
- **[ONLY HERE]** | `scroll_to({ target })` | `scrollIntoView` |
    term `scroll_to({ target })` also in 1: D038#action-tools
    term `scrollIntoView` also in 7: D025#what-does-not-work, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D047#engine, D050#locator-actions
- **[ONLY HERE]** | `drag` | `dragTo` |
    term `drag` also in 16
    term `dragTo` also in 6: D033#map-each-api, D034#map-each-webdriver-call, D038#action-tools, D042#actions, D047#engine, D050#locator-actions
- **[ONLY HERE]** | `upload` | `setInputFiles` |
    term `upload` also in 26
    term `setInputFiles` also in 8: D005#reach-into-an-iframe, D030#map-each-command, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D047#engine, D050#locator-actions
- **[ONLY HERE]** | `navigate` | `session.open` |
    term `navigate` also in 23
    term `session.open` also in 5: D038#action-tools, D039#open, D042#lifecycle, D042#app, D060#capabilities
- **[ONLY HERE]** | `back` | `session.back` |
    term `back` also in 77
    term `session.back` also in 2: D038#action-tools, D039#back
- **[ONLY HERE]** | `tap_at`, `hover_at` | the `tap` or `hover` kind, in `actions` or in `pointerActions` |
    term `tap_at` also in 9: D016#how-text-gets-typed, D016#vision, D025#what-does-not-work, D038#pixel-tools-screenshot-and-the-point-verbs, D042#engine, D046#the-catalog, D047#engine, D047#agent-tools, D060#vision-only-surfaces
    term `hover_at` also in 4: D038#pixel-tools-screenshot-and-the-point-verbs, D046#the-catalog, D047#engine, D047#agent-tools
    term `tap` also in 72
    term `hover` also in 14
    term `actions` also in 88
    term `pointerActions` also in 5: D038#pixel-tools-screenshot-and-the-point-verbs, D042#defineengine, D042#engine, D042#actions, D060#vision-only-surfaces
- **[ONLY HERE]** | `type_at` | `fill` or `keyboard` |
    term `type_at` also in 8: D016#how-text-gets-typed, D016#vision, D016#limits, D025#what-does-not-work, D038#pixel-tools-screenshot-and-the-point-verbs, D046#the-catalog, D047#engine, D047#agent-tools
    term `fill` also in 93
    term `keyboard` also in 25
- **[ONLY HERE]** | `press_at` | `press` or `keyboard` |
    term `press_at` also in 4: D038#pixel-tools-screenshot-and-the-point-verbs, D046#the-catalog, D047#engine, D047#agent-tools
    term `press` also in 41
    term `keyboard` also in 25
- **[ONLY HERE]** | `select_at` | `selectOption` |
    term `select_at` also in 3: D038#pixel-tools-screenshot-and-the-point-verbs, D046#the-catalog, D047#agent-tools
    term `selectOption` also in 10: D030#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D035#write-a-device-test, D038#action-tools, D042#actions, D042#exported-names, D047#engine, D050#locator-actions, D050#types
- **[ONLY HERE]** | `dismiss_keyboard` | `keyboard.dismiss` |
    term `dismiss_keyboard` also in 5: D016#what-the-model-can-do, D038#action-tools, D046#the-catalog, D047#engine, D047#agent-tools
    term `keyboard.dismiss` also in 1: D038#action-tools
- **[ONLY HERE]** - `clear` and `focus` unlock no verb.
    term `clear` also in 41
    term `focus` also in 28
- **[ALSO: D038#action-tools]** - `tap_at`, `hover_at`, `type_at`, `press_at`, and `select_at` go through `perform` when the point lands on a node the tree lists.
    term `tap_at` also in 9: D016#how-text-gets-typed, D016#vision, D025#what-does-not-work, D038#pixel-tools-screenshot-and-the-point-verbs, D042#engine, D046#the-catalog, D047#engine, D047#agent-tools, D060#vision-only-surfaces
    term `hover_at` also in 4: D038#pixel-tools-screenshot-and-the-point-verbs, D046#the-catalog, D047#engine, D047#agent-tools
    term `type_at` also in 8: D016#how-text-gets-typed, D016#vision, D016#limits, D025#what-does-not-work, D038#pixel-tools-screenshot-and-the-point-verbs, D046#the-catalog, D047#engine, D047#agent-tools
    term `press_at` also in 4: D038#pixel-tools-screenshot-and-the-point-verbs, D046#the-catalog, D047#engine, D047#agent-tools
    term `select_at` also in 3: D038#pixel-tools-screenshot-and-the-point-verbs, D046#the-catalog, D047#agent-tools
    term `perform` also in 24
- **[ALSO: D042#engine]** - When the point lands on nothing the tree lists, `tap_at` and `hover_at` go through `performAt` (the `tap` and `hover` pointer kinds), and `type_at` and `press_at` fall back to `keyboard`.
    term `tap_at` also in 9: D016#how-text-gets-typed, D016#vision, D025#what-does-not-work, D038#pixel-tools-screenshot-and-the-point-verbs, D042#engine, D046#the-catalog, D047#engine, D047#agent-tools, D060#vision-only-surfaces
    term `hover_at` also in 4: D038#pixel-tools-screenshot-and-the-point-verbs, D046#the-catalog, D047#engine, D047#agent-tools
    term `performAt` also in 6: D042#defineengine, D042#engine, D042#actions, D046#the-catalog, D047#engine, D060#vision-only-surfaces
    term `tap` also in 72
    term `hover` also in 14
    term `type_at` also in 8: D016#how-text-gets-typed, D016#vision, D016#limits, D025#what-does-not-work, D038#pixel-tools-screenshot-and-the-point-verbs, D046#the-catalog, D047#engine, D047#agent-tools
    term `press_at` also in 4: D038#pixel-tools-screenshot-and-the-point-verbs, D046#the-catalog, D047#engine, D047#agent-tools
    term `keyboard` also in 25
- **[ONLY HERE]** The test-facing APIs each engine member backs.
- **[ALSO: D042#engine]** A `screen` or `Locator` method for an undeclared kind, or a call with `modifiers` and no `tapModifiers`, fails with `UNSUPPORTED_CAPABILITY` before it reaches the engine.
    term `screen` also in 214
    term `Locator` also in 109
    term `modifiers` also in 12
    term `tapModifiers` also in 9: D018#what-the-context-holds, D038#action-tools, D042#defineengine, D042#engine, D042#actions, D046#the-catalog, D047#engine, D050#locator-actions, D050#types
    term `UNSUPPORTED_CAPABILITY` also in 32
- **[ONLY HERE]** | `screen`, `Locator`, `expect(locator)` | `locate` |
    term `screen` also in 214
    term `Locator` also in 109
    term `expect(locator)` also in 11
    term `locate` also in 23
- **[ALSO: D042#engine]** | `screen` and `Locator` actions | `perform`, each only for a kind listed in `actions` |
    term `screen` also in 214
    term `Locator` also in 109
    term `perform` also in 24
    term `actions` also in 88
- **[ALSO: D042#engine]** | `screen.swipe()` | `perform` with `swipe` on the observation root |
    term `screen.swipe()` also in 2: D042#actions, D060#nodes-and-refs
    term `perform` also in 24
    term `swipe` also in 25
- **[ONLY HERE]** | `modifiers` on a tap (`row.click({ modifiers: ['Shift'] })`) | `tapModifiers: true`; the keys are held for the click |
    term `modifiers` also in 12
    term `row.click({ modifiers: ['Shift'] })` also in 1: D050#locator-actions
- **[ONLY HERE]** | `screen.tapAt`, `tap({ position })` | `performAt` with the `tap` pointer kind |
    term `screen.tapAt` also in 6: D032#map-each-command, D033#map-each-api, D042#engine, D047#engine, D050#screen-actions, D050#types
    term `tap({ position })` also in 5: D033#map-each-api, D042#engine, D047#engine, D050#screen-actions, D050#types
    term `performAt` also in 6: D042#defineengine, D042#engine, D042#actions, D046#the-catalog, D047#engine, D060#vision-only-surfaces
    term `tap` also in 72
- **[ONLY HERE]** | `screen.swipe({ from, to })` | `performAt` with the `swipeTo` pointer kind |
    term `screen.swipe({ from, to })` also in 3: D033#map-each-api, D042#engine, D047#engine
    term `performAt` also in 6: D042#defineengine, D042#engine, D042#actions, D046#the-catalog, D047#engine, D060#vision-only-surfaces
    term `swipeTo` also in 4: D025#what-does-not-work, D042#actions, D047#engine, D050#screen-actions
- **[ONLY HERE]** | `locator.pressSequentially` | the `focus` action and `keyboard`; the harness composes `focus` then `keyboard.type` |
    term `locator.pressSequentially` also in 1: D060#keyboard
    term `focus` also in 28
    term `keyboard` also in 25
    term `keyboard.type` also in 4: D033#map-each-api, D033#port-page-objects, D053#the-browser-fixture, D060#keyboard
- **[ONLY HERE]** | `test.setup` sessions, the `session:` option | `state` |
    term `test.setup` also in 19
    term `session:` also in 17
    term `state` also in 93
- **[ONLY HERE]** | `app.screenshot()`, assertion evidence, the failure screenshot | `artifacts` |
    term `app.screenshot()` also in 4: D045#screenshot-matchers, D049#playwright-test-fixtures, D051#policy-denials, D051#screenshots-after-a-secret-fill
    term `artifacts` also in 44
- **[ALSO: D041#recording]** | every [`video` mode](/reference/config#recording) but `off`, from the config, a target, a test, or `--video` | `artifacts` |
    term `video` also in 56
    term `off` also in 76
    term `--video` also in 14
    term `artifacts` also in 44
- **[ALSO: D039#open]** | `app.open()` | `session.open`; on a target with no app URL, `session.restart` |
    term `app.open()` also in 36
    term `session.open` also in 5: D038#action-tools, D039#open, D042#lifecycle, D042#app, D060#capabilities
    term `session.restart` also in 2: D039#open, D039#restart
- **[ONLY HERE]** | `app.back()` | `session.back` |
    term `app.back()` also in 6: D032#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D039#back, D042#session, D060#capabilities
    term `session.back` also in 2: D038#action-tools, D039#back
- **[ONLY HERE]** | `app.restart()` | `session.restart` |
    term `app.restart()` also in 14
    term `session.restart` also in 2: D039#open, D039#restart
- **[ONLY HERE]** | `app.clearState()` | `session.reset` |
    term `app.clearState()` also in 20
    term `session.reset` also in 1: D039#clearstate
- **[ONLY HERE]** | `requires: ['<name>']` | `fixtures.<name>` |
    term `requires: ['<name>']` also in 1: D042#engine
- **[ONLY HERE]** The computed `ReadonlySet` of capability names.
    term `ReadonlySet` also in 2: D042#defineengine, D042#errors
- **[ONLY HERE]** Selection, the report, and `UNSUPPORTED_CAPABILITY` messages read it.
    term `UNSUPPORTED_CAPABILITY` also in 32
- **[ONLY HERE]** Selection also grades a target by the kind of app it declares, not by its engine.
- **[ONLY HERE]** A target with `app.url` has `browser`, and one with `app.bundleId` or `app.appPath` has `native-app`, so a test can `requires: ['native-app']`.
    term `app.url` also in 19
    term `browser` also in 146
    term `app.bundleId` also in 14
    term `app.appPath` also in 10: D008#mobile-jobs, D028#setup, D035#point-at-your-app, D035#physical-devices, D035#hosted-devices, D041#the-app-under-test, D044#runner-codes, D047#engine, D047#device, D052#options
    term `native-app` also in 2: D047#engine, D052#options
    term `requires: ['native-app']` also in 2: D047#engine, D052#options

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D038#action-tools: Both say the agent offers only the verbs the engine declares, with their required members (tapModifiers, scrollIntoView, keyboard.dismiss).
- D038#pixel-tools-screenshot-and-the-point-verbs: Both say tap_at needs actions or pointerActions with tap, and type_at needs fill or keyboard.
- D039#reference-app: Both state app.open, back, restart and clearState need session members, else UNSUPPORTED_CAPABILITY.
- D039#open: Both state app.open needs session.open or session.restart, else UNSUPPORTED_CAPABILITY.
- D039#restart: Both state app.restart needs session.restart, else UNSUPPORTED_CAPABILITY.
- D039#clearstate: Both state app.clearState needs session.reset, else UNSUPPORTED_CAPABILITY.
- D039#back: Both state app.back needs session.back, else UNSUPPORTED_CAPABILITY.
- D039#screenshot: Both state app.screenshot and failure screenshots need the artifacts capability.
- D042#defineengine: Both give validation rules such as tapModifiers needing perform and performAt needing pointerActions.
- D042#engine: Both list engine members (tapModifiers, performAt, pointerActions, state) and that unsupported calls fail with UNSUPPORTED_CAPABILITY.
- D042#actions: Both say perform kinds in actions and performAt kinds in pointerActions set what is supported, else UNSUPPORTED_CAPABILITY.
- D042#contributed-fixtures: Both state a contributed fixture is a capability name that tests can require.
- D046#the-catalog: Both state an undeclared verb is absent from the MCP catalog and modifiers need tapModifiers.
- D047#engine: Both state a target with bundleId or appPath is a native-app target and show what the mobile engine declares (perform, performAt, keyboard).
- D047#agent-tools: Both describe which agent verbs (scroll_to, dismiss_keyboard, type_at, press_at) the mobile engine's declarations unlock.
- D050#screen-actions: Both state tap position and swipe need the engine's pointer or swipe actions else UNSUPPORTED_CAPABILITY.
- D050#locator-actions: Both state modifiers need tapModifiers and unlisted action kinds fail with UNSUPPORTED_CAPABILITY before the engine.
- D052#options: Both state requires: ['native-app'] selects targets with app.bundleId or app.appPath.
- D052#fixtures: Both state a test needing a missing fixture is skipped via requires, else UNSUPPORTED_CAPABILITY.
- D060#capabilities: Both list which engine members unlock which APIs and state a missing one fails with UNSUPPORTED_CAPABILITY.
- D060#keyboard: Both say locator.pressSequentially uses the keyboard hook after a focus action and keys may fail UNSUPPORTED_CAPABILITY.
- D060#vision-only-surfaces: Both describe performAt with pointerActions for point-addressed actions, used by tap_at.

## S46 · single · D042#lifecycle  (e2e/engine › Reference › Lifecycle; page title: e2e/engine)

Regel: genau ein Abschnitt, dessen Hauptinhalt die Antwort ist; jeder Teil der Antwort muss nur hier stehen.

**Typ-Eignung:** Ziel `conceptual`: warum `prepare` keine Zeitgrenze hat: „Provisioning has no budget: a first-run download is as long as the network makes it, and cutting it short would fail every test behind it“ (`find "has no timeout"` und `find "Provisioning has no budget"`: nur hier; D060#lifecycle nennt `prepare` ohne Budget). Das gehört zum Hauptinhalt des Abschnitts (welche Hooks in welchem Budget laufen). Verworfen für `limitation`: „protected as text only … withholds no screenshot or model pixels“ steht auch in D053#options und D060#handle-secrets.

- **[ONLY HERE]** The hooks the runner calls around workers and attempts.
- **[ONLY HERE]** Every hook is optional.
- **[ONLY HERE]** The `Engine` declaration's JSDoc above states each hook's contract.
    term `Engine` also in 202
- **[ONLY HERE]** `init` and `startAttempt` run within `launchTimeout`.
    term `init` also in 59
    term `startAttempt` also in 5: D042#defineengine, D042#engine, D042#artifacts, D060#lifecycle, D060#handle-secrets
    term `launchTimeout` also in 5: D035#set-up, D041#top-level, D041#e2econfig, D044#runner-codes, D047#engine
- **[ONLY HERE]** `finish`, `settleAttempt`, `endAttempt`, and `dispose` run within `cleanupTimeout`.
    term `finish` also in 30
    term `settleAttempt` also in 3: D042#defineengine, D042#engine, D060#lifecycle
    term `endAttempt` also in 4: D042#defineengine, D042#engine, D042#artifacts, D060#lifecycle
    term `dispose` also in 8: D040#commands, D042#defineengine, D042#engine, D042#exported-names, D046#tools, D049#host, D060#the-shape-of-an-engine, D060#lifecycle
    term `cleanupTimeout` also in 11
- **[ONLY HERE]** `prepare` has no timeout.
    term `prepare` also in 19
- **[ALSO: D039#reference]** Both budgets come from the [config](/reference/config).
- **[ONLY HERE]** | [`prepare(info)`](#prepare) | Once per target, before any worker |
- **[ONLY HERE]** | [`finish(info)`](#finish) | After the target's last worker is gone |
- **[ALSO: D060#lifecycle]** | [`init(info)`](#init) | Once per worker, before its first step |
    term `init(info)` also in 1: D060#the-shape-of-an-engine
- **[ONLY HERE]** | [`startAttempt(context)`](#startattempt) | Before each attempt |
- **[ALSO: D060#lifecycle]** | [`settleAttempt(context)`](#settleattempt) | After the body and after teardown |
- **[ONLY HERE]** | [`endAttempt(context)`](#endattempt) | After each attempt |
- **[ONLY HERE]** | [`dispose(context)`](#dispose) | Worker shutdown |
    term `dispose(context)` also in 1: D060#the-shape-of-an-engine
- **[ALSO: D042#engine, D060#lifecycle]** Runs once per target in the runner process, after collection and before workers, app commands, and the run's clock start.
- **[ALSO: D025#setup, D042#engine]** A failure ends the run before any test:
- **[ONLY HERE]** | A runner error class, such as a `ConfigurationError` for an option the engine cannot honour | The same code. |
    term `ConfigurationError` also in 4: D042#app, D042#errors, D049#functions, D060#the-shape-of-an-engine
- **[ONLY HERE]** | An `EngineError` with code `CANCELLED` | A cancellation. |
    term `EngineError` also in 3: D042#actions, D042#errors, D060#errors
    term `CANCELLED` also in 23
- **[ONLY HERE]** | Any other `EngineError`, or a plain `Error` | Infrastructure `ENGINE_FAILURE`. |
    term `EngineError` also in 3: D042#actions, D042#errors, D060#errors
    term `Error` also in 99
    term `ENGINE_FAILURE` also in 13
- **[ALSO: D042#engine, D060#lifecycle]** Runs once per run and target in the runner process, after every worker of the target is gone.
- **[ALSO: D042#engine]** Release what `prepare` acquired for the run.
    term `prepare` also in 19
- **[ONLY HERE]** The `finish` hooks of all prepared targets share one `cleanupTimeout`.
    term `finish` also in 30
    term `cleanupTimeout` also in 11
- **[ALSO: D042#engine]** Runs once per worker, before the first step.
- **[ALSO: D042#engine]** Boot devices here, not in a step budget.
- **[ONLY HERE]** `init` never learns the app URL; URLs arrive through `session.open` only.
    term `init` also in 59
    term `session.open` also in 5: D038#action-tools, D039#open, D042#capabilities, D042#app, D060#capabilities
- **[ONLY HERE]** A failure is an infrastructure error.
- **[ONLY HERE]** Runs before each attempt, to set up the per-test isolation that [`endAttempt`](#endattempt) tears down.
    term `endAttempt` also in 4: D042#defineengine, D042#engine, D042#artifacts, D060#lifecycle
- **[ONLY HERE]** On failure or timeout, `context.signal` aborts and `endAttempt` runs.
    term `context.signal` also in 8: D005#write-a-provider, D005#recording-on-the-provider, D035#hosted-devices, D042#actions, D042#session, D042#shared-semantics, D042#artifacts, D060#the-shape-of-an-engine
    term `endAttempt` also in 4: D042#defineengine, D042#engine, D042#artifacts, D060#lifecycle
- **[ONLY HERE]** **Warning** A value from `resolveSecret` is protected as text only.
    term `resolveSecret` also in 3: D042#engine, D042#shared-semantics, D060#handle-secrets
- **[ALSO: D053#options]** Reports, logs, and observations redact it and the attempt's text downloads are rewritten, but unlike a fill it withholds no screenshot or model pixels.
- **[ALSO: D042#engine, D045#soft-assertions]** Runs after the body has settled, and again after teardown, before the verdict.
- **[ALSO: D042#engine, D060#lifecycle]** It reports a failure on a path no step awaited, such as a request interceptor or a native dialog handler.
- **[ONLY HERE]** Runs after each attempt and tears down what `startAttempt` set up.
    term `startAttempt` also in 5: D042#defineengine, D042#engine, D042#artifacts, D060#lifecycle, D060#handle-secrets
- **[ONLY HERE]** A failure marks cleanup failed; the test keeps its status.
- **[ONLY HERE]** Runs one time per worker, including when `init` never ran.
    term `init` also in 59
- **[ONLY HERE]** Missing or aborted `context.reuseSignal` requires final cleanup.
- **[ALSO: D042#engine]** A live signal permits keeping run-owned resources for a replacement worker.
- **[ONLY HERE]** An engine that keeps resources must observe revocation until its hook settles.
- **[ONLY HERE]** Final shutdown, a forced interrupt, or parent disconnect revokes that permission.
- **[ONLY HERE]** The cleanup budget still uses `context.signal` and `context.timeoutMs`.
    term `context.signal` also in 8: D005#write-a-provider, D005#recording-on-the-provider, D035#hosted-devices, D042#actions, D042#session, D042#shared-semantics, D042#artifacts, D060#the-shape-of-an-engine
- **[ONLY HERE]** Cleanup is best effort within that budget.
- **[ONLY HERE]** The runner does not guarantee cleanup after a worker exits or after disposal settles with reuse permission.

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D005#write-a-provider: Both describe slot and slots for a worker and cleanup within cleanupTimeout.
- D035#hosted-devices: Both describe provider slot/slots handed per worker and release running after the last worker, within cleanupTimeout.
- D041#top-level: Both state init/startAttempt run within launchTimeout and cleanup hooks within cleanupTimeout.
- D042#engine: Both describe the engine lifecycle hooks, EnginePrepareResult, and that init must work on a disposed engine and finish releases what prepare acquired.
- D042#app: Both describe EngineAppInfo handed to prepare and init, and init never learning the app URL.
- D047#engine: Both state devices boot in prepare, once per run before the run's clock starts, not charged to launchTimeout.
- D060#lifecycle: Both list the engine hooks prepare, init, startAttempt, settleAttempt, endAttempt, dispose and finish with when each runs.
- D060#handle-secrets: Both say to read a declared secret in startAttempt with context.resolveSecret and redact derived values under its name.

## S47 · multi-section · D042#app  (e2e/engine › Reference › App; page title: e2e/engine)

Regel: mindestens zwei Abschnitte, jeder liefert einen nötigen Teil; enthaltene oder umschließende Abschnitte zählen nicht als zweiter; H1 nur mit Grund in `notes`.

**Typ-Eignung:** Ziel `comparative`: Web- gegen Gerätetarget aus Sicht der Engine. Hier: „`@e2e-dev/web` requires `url`; `@e2e-dev/mobile` requires `bundleId` or `appPath` and refuses `url`“ und die Tabelle, was die Engine von `url` sieht (nur `validateApp`, geöffnet über `session.open`) und von den Gerätefeldern (`info.app` in `prepare` und `init`). Zweiter Abschnitt mit eigenem Teil: D047#engine (The app under test): „`app.open()` launches the target's app fresh“, „`app.open` takes no path on a device: a link goes through `device.openLink`“. Vorsicht: Die Anforderungen selbst stehen auch in D041#the-app-under-test („A `mobile()` target needs `app.bundleId` or `app.appPath`“), D044#runner-codes (`INVALID_CONFIG`) und in der Capabilities-Tabelle von D047#engine (`validateApp`); nennt die Antwort sie, sind diese Abschnitte relevant. Ebenso steht der Teil aus D047#engine auch in D039#open („On a device target, which has no URL, `open()` launches the pinned app fresh and takes no path“) und im JSDoc von D039#types; nennt die Antwort ihn, sind beide relevant. Alternative `limitation` (wenn `comparative` schon anders vergeben ist): was eine Engine nie zu sehen bekommt, „`command`, `readyUrl` | Never. The runner starts the app.“ und die URL, „which a surface never gets“ (beide nur hier), mit D042#lifecycle („`init` never learns the app URL; URLs arrive through `session.open` only“, nur dort) als zweitem Abschnitt.

- **[ALSO: D047#engine, D053#options, D060#the-shape-of-an-engine]** The app under test is declared on the target (`targets: [{ engine, app }]`, see [the app under test](/reference/config#the-app-under-test)); an engine only drives it.
- **[ONLY HERE]** The harness checks the shape of every field.
- **[ONLY HERE]** Then it hands the declaration to [`validateApp`](#validateapp) at config load.
    term `validateApp` also in 6: D042#defineengine, D042#engine, D042#capabilities, D047#engine, D060#the-shape-of-an-engine, D060#capabilities
- **[ONLY HERE]** | `url` | `validateApp` only. The harness opens it through `session.open`. |
    term `url` also in 141
    term `validateApp` also in 6: D042#defineengine, D042#engine, D042#capabilities, D047#engine, D060#the-shape-of-an-engine, D060#capabilities
    term `session.open` also in 5: D038#action-tools, D039#open, D042#capabilities, D042#lifecycle, D060#capabilities
- **[ONLY HERE]** | the site of `url` | `info.app.site` in `prepare` and `init` |
    term `url` also in 141
    term `prepare` also in 19
    term `init` also in 59
- **[ONLY HERE]** | `bundleId`, `appPath`, `launchArguments`, `permissions` | `validateApp`, and `info.app` in `prepare` and `init`, as the target declared them |
    term `bundleId` also in 33
    term `appPath` also in 16
    term `launchArguments` also in 10: D031#port-the-config, D032#map-each-command, D035#launch-arguments-and-permissions, D035#expo-development-builds, D035#physical-devices, D041#the-app-under-test, D047#engine, D047#device, D047#device-fixture, D053#options
    term `permissions` also in 22
    term `validateApp` also in 6: D042#defineengine, D042#engine, D042#capabilities, D047#engine, D060#the-shape-of-an-engine, D060#capabilities
    term `info.app` also in 1: D060#the-shape-of-an-engine
    term `prepare` also in 19
    term `init` also in 59
- **[ONLY HERE]** | `command`, `readyUrl` | Never. The runner starts the app. |
    term `command` also in 81
    term `readyUrl` also in 7: D035#expo-development-builds, D041#the-app-under-test, D044#agenterror, D044#runner-codes, D046#several-sessions, D051#outbound-connections, D059#let-the-runner-start-it
- **[ONLY HERE]** `CommandConfig` is exported from `e2e`, not `e2e/engine`.
    term `CommandConfig` also in 2: D041#the-app-under-test, D041#commandconfig
    term `e2e` also in 315
    term `e2e/engine` also in 10: D005#recording-on-the-provider, D018#executors, D035#hosted-devices, D042#defineengine, D042#artifacts, D042#exported-names, D060#writing-an-engine, D060#the-shape-of-an-engine, D060#handle-secrets, D060#next
- **[ONLY HERE]** Checks the declared app at config load, synchronously.
- **[ALSO: D039#baseurl, D039#open, D039#types, D042#contributed-fixtures, D044#runner-codes, D053#the-browser-fixture]** - It runs for every target the engine serves, with `{}` for a target that declares no `app`.
    term `app` also in 307
- **[ONLY HERE]** - `@e2e-dev/web` requires `url`; `@e2e-dev/mobile` requires `bundleId` or `appPath` and refuses `url`.
    term `@e2e-dev/web` also in 54
    term `url` also in 141
    term `@e2e-dev/mobile` also in 33
    term `bundleId` also in 33
    term `appPath` also in 16
- **[ALSO: D042#engine, D060#capabilities]** | `INVALID_CONFIG` | A field the platform needs is missing, or the engine cannot drive one. Name `info.targetName` in the message. |
    term `INVALID_CONFIG` also in 42
    term `info.targetName` also in 2: D042#engine, D060#capabilities
- **[ONLY HERE]** The resolved app, as `EnginePrepareInfo.app` and `EngineInitInfo.app`: the site of the URL and the device fields as the target declared them.
- **[ONLY HERE]** Apply the site to a URL with [`sameSite`](#site-helpers).
    term `sameSite` also in 2: D042#shared-semantics, D053#the-browser-fixture

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D041#the-app-under-test: Both describe the app under test declared on the target and runner-started command and readyUrl, which the engine never receives.
- D042#defineengine: Both say the app is declared on the target and checked in validateApp.
- D042#engine: Both list validateApp and EngineAppDeclaration as the engine's config-load check of the target's app.
- D042#capabilities: Both state validateApp is a config-load check of the target's app, and app.url or bundleId decide capabilities.
- D042#lifecycle: Both describe EngineAppInfo handed to prepare and init, and that init never learns the app URL.
- D042#shared-semantics: Both describe siteOf and sameSite applied to EngineAppInfo.site.
- D047#engine: Both state a device target needs app.bundleId or app.appPath, which the mobile engine's validateApp enforces and refuses url.
- D060#the-shape-of-an-engine: Both show a validateApp example throwing INVALID_CONFIG for a missing app field, with info.app in init.
- D060#capabilities: Both state validateApp checks the target's app at config load and throws INVALID_CONFIG naming the target.

## S48 · multi-section · D017#pick-an-example  (Example projects › Pick an example; page title: Example projects)

Regel: mindestens zwei Abschnitte, jeder liefert einen nötigen Teil; enthaltene oder umschließende Abschnitte zählen nicht als zweiter; H1 nur mit Grund in `notes`.

**Typ-Eignung:** Ziel `procedural`: ein Beispielprojekt wählen und ausführen. Hier: welches Beispiel welche Plattform testet und welche der Runner startet (Next.js, Astro). Zweiter Abschnitt mit eigenem Teil: D017#run-an-example: „Follow the project's README to install, build, and run it“, Konfiguration und Tests in einem `e2e/`-Ordner bei den nativen, Flutter- und .NET-MAUI-Projekten, „The locator tests need no model. The agent tests … skip unless `AI_GATEWAY_API_KEY` is set“ (`find "skip unless"`: nur dort). Nicht als zweiter Abschnitt zählt D017#example-projects (H1, umschließt beide). Die Web-Beispiele (Vite, Next.js, Astro) und die Plattformangaben stehen nur hier; die Links der sechs mobilen Beispiele stehen auch in D035#test-ids-by-framework (dort je Framework mit dem Attribut für Test-IDs).

- **[ONLY HERE]** - [Vite](https://github.com/tester-army/e2e/tree/main/examples/with-vite): React with Vite, tested in Chromium.
- **[ONLY HERE]** - [Next.js](https://github.com/tester-army/e2e/tree/main/examples/with-next): Next.js App Router, started by the runner and tested in Chromium.
- **[ONLY HERE]** - [Astro](https://github.com/tester-army/e2e/tree/main/examples/with-astro): An Astro page with no UI framework, started by the runner and tested in Chromium.
- **[ALSO: D021#index]** - [Expo](https://github.com/tester-army/e2e/tree/main/examples/with-expo): React Native with Expo, tested on web, iOS, and Android.
- **[ONLY HERE]** - [SwiftUI](https://github.com/tester-army/e2e/tree/main/examples/with-swiftui): A native iOS app, tested on an iPhone simulator.
- **[ONLY HERE]** - [Jetpack Compose](https://github.com/tester-army/e2e/tree/main/examples/with-compose): A native Android app, tested on an emulator.
- **[ONLY HERE]** - [Kotlin Multiplatform](https://github.com/tester-army/e2e/tree/main/examples/with-kotlin-multiplatform): One Compose Multiplatform screen, tested on Android and iOS.
- **[ONLY HERE]** - [Flutter](https://github.com/tester-army/e2e/tree/main/examples/with-flutter): A Flutter app, tested on Android and iOS.
- **[ONLY HERE]** - [.NET MAUI](https://github.com/tester-army/e2e/tree/main/examples/with-maui): A .NET MAUI app, tested on Android and iOS.

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D035#test-ids-by-framework: Both link the example projects with-expo, with-swiftui, with-compose, with-kotlin-multiplatform, with-flutter and with-maui for each framework.
