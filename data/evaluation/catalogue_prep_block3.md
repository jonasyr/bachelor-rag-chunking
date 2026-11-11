# Vorbereitungsblatt Block 3 (S17–S24)

KI-Hilfe (Claude) vor dem Schreiben, offengelegt nach ADR 0031/0049. Mechanischer Teil wie bei Block 1 und 2: je Satz
des Ausgangsabschnitts (ohne Codeblöcke; Tabellenzeilen zählen je als ein Satz), ob eine Folge von 5 Wörtern auch im
eigenen Text eines anderen Abschnitts steht (außer umschließenden und enthaltenen Abschnitten), und für Begriffe in
Backticks, in welchen anderen Abschnitten sie vorkommen (nur bei höchstens 10 Treffern gelistet, dann vollständig).
Dazu die Zeilen aus `catalogue_overlap.csv`. Neu je Slot (ADR 0049, Nachtrag 10.11.2026): **Typ-Eignung**, also welche
Fragetypen der Text trägt, mit der Stelle, auf die sich der Typ stützt, und ob sie nur hier steht. Das ist ein
Vorschlag; den Typ wählt Jonas (ADR 0031). Das Blatt enthält keine Frage, keine Antwort und kein Relevanzurteil.
„ONLY HERE“ heißt nur: kein wörtlicher Treffer; anders formulierte Stellen mit gleichem Inhalt findet es nicht (dafür
„Also covered elsewhere“ im Editor). Erstellt am 10.11.2026.

Typziel Block 3 ([Plan](../../docs/plan.md#stand)): 3 conceptual, 2 comparative, 1 limitation, 1 procedural,
1 factual. Die Abschnitte tragen nach dieser Prüfung eher **4 conceptual, 1 comparative**, 1 limitation,
1 procedural, 1 factual: Ein zweites `comparative` fand sich in keinem Slot, ohne die Klassenregel zu brechen
(siehe S17, S19, S22). Das fehlende `comparative` wandert in Block 4.

## S17 · paraphrase · D030#map-each-command  (From Cypress › Map each command; page title: From Cypress)

Regel: genau ein Abschnitt; die Frage teilt kein Inhaltswort mit der Abschnittsüberschrift oder dem Seitentitel (auch keine Wortformen).

**Typ-Eignung:** Komparativ geht hier kaum: `comparative` braucht zwei benannte Dinge, und „Cypress“ ist als Wort des Seitentitels in der Frage verboten (ebenso „map“, „command(s)“). Der Abschnitt trägt `procedural`: wie man in e2e etwas erledigt, für das man einen bestimmten Aufruf hatte, ohne ihn beim Namen „Cypress“ zu nennen. Wörtlich nur hier: die Zeilen zu `cy.task`/`cy.exec`/`cy.request` (Node-Code: `fetch`, `fs`, Datenbank-Client), `cy.wait(ms)` (Locator-Assertion statt Wartezeit), `cy.contains('li', 'text')` (`filter({ hasText })`). Vorsicht: „await each call“, „one match oder `LOCATOR_AMBIGUOUS`“ und die Zeilen zu `browser.route`, `test.setup`/`{ session }` stehen auch in D031, D033, D034 oder D050. Backticks wie `cy.wait` lösen die Wortsperre nicht aus (im Editor geprüft: kein gemeinsames Wort mit dem Seitentitel).

- **[ONLY HERE]** ## Map each command Two things differ from Cypress:
- **[(short, not compared)]** - There is no chain.
- **[ONLY HERE]** Await each call on its own line.
- **[(short, not compared)]** It returns a value:
- **[(short, not compared)]** `const text = await locator.textContent()`.
- **[ALSO: D031#map-each-detox-call]** - Actions and single-node reads and assertions need one match.
- **[(short, not compared)]** Several fail with `LOCATOR_AMBIGUOUS`.
- **[ALSO: D031#map-each-detox-call, D034#map-each-webdriver-call]** Narrow with `.filter()`, `.first()`, or `.nth()`.
    term `.filter()` also in 3: D014#locators, D031#map-each-detox-call, D034#map-each-webdriver-call
    term `.first()` also in 6: D014#locators, D031#map-each-detox-call, D032#rewrite-selectors, D034#map-each-webdriver-call, D050#queries, D050#refinement
    term `.nth()` also in 3: D014#locators, D031#map-each-detox-call, D034#map-each-webdriver-call
- **[(short, not compared)]** | `cy.visit(path)` | `app.open(path)` |
    term `app.open(path)` also in 2: D033#map-each-api, D034#map-each-webdriver-call
- **[ONLY HERE]** | `cy.get('[data-cy=x]')` | `screen.getByTestId('x')` |
    term `screen.getByTestId('x')` also in 3: D031#map-each-detox-call, D032#map-each-command, D034#map-each-webdriver-call
- **[ALSO: D034#map-each-webdriver-call]** | `cy.get('css')` | `browser.locator('css')`, not portable; prefer a role or label |
    term `browser.locator('css')` also in 1: D033#map-each-api
- **[ONLY HERE]** | `cy.contains('text')` | `screen.getByText('text', { exact: false })` |
- **[ONLY HERE]** | `cy.contains('li', 'text')` | `screen.getByRole('listitem').filter({ hasText: 'text' })` |
- **[ONLY HERE]** | `.find()`, `.within()` | Chain a query off the locator: `row.getByRole(...)` |
- **[ONLY HERE]** | `.first()`, `.eq(n)` | `.first()`, `.nth(n)` |
    term `.first()` also in 6: D014#locators, D031#map-each-detox-call, D032#rewrite-selectors, D034#map-each-webdriver-call, D050#queries, D050#refinement
    term `.nth(n)` also in 2: D031#map-each-detox-call, D034#map-each-webdriver-call
- **[ONLY HERE]** | `.click()`, `.dblclick()`, `.rightclick()` | `.tap()`, `.doubleTap()` (or `.dblclick()`), `.secondaryTap()` |
    term `.click()` also in 10: D013#how-an-agent-writes-and-runs-a-test, D018#driving-the-page-yourself, D026#test-an-app-flow, D027#start-every-test-signed-in, D030#rewrite-one-spec, D033#map-each-api, D033#port-page-objects, D033#rewrite-one-spec, D034#map-each-webdriver-call, D034#rewrite-one-flow
    term `.doubleTap()` also in 3: D031#map-each-detox-call, D032#map-each-command, D050#locator-actions
    term `.secondaryTap()` also in 1: D050#locator-actions
- **[ALSO: D034#map-each-webdriver-call]** | `.type('text')` | `.fill('text')` replaces the content |
    term `.fill('text')` also in 2: D032#map-each-command, D034#map-each-webdriver-call
- **[(short, not compared)]** | `.type('{enter}')` | `.press('Enter')` |
    term `.press('Enter')` also in 5: D026#check-app-compatibility, D031#map-each-detox-call, D032#map-each-command, D034#map-each-webdriver-call, D050#locator-actions
- **[ONLY HERE]** | `.clear()`, `.check()`, `.select()` | `.clear()`, `.check()`, `.selectOption()` |
    term `.check()` also in 3: D050#locator-actions, D050#locator-reads, D050#refinement
    term `.clear()` also in 6: D031#map-each-detox-call, D032#map-each-command, D034#map-each-webdriver-call, D042#lifecycle, D050#locator-actions, D050#queries
- **[ONLY HERE]** | `.should('be.visible')` | `await expect(locator).toBeVisible()` |
    term `.should('be.visible')` also in 1: D030#rewrite-one-spec
    term `await expect(locator).toBeVisible()` also in 2: D032#map-each-command, D034#map-each-webdriver-call
- **[ONLY HERE]** | `.should('have.text', t)`, `.should('contain', t)` | `.toHaveText(t)`, `.toContainText(t)` |
    term `.toHaveText(t)` also in 1: D031#map-each-detox-call
- **[ONLY HERE]** | `.should('have.length', n)` | `.toHaveCount(n)` |
- **[ONLY HERE]** | `.should('have.value', v)` | `.toHaveValue(v)` |
    term `.toHaveValue(v)` also in 1: D031#map-each-detox-call
- **[ONLY HERE]** | `.should('not.exist')` | `.toHaveCount(0)`; `toBeHidden()` also accepts a node that is still in the DOM |
    term `toBeHidden()` also in 6: D031#map-each-detox-call, D032#map-each-command, D033#map-each-api, D045#locator-matchers, D050#queries, D059#resize-inside-a-test
- **[ONLY HERE]** | `cy.url().should('include', p)` | `expect(browser).toHaveURL(/p/)` |
- **[(short, not compared)]** | `cy.title()` | `expect(browser).toHaveTitle()` |
- **[ONLY HERE]** | `cy.intercept(url, body)` | `browser.route(url, route => route.fulfill({ json: body }))` |
- **[(short, not compared)]** | `cy.wait('@alias')` | `browser.waitForResponse(url)` |
- **[ONLY HERE]** | `cy.on('window:confirm')` | `browser.onDialog('accept')` |
    term `browser.onDialog('accept')` also in 4: D005#handle-a-dialog, D033#map-each-api, D034#map-each-webdriver-call, D053#the-browser-fixture
- **[(short, not compared)]** | `cy.session` | `test.setup` and `{ session }` |
    term `{ session }` also in 7: D031#map-each-detox-call, D032#what-differs-on-purpose, D033#browser-timeouts-and-artifacts, D033#what-differs-on-purpose, D034#port-the-config, D040#commands, D052#options
- **[ONLY HERE]** | `cy.task`, `cy.exec`, `cy.request` | Node code: `fetch`, `fs`, your database client |
- **[ONLY HERE]** | `cy.fixture` | `import data from './fixture.json'` |
- **[ALSO: D032#map-each-command]** | `Cypress.Commands.add` | A function, or a fixture from `test.extend` |
- **[ALSO: D034#map-each-webdriver-call]** | `cy.wait(ms)` | Use a locator assertion for the condition you need |
- **[ONLY HERE]** | `cypress open` | `npx e2e run --headed`, plus `--debug` for the step table |
    term `--debug` also in 9: D001#what-a-step-costs, D002#make-the-agent-yours, D015#agent-steps, D015#artifacts, D018#what-the-context-holds, D033#map-each-api, D040#commands, D043#diagnostics, D044#agenterror
    term `npx e2e run --headed` also in 1: D015#watch-it-happen

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D015#watch-it-happen: Both say npx e2e run --headed shows the browser while the test runs.
- D015#agent-steps: Both say --debug prints the agent step table.
- D003#api-testing: Both say API calls are made from test code with Node fetch.
- D004#sign-in-once-in-a-setup-test: Both say a session is created in test.setup and restored with the session option.
- D005#mock-an-api: Both show mocking a response with browser.route and waiting with browser.waitForResponse.
- D005#handle-a-dialog: Both show browser.onDialog('accept') to handle a confirm dialog.
- D005#read-from-the-page: Both use browser.evaluate to run a function in the page.
- D005#cookies: Both use browser.setCookies to set a cookie.
- D015#watch-it-happen: Both say npx e2e run --headed shows the browser while the test runs.
- D015#agent-steps: Both say --debug prints the agent step table.
- D031#map-each-detox-call: Both map test commands to e2e equivalents such as doubleTap, toBeHidden and the LOCATOR_AMBIGUOUS single-match rule.
- D032#map-each-command: Both map test commands to e2e equivalents such as doubleTap, toBeHidden and a fixture from test.extend.
- D033#map-each-api: Both map framework commands to e2e equivalents such as browser.setCookies, browser.onDialog, browser.setViewport, browser.evaluate, doubleTap and secondaryTap.
- D033#what-differs-on-purpose: Both say actions and reads need exactly one match, otherwise LOCATOR_AMBIGUOUS.
- D034#map-each-webdriver-call: Both map legacy test calls to e2e equivalents such as browser.setCookies, browser.onDialog, browser.evaluate and test.extend fixtures.
- D045#locator-matchers: Both list locator assertions toBeVisible, toHaveText, toContainText, toHaveCount and toHaveValue.
- D045#browser-matchers: Both cover expect(browser).toHaveURL and toHaveTitle.
- D045#strictness: Both say assertions on several matches fail immediately with LOCATOR_AMBIGUOUS, and toBeHidden accepts a hidden node.
- D050#queries: Both cover getByTestId, getByText with exact false, and getByRole queries.
- D050#locator-actions: Both list locator actions tap, doubleTap, secondaryTap, clear, selectOption and setInputFiles, and LOCATOR_AMBIGUOUS on several matches.
- D052#fixtures: Both say test.extend defines custom fixtures for setup and helpers.
- D053#the-browser-fixture: Both name browser fixture methods setCookies, setViewport, evaluate, waitForResponse, onDialog and route.
- D059#resize-inside-a-test: Both use browser.setViewport to resize the page during a test.
- D032#map-each-command: Both map reusable flows and text reads to a function or test.extend fixture and locator.textContent.
- D032#rewrite-selectors: Both say several matches fail with LOCATOR_AMBIGUOUS and are narrowed with filter(), first() or nth(), and fragment text uses { exact: false }.
- D033#browser-timeouts-and-artifacts: Both map setting cookies to browser.setCookies.
- D033#map-each-api: Both map click/dblclick/rightclick, select, setInputFiles, route, waitForResponse, onDialog and setCookies calls to e2e equivalents.
- D033#what-differs-on-purpose: Both say several matches fail with LOCATOR_AMBIGUOUS and are narrowed with filter(), first() or nth().
- D050#refinement: Both map Cypress contains, first and eq to filter({ hasText }), first() and nth(n).
- D050#locator-actions: Both show doubleTap/dblclick, secondaryTap, selectOption and setInputFiles as the click, select and file actions.
- D053#the-browser-fixture: Both map Cypress intercept, visit and cookie commands to browser.route, goto and setCookies.

## S18 · single · D033#map-each-api  (From Playwright › Map each API; page title: From Playwright)

Regel: genau ein Abschnitt, dessen Hauptinhalt die Antwort ist; jeder Teil der Antwort muss nur hier stehen.

**Typ-Eignung:** Trägt `limitation`: Zeilen mit Status `missing` sagen, was e2e von Playwright nicht hat und was man heute stattdessen tut. Wörtlich nur hier z. B. `locator.and(other)`/`locator.or(other)` (not yet), `selectOption(['a', 'b'])` (eine Option je Aufruf, Array ist `INVALID_ARGUMENT`), `setInputFiles({ name, buffer })` (nur Pfade). Für `single` eine Gruppe der Tabelle nehmen (Locators oder Actions), nicht die ganze Tabelle. Vorsicht: `tap({ position })` steht auch in D050#locator-actions, `filter({ hasNot })` in D050#refinement, die `toHaveScreenshot`-Optionen in D045#screenshot-matchers. `comparative` ist schwach, weil die `by design`-Zeilen in D033#what-differs-on-purpose erklärt sind (zweiter Abschnitt).

- **[ONLY HERE]** ## Map each API `Status` is `same`, `renamed`, `web only`, `by design`, or `missing` with what to do today.
    term `Status` also in 6: D031#map-each-detox-call, D033#app-targets-and-output, D033#browser-timeouts-and-artifacts, D040#commands, D045#polling-a-value, D048#custom-reporters
    term `by design` also in 1: D033#browser-timeouts-and-artifacts
    term `renamed` also in 3: D033#app-targets-and-output, D033#browser-timeouts-and-artifacts, D052#fixtures
    term `web only` also in 1: D033#port-page-objects
- **[ALSO: D033#browser-timeouts-and-artifacts]** See [What differs on purpose](#what-differs-on-purpose) for the `by design` rows.
    term `by design` also in 1: D033#browser-timeouts-and-artifacts
- **[ALSO: D032#map-each-command]** Calls on `browser` run only in a browser, so a test that uses it declares `requires: ['browser']` and other targets skip it.
    term `requires: ['browser']` also in 5: D005#browser, D033#port-page-objects, D052#fixtures, D053#options, D053#the-browser-fixture
- **[ALSO: D032#map-each-command]** Calls on `screen`, `app`, `agent`, and `expect(locator)` run on every target.
- **[ONLY HERE]** **Locators** **Actions** **Assertions** **Navigation and app** **Network and browser** **Test structure** **CLI**
- **[ONLY HERE]** | `page.getByRole`, `getByLabel`, `getByText`, `getByTestId`, `getByPlaceholder` | the same on `screen`; `getByRole` also takes the name positionally, `getByRole('button', 'Save')` | same |
    term `getByPlaceholder` also in 3: D005#shadow-dom, D033#what-differs-on-purpose, D050#queries
    term `getByRole('button', 'Save')` also in 3: D033#what-differs-on-purpose, D050#locator-actions, D050#queries
    term `page.getByRole` also in 3: D018#driving-the-page-yourself, D027#start-every-test-signed-in, D033#rewrite-one-spec
- **[ALSO: D033#browser-timeouts-and-artifacts]** | `getByRole(role, { name })`, `getByLabel`, `getByPlaceholder`, `getByText` with a string | an exact, case-sensitive match, see [What differs on purpose](#what-differs-on-purpose) | by design |
    term `getByPlaceholder` also in 3: D005#shadow-dom, D033#what-differs-on-purpose, D050#queries
- **[ONLY HERE]** | `getByRole('img')` | the same; `img` is an alias of `image` | same |
    term `img` also in 2: D050#queries, D050#types
- **[ONLY HERE]** | `getByAltText(alt)` | `getByRole('image', alt)` | renamed |
- **[ONLY HERE]** | `getByTitle` | the node carries no title | missing |
- **[ALSO: D050#queries, D050#types]** | `getByRole(role, { includeHidden })` | a role query never matches a hidden node; `{ visible: true }` on the other queries drops hidden twins | by design |
    term `{ visible: true }` also in 6: D005#reach-into-an-iframe, D015#common-errors, D032#rewrite-selectors, D033#what-differs-on-purpose, D042#queries, D050#queries
- **[ONLY HERE]** | `locator.filter({ hasText, has })`, `first()`, `last()`, `nth(i)`, `count()` | the same | same |
    term `count()` also in 4: D034#map-each-webdriver-call, D035#troubleshooting, D050#locator-reads, D050#match-rules
    term `first()` also in 9: D014#locators, D015#common-errors, D030#map-each-command, D031#map-each-detox-call, D032#rewrite-selectors, D033#what-differs-on-purpose, D034#map-each-webdriver-call, D050#queries, D050#refinement
    term `last()` also in 1: D050#refinement
    term `nth(i)` also in 1: D050#locator-reads
- **[ONLY HERE]** | `filter({ hasNot, hasNotText })` | a positive filter or `nth`. `INVALID_LOCATOR`, alone or beside `hasText` or `has` | missing |
    term `INVALID_LOCATOR` also in 8: D042#errors, D042#shared-semantics, D044#runner-codes, D050#locator-actions, D050#queries, D050#refinement, D050#screen-actions, D053#the-browser-fixture
    term `hasText` also in 8: D005#shadow-dom, D014#locators, D030#map-each-command, D032#rewrite-selectors, D046#the-catalog, D050#reference-screen, D050#refinement, D053#the-browser-fixture
- **[ONLY HERE]** | `locator.and(other)`, `locator.or(other)` | not yet | missing |
- **[ONLY HERE]** | `locator.all()`, `allTextContents()` | the same; `allInnerTexts()` is `allTextContents()` | same |
    term `allTextContents()` also in 2: D050#locator-reads, D050#match-rules
- **[ALSO: D053#the-browser-fixture]** | `page.locator('css')`, `page.locator('xpath=...')` | `browser.locator('css')`: the string is a Playwright selector, so `xpath=` (or a leading `//`) and `>>` chains work too | web only |
    term `browser.locator('css')` also in 1: D030#map-each-command
    term `xpath=` also in 1: D053#the-browser-fixture
- **[ALSO: D033#browser-timeouts-and-artifacts]** | `page.waitForSelector(selector)` | `browser.locator(selector).waitFor()`; a locator is strict, see [What differs on purpose](#what-differs-on-purpose) | renamed |
- **[ALSO: D033#browser-timeouts-and-artifacts]** | `page.click(selector)`, `page.fill(selector, value)`, `page.getAttribute(selector, name)`, and the other `page` methods that take a selector | `browser.locator(selector).tap()`, `.fill(value)`, `.getAttribute(name)`. Playwright acts on the first match; a locator is strict, so add `first()` for the
    term `first()` also in 9: D014#locators, D015#common-errors, D030#map-each-command, D031#map-each-detox-call, D032#rewrite-selectors, D033#what-differs-on-purpose, D034#map-each-webdriver-call, D050#queries, D050#refinement
- **[ONLY HERE]** | `locator.locator('css')` | a semantic query inside the scope (`cell.getByRole('textbox')` for `cell.locator('input')`), `browser.locator('css').getByRole(...)` the other way round, or one `browser.locator` selector for the whole path | missing |
    term `browser.locator` also in 10: D005#icon-fonts-and-generated-content, D005#reach-into-an-iframe, D005#shadow-dom, D030#map-each-command, D033#what-differs-on-purpose, D034#map-each-webdriver-call, D037#run-your-first-test, D045#browser-matchers, D050#queries, D053#the-browser-fixture
- **[ONLY HERE]** | `page.frameLocator('#frame')` | `browser.frameLocator('#frame')`, then `screen` queries inside it | web only |
    term `browser.frameLocator('#frame')` also in 1: D034#map-each-webdriver-call
- **[ONLY HERE]** | `locator.click()` | `locator.tap()`; `click()` is an alias | same |
    term `click()` also in 10: D013#how-an-agent-writes-and-runs-a-test, D018#driving-the-page-yourself, D026#test-an-app-flow, D027#start-every-test-signed-in, D030#map-each-command, D030#rewrite-one-spec, D033#port-page-objects, D033#rewrite-one-spec, D034#map-each-webdriver-call, D034#rewrite-one-flow
- **[ONLY HERE]** | `click({ button: 'right' })` | `secondaryTap()` | renamed |
    term `secondaryTap()` also in 2: D030#map-each-command, D050#locator-actions
- **[ONLY HERE]** | `dblclick()` | `doubleTap()`; `dblclick()` is an alias | same |
    term `dblclick()` also in 1: D030#map-each-command
    term `doubleTap()` also in 5: D030#map-each-command, D031#map-each-detox-call, D032#map-each-command, D035#known-device-limitations, D050#locator-actions
- **[ALSO: D050#locator-actions]** | `click({ position })` | `tap({ position })`, an offset from the node's top-left corner | renamed |
    term `tap({ position })` also in 5: D042#capabilities, D042#engine, D047#engine, D050#screen-actions, D050#types
- **[ONLY HERE]** | `click({ force })` | `tap({ position })` skips every actionability check but the scroll into view | missing |
    term `tap({ position })` also in 5: D042#capabilities, D042#engine, D047#engine, D050#screen-actions, D050#types
- **[ONLY HERE]** | `click({ modifiers })`, `dblclick({ modifiers })` | `tap({ modifiers })`, `doubleTap({ modifiers })` or `dblclick({ modifiers })`, `secondaryTap({ modifiers })`; not beside `position` yet | same |
- **[ONLY HERE]** | `click({ clickCount, delay, trial })` | not yet | missing |
- **[ONLY HERE]** | `{ trial }`, `{ force }`, `{ noWaitAfter }` on `check()`, `fill()`, and the other actions | an unknown option is `INVALID_ARGUMENT`, never ignored | missing |
    term `check()` also in 5: D030#map-each-command, D033#what-differs-on-purpose, D050#locator-actions, D050#locator-reads, D050#refinement
- **[ONLY HERE]** | `fill(value)` | the same; also takes a `Secret` | same |
- **[ONLY HERE]** | `pressSequentially(text, { delay })` | the same; keystrokes through the platform keyboard, a `Secret` is refused | same |
- **[ALSO: D050#locator-actions, D060#keyboard]** | `press(key)` | the same; modifiers join with `+`, see the [key grammar](/reference/engine#keys) | same |
- **[ONLY HERE]** | `clear()`, `focus()`, `hover()`, `setInputFiles()`, `dragTo()` | the same | same |
    term `clear()` also in 7: D030#map-each-command, D031#map-each-detox-call, D032#map-each-command, D034#map-each-webdriver-call, D042#lifecycle, D050#locator-actions, D050#queries
    term `focus()` also in 1: D050#locator-actions
    term `hover()` also in 2: D034#map-each-webdriver-call, D050#locator-actions
    term `setInputFiles()` also in 1: D030#map-each-command
- **[ALSO: D033#browser-timeouts-and-artifacts]** | `check()`, `uncheck()` | the same, except when the state updates late or the click removes the control, see [What differs on purpose](#what-differs-on-purpose) | by design |
    term `check()` also in 5: D030#map-each-command, D033#what-differs-on-purpose, D050#locator-actions, D050#locator-reads, D050#refinement
    term `uncheck()` also in 2: D033#what-differs-on-purpose, D050#locator-actions
- **[ONLY HERE]** | `selectOption('pro')` | `selectOption('Pro')`: a string matches the option's label only, where Playwright matches its value or its label; `selectOption({ value: 'pro' })` for the value | by design |
    term `selectOption('Pro')` also in 1: D050#locator-actions
    term `selectOption({ value: 'pro' })` also in 1: D050#locator-actions
- **[ONLY HERE]** | `selectOption(['a', 'b'])` | one option per call. An array is `INVALID_ARGUMENT` | missing |
- **[ALSO: D040#commands]** | `setInputFiles({ name, buffer })` | paths only, resolved from the project root | missing |
- **[ONLY HERE]** | `locator.innerText()` | `textContent()`, whitespace collapsed to single spaces | renamed |
- **[ALSO: D033#browser-timeouts-and-artifacts]** | `locator.textContent()` | the rendered text, what `innerText()` reads, see [What differs on purpose](#what-differs-on-purpose) | by design |
    term `locator.textContent()` also in 3: D007#when-a-recording-is-written, D030#map-each-command, D032#map-each-command
- **[ONLY HERE]** | `inputValue()`, `getAttribute()`, `isVisible()`, `isHidden()`, `isEnabled()`, `isDisabled()`, `boundingBox()` | the same | same |
    term `boundingBox()` also in 3: D050#locator-reads, D050#screen-actions, D050#types
    term `getAttribute()` also in 2: D034#map-each-webdriver-call, D045#secure-fields
    term `inputValue()` also in 3: D045#secure-fields, D050#locator-reads, D050#queries
    term `isDisabled()` also in 1: D050#locator-reads
    term `isEnabled()` also in 1: D050#locator-reads
    term `isHidden()` also in 2: D050#locator-reads, D050#match-rules
    term `isVisible()` also in 8: D032#map-each-command, D032#rewrite-selectors, D033#what-differs-on-purpose, D034#map-each-webdriver-call, D035#troubleshooting, D050#locator-reads, D050#match-rules, D050#queries
- **[ALSO: D033#browser-timeouts-and-artifacts]** | `isChecked()` | the same on a checkbox, radio, or `aria-checked` node; `false` on any other, see [What differs on purpose](#what-differs-on-purpose) | by design |
    term `isChecked()` also in 2: D033#what-differs-on-purpose, D050#locator-reads
- **[(short, not compared)]** | `isEditable()` | not yet | missing |
- **[ONLY HERE]** | `waitFor({ state: 'visible' })`, `'hidden'`, `'attached'`, `'detached'` | the same | same |
    term `'attached'` also in 1: D050#locator-reads
    term `'detached'` also in 2: D045#strictness, D050#locator-reads
    term `'hidden'` also in 3: D042#semanticnode, D045#strictness, D050#locator-reads
- **[ONLY HERE]** | `locator.evaluate(fn)`, `evaluateAll(fn)` | `browser.evaluate(fn, selector)` with a CSS selector argument | missing |
- **[ONLY HERE]** | `locator.screenshot()` | `app.screenshot(label)` captures the viewport | missing |
- **[ONLY HERE]** | `innerHTML()`, `dispatchEvent()`, `selectText()`, `blur()`, `highlight()` | `browser.evaluate` | missing |
    term `browser.evaluate` also in 8: D005#read-from-the-page, D030#map-each-command, D033#what-differs-on-purpose, D034#map-each-webdriver-call, D044#runner-codes, D053#options, D053#the-browser-fixture, D059#scoping-a-test-to-one-size
- **[(short, not compared)]** | `ariaSnapshot()` | not yet | missing |
- **[ALSO: D053#the-browser-fixture]** | `page.keyboard.press`, `keyboard.type` | `browser.keyboard.press`, `browser.keyboard.type`; plain text only, never a `Secret` | web only |
    term `browser.keyboard.press` also in 1: D053#the-browser-fixture
    term `browser.keyboard.type` also in 2: D033#port-page-objects, D053#the-browser-fixture
    term `keyboard.type` also in 4: D033#port-page-objects, D042#capabilities, D053#the-browser-fixture, D060#keyboard
- **[ONLY HERE]** | `keyboard.down`, `keyboard.up` | `browser.keyboard.down`, `browser.keyboard.up`; keys and modifiers stay held until released | web only |
- **[(short, not compared)]** | `keyboard.insertText` | not yet | missing |
- **[ALSO: D032#map-each-command]** | `page.mouse.click(x, y)` | `screen.tapAt({ x, y })`, viewport coordinates | renamed |
    term `screen.tapAt({ x, y })` also in 1: D032#map-each-command
- **[ONLY HERE]** | `mouse.move`, `down`, `up` as a drag | `screen.swipe({ from, to })` | renamed |
    term `mouse.move` also in 1: D053#the-browser-fixture
- **[ONLY HERE]** | `page.dragAndDrop(source, target, { sourcePosition, targetPosition })` | `source.dragTo(target)`, which takes no positions; for `sourcePosition` or `targetPosition`, `screen.swipe({ from, to })` with each `boundingBox()` origin plus its offset | renamed |
    term `boundingBox()` also in 3: D050#locator-reads, D050#screen-actions, D050#types
    term `screen.swipe({ from, to })` also in 3: D042#capabilities, D042#engine, D047#engine
- **[ONLY HERE]** | `page.mouse.move`, `wheel`, `down`, `up` | `browser.mouse.*` | web only |
    term `wheel` also in 3: D047#engine, D053#browser-interface, D053#the-browser-fixture
- **[ONLY HERE]** | `expect(locator).toBeVisible()`, `toBeHidden()`, `toBeEnabled()`, `toBeDisabled()`, `toBeFocused()`, `toHaveValue()`, `toHaveAttribute()`, `toHaveCount()`, `toHaveAccessibleName()` | the same | same |
    term `expect(locator).toBeVisible()` also in 3: D030#map-each-command, D032#map-each-command, D034#map-each-webdriver-call
    term `toBeDisabled()` also in 1: D045#locator-matchers
    term `toBeEnabled()` also in 3: D032#map-each-command, D045#locator-matchers, D045#soft-assertions
    term `toBeFocused()` also in 2: D032#map-each-command, D045#locator-matchers
    term `toBeHidden()` also in 6: D030#map-each-command, D031#map-each-detox-call, D032#map-each-command, D045#locator-matchers, D050#queries, D059#resize-inside-a-test
- **[ALSO: D033#browser-timeouts-and-artifacts]** | `toBeChecked()` | the same on a checkable node; on any other node `.not.toBeChecked()` passes, see [What differs on purpose](#what-differs-on-purpose) | by design |
    term `.not.toBeChecked()` also in 2: D033#what-differs-on-purpose, D045#locator-matchers
    term `toBeChecked()` also in 4: D031#map-each-detox-call, D032#map-each-command, D033#what-differs-on-purpose, D045#locator-matchers
- **[ALSO: D033#browser-timeouts-and-artifacts]** | `toHaveText()`, `toContainText()` | compare the rendered text, see [What differs on purpose](#what-differs-on-purpose) | by design |
    term `toHaveText()` also in 1: D034#map-each-webdriver-call
- **[ONLY HERE]** | `toHaveText(['a', 'b'])`, `toContainText([...])` on several matches | the same: `toHaveText` needs the count to match, `toContainText` an ordered subsequence | same |
    term `toContainText([...])` also in 1: D045#locator-matchers
- **[ONLY HERE]** | `toBeChecked({ checked: false })`, `toBeEnabled({ enabled })`, `toBeVisible({ visible })`, `toBeAttached({ attached })` | the same | same |
    term `toBeChecked({ checked: false })` also in 1: D045#locator-matchers
- **[ONLY HERE]** | `{ ignoreCase }` on `toHaveText()`, `toContainText()`, `toHaveAccessibleName()`, `toHaveAttribute(name, value)` | the same | same |
    term `toHaveAttribute(name, value)` also in 1: D045#text-matching
    term `toHaveText()` also in 1: D034#map-each-webdriver-call
- **[ONLY HERE]** | `toBeChecked({ indeterminate })`, `{ useInnerText }` | `INVALID_ARGUMENT`, so the matcher never passes on its default | missing |
- **[ONLY HERE]** | `toHaveAttribute('aria-selected', 'true')`, `'aria-expanded'` | `toBeSelected()`, `toBeExpanded()` | renamed |
    term `toBeSelected()` also in 2: D032#map-each-command, D045#locator-matchers
- **[ALSO: D033#browser-timeouts-and-artifacts]** | a positive matcher on several matches | `LOCATOR_AMBIGUOUS` at once, see [What differs on purpose](#what-differs-on-purpose) | by design |
- **[ONLY HERE]** | `toBeAttached()` | the same; passes on a hidden match too | same |
    term `toBeAttached()` also in 1: D045#locator-matchers
- **[ONLY HERE]** | `toBeEmpty()`, `toBeInViewport()`, `toBeEditable()`, `toHaveRole()`, `toHaveAccessibleDescription()` | not yet | missing |
- **[ALSO: D045#browser-matchers]** | `expect(locator).toHaveClass(cls)` | `expect(browser).toHaveClass(locator, cls)`; a DOM fact is asserted through `browser`; reads the `class` attribute, so `''` matches `class=""` and not a missing attribute | web only |
- **[ONLY HERE]** | `toHaveCSS()`, `toHaveId()`, `toHaveJSProperty()`, `toContainClass()`, `toHaveValues()` | `browser.evaluate` plus a value matcher | missing |
    term `browser.evaluate` also in 8: D005#read-from-the-page, D030#map-each-command, D033#what-differs-on-purpose, D034#map-each-webdriver-call, D044#runner-codes, D053#options, D053#the-browser-fixture, D059#scoping-a-test-to-one-size
- **[ONLY HERE]** | `expect(page).toHaveURL()`, `toHaveTitle()` | `expect(browser).toHaveURL()`, `toHaveTitle()`; `toHaveURL` takes `ignoreCase` | web only |
    term `expect(browser).toHaveURL()` also in 1: D045#reference
    term `ignoreCase` also in 6: D042#shared-semantics, D045#asyncexpectation-and-textmatcheroptions, D045#browser-matchers, D045#browserexpectation, D045#locator-matchers, D045#text-matching
    term `toHaveTitle()` also in 1: D030#map-each-command
- **[ONLY HERE]** | `expect(page).toHaveScreenshot()`, `expect(locator).toHaveScreenshot()` | `expect(screen).toHaveScreenshot()`, `expect(locator).toHaveScreenshot()` on every target, a device included, with `threshold`, `maxDiffPixels`, `maxDiffPixelRatio`, `mask`, `maskColor`, and `timeout`. See [Visual comparison
    term `maskColor` also in 3: D045#screenexpectation-and-screenshotoptions, D045#screenshot-matchers, D058#tolerance-and-masks
    term `maxDiffPixelRatio` also in 4: D032#map-each-command, D045#screenexpectation-and-screenshotoptions, D045#screenshot-matchers, D058#tolerance-and-masks
    term `maxDiffPixels` also in 3: D045#screenexpectation-and-screenshotoptions, D045#screenshot-matchers, D058#tolerance-and-masks
    term `threshold` also in 6: D016#gates, D032#map-each-command, D045#screenexpectation-and-screenshotoptions, D045#screenshot-matchers, D047#engine, D058#tolerance-and-masks
- **[ONLY HERE]** | `toHaveScreenshot({ fullPage, clip, animations, caret, scale, stylePath })` | always the viewport, at CSS scale, animations stopped and the caret hidden | missing |
- **[ONLY HERE]** | `toMatchSnapshot()`, `toMatchAriaSnapshot()` | not yet | missing |
- **[ONLY HERE]** | `expect(value).toBe()`, `toEqual()`, `toMatch()`, `toBeTruthy()`, `toBeCloseTo()`, `toHaveLength()`, `toMatchObject()`, `toHaveProperty()`, and the rest | the same, except `toContain`, below, see [value matchers](/reference/expect#value-matchers) | same |
    term `toBeTruthy()` also in 2: D045#value-matchers, D045#valueexpectation
- **[ONLY HERE]** | `expect(collection).toContain()` | compares items by deep equality, like Playwright's `toContainEqual`, so `toContain({ id: 1 })` passes on `[{ id: 1 }]`. Containment in a string is the same | by design |
- **[ONLY HERE]** | `toStrictEqual()`, `toThrow()`, `toBeInstanceOf()` | `toEqual` on the shape you need | missing |
    term `toEqual` also in 6: D003#api-testing, D045#asymmetric-matchers, D045#asymmetricmatcher, D045#value-matchers, D045#valueexpectation, D050#locator-reads
- **[ONLY HERE]** | `expect.any()`, `objectContaining()`, `arrayContaining()`, `stringMatching()` | the same, plus `anything()` and `stringContaining()`, see [asymmetric matchers](/reference/expect#asymmetric-matchers) | same |
    term `anything()` also in 2: D045#asymmetric-matchers, D045#expectcall-softexpectcall-and-expect
- **[ONLY HERE]** | `expect(async () => { ... }).toPass()` | `expect.poll(read).toBe(...)`; poll an array with `toEqual([a, b])` for several values at once | renamed |
- **[(short, not compared)]** | `expect.poll()` | the same | same |
- **[ONLY HERE]** | `expect.soft()` | the same; kept failures fail the attempt once the body settles, see [soft assertions](/reference/expect#soft-assertions) | same |
- **[ONLY HERE]** | `expect(locator, 'message')` | `expect(locator)`; a locator failure already names the locator, the matcher, and what was observed. Only a value expectation takes a message | by design |
- **[(short, not compared)]** | `expect.extend()` | not yet | missing |
- **[ONLY HERE]** | `expect(promise).resolves`, `.rejects` | `await` first, then `expect(value)` | missing |
    term `expect(value)` also in 5: D007#when-a-recording-is-written, D032#map-each-command, D045#reference-expect, D045#value-matchers, D045#valueexpectation
- **[ONLY HERE]** | `page.goto(path)` | `app.open(path)`; `browser.goto(url, { waitUntil, timeout })` for the browser options | renamed |
    term `app.open(path)` also in 2: D030#map-each-command, D034#map-each-webdriver-call
- **[ONLY HERE]** | `const response = await page.goto()` | `app.open` and `browser.goto` resolve to `void`; take the response from `browser.waitForResponse` | by design |
    term `browser.goto` also in 5: D005#mock-an-api, D016#limits, D033#browser-timeouts-and-artifacts, D051#navigation, D053#the-browser-fixture
    term `browser.waitForResponse` also in 3: D005#mock-an-api, D030#map-each-command, D053#the-browser-fixture
- **[ONLY HERE]** | `page.goBack()` | `app.back()`, or `browser.back()` | renamed |
    term `app.back()` also in 6: D032#map-each-command, D034#map-each-webdriver-call, D039#back, D042#capabilities, D042#session, D060#capabilities
- **[ONLY HERE]** | `page.goForward()`, `page.reload()` | `browser.forward()`, `browser.reload()` | web only |
    term `browser.reload()` also in 3: D034#map-each-webdriver-call, D050#queries, D053#the-browser-fixture
- **[ONLY HERE]** | `page.url()`, `page.title()` | `browser.url()`, `browser.title()` | web only |
    term `browser.title()` also in 1: D053#the-browser-fixture
    term `browser.url()` also in 1: D053#the-browser-fixture
- **[ONLY HERE]** | `page.waitForURL()` | `browser.waitForURL()`, with a string or `RegExp` and `timeout` as the only option. A string is an absolute URL, or a relative one resolved against `app.url`, matched exactly, not a glob: `'**/orders'` never matches, so pass a `RegExp` | web only |
    term `browser.waitForURL()` also in 1: D007#when-a-recording-is-written
- **[ONLY HERE]** | `page.waitForLoadState()` | `browser.goto(url, { waitUntil })` on the navigation itself | missing |
- **[ONLY HERE]** | `page.waitForFunction(fn)` | `expect.poll(() => browser.evaluate(fn)).toBeTruthy()` | missing |
- **[ONLY HERE]** | `page.waitForTimeout(ms)` | a locator assertion on the state you are waiting for: `toBeVisible()` on what appears, `toBeHidden()` on what goes away | by design |
    term `toBeHidden()` also in 6: D030#map-each-command, D031#map-each-detox-call, D032#map-each-command, D045#locator-matchers, D050#queries, D059#resize-inside-a-test
- **[ONLY HERE]** | `page.setViewportSize()` | `browser.setViewport()`, before or after the first navigation | web only |
    term `browser.setViewport()` also in 1: D059#viewports
- **[ONLY HERE]** | `page.viewportSize()` | `browser.evaluate(() => ({ width: innerWidth, height: innerHeight }))` | missing |
- **[ONLY HERE]** | `page.screenshot()` | `app.screenshot(label)`: the viewport, redacted, attached to the report; no `fullPage` | renamed |
    term `fullPage` also in 1: D045#screenshot-matchers
- **[ALSO: D033#port-page-objects]** | a fresh `context` per test | every attempt starts in a fresh context; `app.restart()` recreates it, `app.clearState()` also clears storage | same |
- **[ONLY HERE]** | `page.pause()` | `--headed` to watch, [`e2e mcp`](/mcp) to drive the app from a coding agent | missing |
- **[ONLY HERE]** | `page.route(pattern, handler)` | `browser.route(pattern, handler)`; a string or `RegExp` pattern, no predicate function; the handler decides exactly once | web only |
- **[ALSO: D033#app-targets-and-output, D039#screenshot, D040#commands, D041#e2econfig, D053#options, D053#the-browser-fixture]** | `route.fulfill({ json, body, path, status, headers, contentType })` | the same; one of `json`, `body`, or `path`, and `path` is relative to the project root | web only |
- **[ONLY HERE]** | `route.continue({ url, method, headers, postData })`, `route.fallback()` | the same; a `url` goes through the navigation rule, and `fallback()` takes no overrides | web only |
    term `fallback()` also in 1: D053#the-browser-fixture
- **[ONLY HERE]** | `route.fetch()`, `route.abort(code)`, `route.fallback(overrides)` | none yet; `abort()` takes no error code | missing |
    term `abort()` also in 1: D053#the-browser-fixture
- **[(short, not compared)]** | `page.unroute()` | `browser.unroute()` | web only |
- **[ONLY HERE]** | `page.waitForResponse(pattern)` | `browser.waitForResponse(pattern)`: a string or `RegExp`, no predicate function; `url`, `status`, `headers`, `json()`, `text()`. A string is a glob tested against the whole URL, query included, and never resolved against `app.url`: Playwright's `'/api/orders'` is
    term `'**/api/orders'` also in 2: D005#mock-an-api, D053#the-browser-fixture
    term `json()` also in 9: D003#api-testing, D005#recording-on-the-provider, D005#write-a-provider, D032#map-each-command, D035#hosted-devices, D045#value-matchers, D045#valueexpectation, D048#custom-reporters, D053#the-browser-fixture
    term `text()` also in 3: D053#surfaceof, D053#the-browser-fixture, D057#add-a-tool
- **[ONLY HERE]** | `response.ok()`, `response.body()`, `response.request()` | `status` and `text()` | missing |
    term `text()` also in 3: D053#surfaceof, D053#the-browser-fixture, D057#add-a-tool
- **[ONLY HERE]** | `page.waitForRequest()`, `request.postDataJSON()` | none yet for `waitForRequest`; `route.request.postData` is a string | missing |
- **[ONLY HERE]** | `routeFromHAR()`, `routeWebSocket()` | not yet | missing |
- **[ONLY HERE]** | `page.on('dialog')` | `browser.onDialog('accept')`, or a handler that calls `accept` or `dismiss` | web only |
    term `browser.onDialog('accept')` also in 4: D005#handle-a-dialog, D030#map-each-command, D034#map-each-webdriver-call, D053#the-browser-fixture
- **[ONLY HERE]** | `page.waitForEvent('download')` | `browser.waitForDownload(() => trigger)` | web only |
- **[ONLY HERE]** | `page.waitForEvent('popup')`, `context.on('page')` | a window the app opens is not driven | missing |
- **[ONLY HERE]** | `page.on('console')`, `page.on('pageerror')` | assert on what the page shows | missing |
- **[ONLY HERE]** | `page.evaluate(fn, arg)` | `browser.evaluate(fn, arg)`; JSON in and out, no handles | web only |
- **[ONLY HERE]** | `page.addInitScript(script, arg)`, `context.addInitScript()` | `browser.addInitScript(script, arg)`, or `web({ initScripts })` for every test; pass `{ content }` as a plain string | web only |
    term `web({ initScripts })` also in 1: D053#options
- **[ALSO: D053#browser-interface, D053#options, D053#the-browser-fixture]** | `page.emulateMedia({ colorScheme, reducedMotion })` | `browser.emulateMedia()`, for every open tab and every tab opened after it; `media`, `forcedColors`, and `contrast` are not yet supported | web only |
    term `contrast` also in 1: D041#agents
- **[ONLY HERE]** | `page.exposeFunction()`, `addStyleTag()`, `setExtraHTTPHeaders()`, `clock` | none yet; for `addStyleTag`, `browser.evaluate` can append a `<style>` once the page is open | missing |
    term `<style>` also in 1: D025#fetch-more-of-the-page
    term `browser.evaluate` also in 8: D005#read-from-the-page, D030#map-each-command, D033#what-differs-on-purpose, D034#map-each-webdriver-call, D044#runner-codes, D053#options, D053#the-browser-fixture, D059#scoping-a-test-to-one-size
- **[ONLY HERE]** | `context.addCookies()`, `context.cookies()` | `browser.setCookies()`, `browser.cookies()` | web only |
    term `browser.cookies()` also in 2: D003#signed-in-requests, D053#the-browser-fixture
- **[ONLY HERE]** | `context.clearCookies()` | `app.clearState()` also clears other persisted state and recreates the context | missing |
- **[ALSO: D032#map-each-command]** | `request` fixture | Node `fetch`, see [API](/api-testing) | by design |
- **[ALSO: D033#browser-timeouts-and-artifacts]** | `context.storageState({ path })` | no file, see [What differs on purpose](#what-differs-on-purpose) | by design |
- **[ALSO: D033#rewrite-one-spec]** | `import { test, expect } from '@playwright/test'` | `import { test } from '@e2e-dev/web'` and `import { expect } from 'e2e'` | renamed |
    term `import { test } from '@e2e-dev/web'` also in 9: D004#several-signed-in-users, D004#sign-in-once-in-a-setup-test, D005#browser, D033#rewrite-one-spec, D034#rewrite-one-flow, D037#add-an-agent-step, D037#run-your-first-test, D053#reference-web, D059#resize-inside-a-test
    term `import { test, expect } from '@playwright/test'` also in 1: D033#rewrite-one-spec
- **[ONLY HERE]** | `test(title, fn)`, `test.describe`, `beforeEach`, `afterEach` | the same; `describe` and the hooks are also top-level imports | same |
    term `test.describe` also in 1: D052#members
- **[ONLY HERE]** | `test.beforeAll`, `afterAll` | the same, with `platform` as the only fixture; no `browser` or `request` | same |
    term `afterAll` also in 10: D020#rerunning-the-failed-tests, D040#commands, D044#runner-codes, D045#polling-a-value, D047#exported-types, D048#custom-reporters, D052#function-types, D052#hooks, D052#testapi, D053#types
- **[ALSO: D033#browser-timeouts-and-artifacts]** | `{ page }` in a test | `{ screen, app, browser }`; no raw `Page` in tests, see [What differs on purpose](#what-differs-on-purpose) | by design |
    term `Page` also in 8: D018#driving-the-page-yourself, D025#what-does-not-work, D033#port-page-objects, D033#what-differs-on-purpose, D034#map-each-webdriver-call, D042#actions, D045#screenshot-matchers, D053#surfaceof
    term `{ page }` also in 1: D033#rewrite-one-spec
- **[ONLY HERE]** | `test.skip(title, fn)`, `test.skip(condition, reason)` | the same | same |
    term `test.skip(condition, reason)` also in 2: D014#organize-tests, D052#members
- **[ONLY HERE]** | `test.only` | the same; CI rejects it with `ONLY_IN_CI` | same |
    term `ONLY_IN_CI` also in 7: D008#what-ci-changes, D041#ci, D043#run-mode, D044#runner-codes, D052#members, D052#options, D052#testoptions
    term `test.only` also in 2: D041#ci, D052#members
- **[ONLY HERE]** | `test.describe.only` | `test.only` on each member | missing |
    term `test.only` also in 2: D041#ci, D052#members
- **[ONLY HERE]** | `test.describe.skip` | `test.describe(title, { skip: true }, fn)` | renamed |
- **[ALSO: D052#options, D052#testoptions]** | `test.describe.serial`, `describe.configure({ mode: 'serial' })` | `test.describe(title, { serial: true }, fn)`: one retry unit with shared app state | renamed |
- **[ALSO: D033#app-targets-and-output]** | `describe.configure({ mode: 'parallel' })` | a file's tests run in order on one worker | missing |
- **[ONLY HERE]** | `describe.configure({ retries, timeout })` | `{ retries, timeout }` on the group | renamed |
- **[ONLY HERE]** | `test.setTimeout(ms)`, `test.slow()` | `test(title, { timeout }, fn)` | renamed |
- **[ONLY HERE]** | `test.fixme()`, `test.fail()` | `{ skip: 'reason' }` | missing |
- **[ONLY HERE]** | `test.step(title, fn)` | every `screen`, `browser`, and `agent` call is already a named step in the report, with its arguments redacted | missing |
- **[ONLY HERE]** | `test.info()`, `attach()`, `annotations` | `app.screenshot(label)` attaches a screenshot | missing |
    term `annotations` also in 2: D041#agentconfig, D057#declare-what-a-tool-does
- **[ALSO: D002#pin-an-agent-in-the-suite, D032#port-the-config]** | `{ tag: '@smoke' }` | `{ tags: ['smoke'] }` on a test or group | renamed |
- **[ONLY HERE]** | `test.use({ ... })` | per target in the config; `browser.setViewport` at runtime | renamed |
    term `browser.setViewport` also in 8: D025#what-does-not-work, D030#map-each-command, D053#options, D053#the-browser-fixture, D053#weboptions, D059#fill-the-window, D059#resize-inside-a-test, D059#viewports
- **[ALSO: D033#port-page-objects, D052#fixturedefinitions, D052#fixtures]** | `test.extend({ fixture })` | the same shape; a fixture that needs another goes in a chained `extend`. Not yet on demand: every fixture of the chain sets up for every test on that `test`, named or not. Give each setup its own `test` | missing |
- **[ONLY HERE]** | `{ scope: 'worker' }` fixtures, option fixtures | `beforeAll` for per-file setup | missing |
    term `{ scope: 'worker' }` also in 1: D049#playwright-test-fixtures
- **[ONLY HERE]** | `npx playwright test` | `npx e2e run` | renamed |
- **[ONLY HERE]** | `npx playwright test tests/login.spec.ts` | `npx e2e run tests/login.e2e.ts`; a directory, a bare name, or a glob also selects | same |
    term `npx e2e run tests/login.e2e.ts` also in 1: D040#commands
- **[ONLY HERE]** | `--project web` | `--target web` | renamed |
    term `--target web` also in 2: D014#run-one-test, D040#commands
- **[ALSO: D040#commands]** | `-g`, `--grep`, `--grep-invert` | `--grep` and `--grep-invert`, no `-g`; matched against the describe titles and the test title joined by spaces; tags are `--tag` and `--exclude-tag` | renamed |
    term `--exclude-tag` also in 4: D006#repro-tests, D032#port-the-config, D040#commands, D049#functions
    term `--grep` also in 5: D014#run-one-test, D040#commands, D041#output, D049#functions, D051#redaction
    term `--grep-invert` also in 1: D040#commands
    term `--tag` also in 7: D022#watch-a-run, D032#port-the-config, D040#commands, D049#functions, D052#options, D052#testoptions, D056#what-is-sent
- **[ONLY HERE]** | `tests/login.spec.ts:12` | `tests/login.e2e.ts:12`, the test whose `test(` call opens on that line | same |
- **[ALSO: D040#commands]** | `--debug` | `--headed` to watch. `e2e run --debug` prints phase timings and the agent step table, not an inspector | missing |
    term `--debug` also in 9: D001#what-a-step-costs, D002#make-the-agent-yours, D015#agent-steps, D015#artifacts, D018#what-the-context-holds, D030#map-each-command, D040#commands, D043#diagnostics, D044#agenterror
    term `e2e run --debug` also in 2: D015#agent-steps, D040#commands
- **[ONLY HERE]** | `--ui` | `--watch` reruns on save with vitest's keys, `--headed` to watch, `e2e mcp` to drive the app from a coding agent | missing |
    term `--watch` also in 2: D040#commands, D056#what-is-sent
- **[ONLY HERE]** | `--headed`, `--retries`, `--workers`, `--config`, `--pass-with-no-tests` | the same | same |
    term `--config` also in 8: D012#ios-and-android, D040#commands, D041#finding-the-config-file, D044#runner-codes, D046#flags, D046#setup, D046#tools, D059#scoping-a-test-to-one-size
    term `--pass-with-no-tests` also in 3: D008#sharding, D040#commands, D044#runner-codes
    term `--retries` also in 2: D008#what-ci-changes, D040#commands
    term `--workers` also in 2: D008#what-ci-changes, D040#commands
- **[ONLY HERE]** | `--reporter` | the same flag; the ids are `list`, `json`, `junit`, `markdown` | same |
- **[ONLY HERE]** | `--output` | `--output`, the results directory; each test's trace page and artifacts are in its `results/` | same |
    term `--output` also in 6: D006#what-the-agent-does, D012#ios-and-android, D032#port-the-config, D040#commands, D041#output, D051#artifacts
- **[ONLY HERE]** | `--trace <mode>` | `--trace [mode]`, the same modes; a bare `--trace` is `on` | same |
    term `--trace` also in 6: D015#traces, D033#browser-timeouts-and-artifacts, D040#commands, D041#recording, D052#options, D052#testoptions
    term `--trace [mode]` also in 3: D033#browser-timeouts-and-artifacts, D040#commands, D041#recording
- **[ONLY HERE]** | `--last-failed`, `--shard`, `--repeat-each`, `--max-failures` | the same names; `--shard` keeps serial groups together | same |
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D040#commands, D041#output, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
    term `--max-failures` also in 5: D008#gate-pull-requests, D020#rerunning-the-failed-tests, D033#app-targets-and-output, D040#commands, D044#runner-codes
    term `--repeat-each` also in 1: D040#commands
    term `--shard` also in 4: D008#sharding, D032#port-the-config, D040#commands, D049#functions
- **[(short, not compared)]** | `--quiet` | not yet | missing |
- **[ONLY HERE]** | `-u`, `--update-snapshots` | the same; rewrites the stored screenshots that differ | same |
    term `--update-snapshots` also in 5: D040#commands, D045#screenshot-matchers, D058#in-ci, D058#stored-screenshots, D058#when-it-fails
- **[ONLY HERE]** | `--list` | `npx e2e list`, with the same selection flags | renamed |
    term `npx e2e list` also in 2: D040#commands, D059#one-size-per-target
- **[ONLY HERE]** | `npx playwright codegen` | `npx e2e explore` walks the app from a goal and reports what it found; `npx e2e mcp` lets a coding agent drive the app while it writes the test, see [MCP server](/mcp) | renamed |
    term `npx e2e explore` also in 3: D019#start-an-exploration, D019#start-signed-in, D040#commands
    term `npx e2e mcp` also in 5: D029#set-it-up, D032#port-the-config, D040#commands, D046#flags, D046#setup
- **[ONLY HERE]** | `npx playwright show-trace` | no viewer; open the `trace.md` under `.e2e/results/` that the terminal names | by design |
    term `.e2e/results/` also in 9: D010#workflow, D013#how-an-agent-reads-a-failure, D015#artifacts, D015#read-the-failure, D032#port-the-config, D033#browser-timeouts-and-artifacts, D040#commands, D041#recording, D058#when-it-fails
- **[ONLY HERE]** | `npx playwright show-report` | `.e2e/summary.md` from the `markdown` reporter | missing |
    term `.e2e/summary.md` also in 5: D015#debugging, D020#the-comment, D032#port-the-config, D033#app-targets-and-output, D040#commands
- **[ONLY HERE]** | `npx playwright install` | `npx @e2e-dev/web install`, for the Playwright version the engine pins; a run also installs a missing browser on its own | renamed |
    term `npx @e2e-dev/web install` also in 2: D005#pick-a-browser, D053#installing-browsers

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D005#run-a-script-before-the-page: Both name web({ initScripts }) and browser.addInitScript as the way to run a script before page scripts.
- D015#watch-it-happen: Both say --headed shows a visible browser to watch the run.
- D015#agent-steps: Both say e2e run --debug prints phase timings and the agent step table.
- D030#map-each-command: Both map framework commands to e2e equivalents such as browser.setCookies, browser.onDialog, browser.setViewport, browser.evaluate, doubleTap and secondaryTap.
- D032#map-each-command: Both map framework calls to e2e equivalents, including screenshots, expect.poll, test.extend, hooks, video and the rule that screen, app, agent and expect run on every target.
- D032#rewrite-selectors: Both state that string names in getByRole, getByText and similar are exact case-sensitive matches and that { visible: true } drops hidden twins.
- D033#browser-timeouts-and-artifacts: Both map Playwright storageState, cookies, show-trace trace.md and emulateMedia (colorScheme, reducedMotion) to e2e equivalents.
- D003#api-testing: Both say the Playwright request fixture is replaced by Node fetch for API tests.
- D005#mock-an-api: Both cover browser.route with fulfill and continue, and browser.waitForResponse.
- D005#handle-a-dialog: Both map page dialog handling to browser.onDialog.
- D005#download-a-file: Both map download waiting to browser.waitForDownload.
- D005#reach-into-an-iframe: Both map frameLocator to browser.frameLocator.
- D005#run-a-script-before-the-page: Both map addInitScript to browser.addInitScript.
- D005#emulate-dark-mode-and-reduced-motion: Both map emulateMedia colorScheme and reducedMotion to browser.emulateMedia.
- D005#cookies: Both map context cookies to browser.setCookies and browser.cookies.
- D008#sharding: Both describe --shard index/total running one slice of the suite.
- D015#traces: Both say there is no trace viewer and the trace is the markdown trace.md page.
- D019#explore: Both describe npx e2e explore as the exploration command that replaces codegen.
- D030#map-each-command: Both map click/dblclick/rightclick, select, setInputFiles, route, waitForResponse, onDialog and setCookies calls to e2e equivalents.
- D031#map-each-detox-call: Both map screenshots, toHaveScreenshot, visibility waits and actions to e2e equivalents.
- D032#map-each-command: Both map screenshots, expect.poll, test.extend, hooks, app.back and retries to e2e equivalents.
- D033#app-targets-and-output: Both map Playwright report output (html reporter) to the markdown reporter's summary.md.
- D033#browser-timeouts-and-artifacts: Both map Playwright timeouts, trace, video, cookies, storage state and emulation options to e2e equivalents.
- D033#port-page-objects: Both say Playwright page objects and fixtures map to test.extend fixtures.
- D033#what-differs-on-purpose: Both explain exact case-sensitive string queries, rendered text reads, LOCATOR_AMBIGUOUS, checked-state behaviour and no raw Page in tests.
- D033#defaults-that-differ: Both state the e2e CLI and trace defaults (retries, workers, trace mode) compared with Playwright.
- D034#map-each-webdriver-call: Both map back navigation, frames, dialogs, cookies, text reads and page objects to e2e equivalents.
- D038#action-tools: Both cover agent action tools for select, upload, right click, dragTo and scroll that map to locator actions.
- D040#commands: Both list the CLI flags --grep, --grep-invert, --tag, --exclude-tag, --shard, --last-failed, --repeat-each, --max-failures, --update-snapshots, --trace and e2e list.
- D041#recording: Both describe trace and video modes and the trace.md page.
- D041#ci: Both state test.only is rejected with ONLY_IN_CI in CI runs.
- D042#actions: Both list engine action kinds such as selectOption, setInputFiles, secondaryTap, dragTo and modifiers.
- D044#runner-codes: Both name ONLY_IN_CI as the error for a focused test in a CI run.
- D045#locator-matchers: Both list locator matchers toBeVisible, toBeEnabled, toBeChecked, toHaveText, toHaveCount, toBeAttached and toBeSelected.
- D045#screenshot-matchers: Both cover toHaveScreenshot with threshold, maxDiffPixels, maxDiffPixelRatio, mask options and the always-viewport behaviour.
- D045#value-matchers: Both cover value matchers, toContain deep equality and the missing toStrictEqual, toThrow and expect.extend.
- D045#asymmetric-matchers: Both list asymmetric matchers expect.any, objectContaining, arrayContaining, stringMatching, stringContaining and anything.
- D045#soft-assertions: Both state expect.soft failures fail the attempt once the body settles.
- D045#polling-a-value: Both give expect.poll as the way to re-read a value until a matcher passes.
- D045#text-matching: Both state toHaveText and toContainText compare rendered text and support ignoreCase.
- D047#engine: Both list device capability notes: dragTo, scrollIntoView, setInputFiles, selectOption and secondaryTap support.
- D048#built-in-reporters: Both list the reporter ids list, json, junit and markdown, with markdown writing summary.md.
- D049#functions: Both describe CLI selection filters such as grep, tags and the shard index/total slice.
- D050#queries: Both describe getByRole, getByLabel, getByText, getByTestId, getByPlaceholder exact string matching and visible: true.
- D050#screen-actions: Both describe screen.tapAt, screen.swipe({ from, to }) and scrollIntoView-style screen actions.
- D050#locator-actions: Both describe locator actions tap, doubleTap, secondaryTap, fill, pressSequentially, press, check, selectOption, setInputFiles and tap position or modifiers.
- D050#locator-reads: Both describe locator reads textContent, inputValue, getAttribute, isVisible, isChecked, boundingBox and allTextContents.
- D050#match-rules: Both state a single-node operation or positive matcher on several matches fails with LOCATOR_AMBIGUOUS.
- D052#members: Both list test members test.describe, test.only, test.skip, test.extend and beforeEach, with CI rejecting test.only.
- D052#hooks: Both cover the beforeEach, afterEach, beforeAll and afterAll hooks.
- D052#options: Both cover per-test options (tags, serial, timeout, skip, trace) and ONLY_IN_CI for only.
- D052#fixtures: Both cover test.extend fixtures and the declared requires for missing fixtures.
- D053#options: Both cover browser.addInitScript, web({ initScripts }), emulateMedia, setViewport and related web options.
- D053#the-browser-fixture: Both list the browser fixture methods: back, forward, url, title, waitForURL, locator, frameLocator, evaluate, waitForResponse, waitForDownload, route, onDialog, addInitScript, keyboard, mouse.
- D053#installing-browsers: Both give npx @e2e-dev/web install to install browsers.
- D053#browser-interface: Both list browser methods such as locator, frameLocator, evaluate, waitForResponse, waitForDownload, onDialog and addInitScript.
- D058#stored-screenshots: Both describe --update-snapshots rewriting stored screenshots.
- D033#what-differs-on-purpose: Both state string names are exact case-sensitive, text reads are rendered text, checked state defaults, LOCATOR_AMBIGUOUS, JSON-only evaluate and no raw Page.
- D039#restart: Both say app.restart() recreates the context.
- D039#clearstate: Both say app.clearState() clears storage and other persisted state and recreates the context.
- D040#commands: Both list CLI flags --grep, --tag, --shard, --last-failed, --repeat-each, --max-failures, --update-snapshots, --trace, --reporter and e2e list, explore, mcp.
- D041#output: Both map Playwright outputDir/--output to the results directory holding each test's trace page.
- D045#locator-matchers: Both state the Playwright matchers map the same, toBeChecked passing negated on non-checkable nodes, and toHaveText/toContainText list semantics.
- D045#screenshot-matchers: Both map toHaveScreenshot options (maxDiffPixels, threshold, maskColor, mask) and unsupported fullPage.
- D050#refinement: Both say filter takes hasText and has, hasNot and hasNotText are not supported (INVALID_LOCATOR), and first, last, nth exist.
- D050#locator-actions: Both say Playwright trial, force and noWaitAfter options are rejected as INVALID_ARGUMENT, and describe fill, pressSequentially and secondaryTap.
- D050#types: Both say a role query never matches hidden nodes and visible: true drops hidden twins on other queries.
- D052#hooks: Both say beforeAll and afterAll have platform as the only fixture.
- D052#fixtures: Both say a fixture needing another goes in a chained extend and every fixture of the chain sets up for every test.
- D053#the-browser-fixture: Both map page.route, waitForResponse, onDialog, waitForDownload, evaluate, cookies and setViewport to the browser fixture.
- D053#browser-interface: Both map Playwright page/context calls to browser.route, onDialog, waitForDownload, keyboard, mouse, evaluate and setViewport.
- D058#stored-screenshots: Both map Playwright toHaveScreenshot update-snapshots behaviour and the -snapshots storage directory.

## S19 · detail · D033#what-differs-on-purpose  (From Playwright › What differs on purpose; page title: From Playwright)

Regel: genau ein Abschnitt, ein einzelnes Faktum, Referenzantwort höchstens 30 Wörter; das Faktum muss nur hier stehen.

**Typ-Eignung:** Trägt `conceptual`: „`browser.evaluate` takes and returns JSON only, so the report can record and redact the result.“ (Grund, ein Satz, „JSON only“ nur hier). `comparative` wäre naheliegend, aber jede geprüfte Gegenüberstellung hat ihre e2e-Hälfte auch woanders: `isChecked()` in D050#locator-reads, exakte Namen in D050#queries und D032#rewrite-selectors, `LOCATOR_AMBIGUOUS` in vielen Abschnitten, Sitzungen „encrypted, deleted at cleanup“ in D051#artifacts. Für `detail` (ein Abschnitt) bricht das die Klassenregel.

- **[ONLY HERE]** ## What differs on purpose - A string name is exact.
- **[ONLY HERE]** Playwright's `getByRole` names, `getByLabel`, `getByPlaceholder`, and `getByText` match a case-insensitive substring, so `Save` also hits `Save as draft`.
    term `getByPlaceholder` also in 3: D005#shadow-dom, D033#map-each-api, D050#queries
- **[ALSO: D050#queries]** In e2e a string matches the whole text, case-sensitive.
- **[ONLY HERE]** Pass `{ exact: false }` or a `RegExp` for a fragment.
    term `{ exact: false }` also in 4: D030#map-each-command, D030#migrate-cypress, D032#rewrite-selectors, D050#queries
- **[ONLY HERE]** A query that misses passes a negated assertion, so check it with a positive one first.
- **[(short, not compared)]** See [queries](/reference/screen#queries).
- **[ONLY HERE]** - Text reads are rendered text.
- **[ONLY HERE]** On the web, `textContent()` and `toHaveText` read what `innerText` returns, like Playwright's `{ useInnerText: true }`.
    term `innerText` also in 3: D033#map-each-api, D045#text-matching, D050#locator-reads
- **[ONLY HERE]** Playwright reads the DOM's `textContent` by default.
- **[ONLY HERE]** Queries still match the source text:
- **[ONLY HERE]** `getByText('Draft')` finds the tag below, `getByText('DRAFT')` does not.
- **[ONLY HERE]** `browser.evaluate` reads the raw DOM text.
    term `browser.evaluate` also in 8: D005#read-from-the-page, D030#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D044#runner-codes, D053#options, D053#the-browser-fixture, D059#scoping-a-test-to-one-size
- **[ONLY HERE]** See [locator reads](/reference/screen#locator-reads).
- **[ALSO: D050#locator-reads]** - A node with no checked state is unchecked.
- **[ALSO: D045#locator-matchers]** `isChecked()` is `false` and `.not.toBeChecked()` passes on a button or a heading, where Playwright throws.
    term `.not.toBeChecked()` also in 2: D033#map-each-api, D045#locator-matchers
    term `isChecked()` also in 2: D033#map-each-api, D050#locator-reads
- **[ONLY HERE]** Query a checkable control by role, so the query fails when the control changes kind.
- **[ONLY HERE]** - `check()` and `uncheck()` read the state back until the action timeout, so a controlled checkbox that updates late passes.
    term `check()` also in 5: D030#map-each-command, D033#map-each-api, D050#locator-actions, D050#locator-reads, D050#refinement
    term `uncheck()` also in 2: D033#map-each-api, D050#locator-actions
- **[ONLY HERE]** A click that removes the control passes too, where Playwright fails.
- **[ONLY HERE]** Assert on what replaced it.
- **[ONLY HERE]** - One match or `LOCATOR_AMBIGUOUS`, `isVisible()` included, where Playwright reads the first match silently.
    term `isVisible()` also in 8: D032#map-each-command, D032#rewrite-selectors, D033#map-each-api, D034#map-each-webdriver-call, D035#troubleshooting, D050#locator-reads, D050#match-rules, D050#queries
- **[ALSO: D015#common-errors]** Narrow with `filter`, `first()`, or `{ visible: true }`, or add a `>> visible=true` step to a `browser.locator` selector.
    term `browser.locator` also in 10: D005#icon-fonts-and-generated-content, D005#reach-into-an-iframe, D005#shadow-dom, D030#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D037#run-your-first-test, D045#browser-matchers, D050#queries, D053#the-browser-fixture
    term `first()` also in 9: D014#locators, D015#common-errors, D030#map-each-command, D031#map-each-detox-call, D032#rewrite-selectors, D033#map-each-api, D034#map-each-webdriver-call, D050#queries, D050#refinement
    term `{ visible: true }` also in 6: D005#reach-into-an-iframe, D015#common-errors, D032#rewrite-selectors, D033#map-each-api, D042#queries, D050#queries
- **[ONLY HERE]** - `browser.evaluate` takes and returns JSON only, so the report can record and redact the result.
    term `browser.evaluate` also in 8: D005#read-from-the-page, D030#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D044#runner-codes, D053#options, D053#the-browser-fixture, D059#scoping-a-test-to-one-size
- **[ONLY HERE]** Pass values in through `arg`.
- **[ONLY HERE]** - A password is a `Secret` with no string value, and the model never sees it.
- **[(short, not compared)]** See [Signing in](/authentication).
- **[(short, not compared)]** - Sessions are per run.
- **[ONLY HERE]** `test.setup` saves state under a name, one time per run and target, and `{ session }` restores it.
    term `{ session }` also in 7: D030#map-each-command, D031#map-each-detox-call, D032#what-differs-on-purpose, D033#browser-timeouts-and-artifacts, D034#port-the-config, D040#commands, D052#options
- **[ONLY HERE]** The file is encrypted and deleted at cleanup, so there is no `.auth/user.json` to reuse across runs.
- **[ONLY HERE]** - No raw `Page` in tests.
    term `Page` also in 8: D018#driving-the-page-yourself, D025#what-does-not-work, D033#map-each-api, D033#port-page-objects, D034#map-each-webdriver-call, D042#actions, D045#screenshot-matchers, D053#surfaceof
- **[ONLY HERE]** Nothing on a raw page is recorded, redacted, or masked.
- **[ONLY HERE]** `surfaceOf(engine)` is for [custom executors](/executors#driving-the-page-yourself), not test code.
    term `surfaceOf(engine)` also in 3: D018#driving-the-page-yourself, D053#options, D053#surfaceof

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D004#session-rules: Both say sessions last one run and the session file is encrypted and deleted at cleanup.
- D030#map-each-command: Both say actions and reads need exactly one match, otherwise LOCATOR_AMBIGUOUS.
- D032#rewrite-selectors: Both say string queries match the whole text case-sensitively, with { exact: false } or a RegExp for fragments, and that several matches give LOCATOR_AMBIGUOUS including isVisible().
- D033#browser-timeouts-and-artifacts: Both say sessions replace storageState and are per run with no file.
- D033#map-each-api: Both explain exact case-sensitive string queries, rendered text reads, LOCATOR_AMBIGUOUS, checked-state behaviour and no raw Page in tests.
- D004#sign-in-once-in-a-setup-test: Both describe test.setup saving a session that a test restores with the session option.
- D004#session-rules: Both describe test.setup sessions saved by name and restored via the session option.
- D004#the-password-is-a-handle: Both state a password is a Secret with no string value that the model never sees.
- D018#driving-the-page-yourself: Both mention surfaceOf(engine) giving the raw Page for custom executors rather than test code.
- D030#map-each-command: Both say several matches fail with LOCATOR_AMBIGUOUS and are narrowed with filter(), first() or nth().
- D031#map-each-detox-call: Both say several matches fail with LOCATOR_AMBIGUOUS and are narrowed with filter(), first() or nth().
- D032#rewrite-selectors: Both state string queries match the whole text in whole case, with { exact: false } or a RegExp for fragments, and LOCATOR_AMBIGUOUS for several matches.
- D033#browser-timeouts-and-artifacts: Both say sessions replace storageState and are saved without a file.
- D033#map-each-api: Both state string names are exact case-sensitive, text reads are rendered text, checked state defaults, LOCATOR_AMBIGUOUS, JSON-only evaluate and no raw Page.
- D034#map-each-webdriver-call: Both say first-match lookups become LOCATOR_AMBIGUOUS in e2e and are narrowed with filter(), first() or nth().
- D041#output: Both state encrypted sessions are deleted when the run ends.
- D045#locator-matchers: Both state .not.toBeChecked() passes on a node with no checked state such as a button or heading.
- D045#text-matching: Both state toHaveText compares rendered text (innerText on the web).
- D050#queries: Both state a string query matches the whole text case-sensitively and { exact: false } or a RegExp matches fragments.
- D050#locator-reads: Both state textContent() on the web reads rendered text like innerText rather than the DOM textContent.
- D050#match-rules: Both state a single-node operation, isVisible() included, fails with LOCATOR_AMBIGUOUS on several matches.
- D051#sessions: Both state a saved session is encrypted state restored by the test.
- D053#the-browser-fixture: Both state browser.evaluate takes and returns JSON values only, with arg passing values in.
- D053#surfaceof: Both mention surfaceOf(engine) as the way to reach the raw Page.
- D045#locator-matchers: Both state .not.toBeChecked() passes on a button or heading and text matchers compare rendered text.
- D050#refinement: Both say a locator with several matches must be narrowed with filter, first or nth.
- D051#sessions: Both say the saved session file is encrypted and deleted at cleanup, with no reusable auth file.

## S20 · multi-section · D032#map-each-command  (From Maestro › Map each command; page title: From Maestro)

Regel: mindestens zwei Abschnitte, jeder liefert einen nötigen Teil; enthaltene oder umschließende Abschnitte zählen nicht als zweiter; H1 nur mit Grund in `notes`.

**Typ-Eignung:** Trägt `comparative` (Maestro gegen e2e, zwei benannte Dinge; in `multi-section` gibt es keine Wortsperre). Naheliegender zweiter Abschnitt: D032#rewrite-selectors („Four differences from Maestro's selectors“, z. B. „Maestro taps the first of several matches. e2e fails with `LOCATOR_AMBIGUOUS`“, nur dort), gleiche Seite, aber nicht verschachtelt. Vorsicht: die Bedeutung von „Not yet“/„No equivalent“ steht auch in D032#migrate-maestro (H1, nur mit Grund in `notes`).

- **[ALSO: D033#map-each-api]** ## Map each command Calls on `device` run only on a device, so a test that uses it declares `requires: ['device']` and other targets skip it.
    term `requires: ['device']` also in 1: D047#reference-mobile
- **[ALSO: D033#map-each-api]** Calls on `screen`, `app`, `agent`, and `expect(locator)` run on every target. "Not yet" marks a command e2e doesn't have today, and "No equivalent" one it leaves out on purpose.
- **[ONLY HERE]** **App lifecycle** **Taps and input** **Gestures** **Assertions and waits** **Device** **AI commands and flow control**
- **[ALSO: D031#rewrite-one-spec, D047#engine]** | `launchApp` | `app.open()`, the fresh launch of the target's `app.bundleId`; nothing launches on its own |
    term `launchApp` also in 4: D031#map-each-detox-call, D031#port-the-config, D031#rewrite-one-spec, D032#rewrite-one-flow
- **[ONLY HERE]** | `launchApp: { clearState: true }`, `clearState` | `app.clearState()` |
- **[ONLY HERE]** | `launchApp: { stopApp: false }` | `device.openApp(id)` without `relaunch` |
    term `device.openApp(id)` also in 1: D032#port-the-config
    term `relaunch` also in 9: D031#port-the-config, D035#launch-arguments-and-permissions, D042#session, D047#agent-tools, D047#device, D047#device-fixture, D047#engine, D060#capabilities, D060#the-shape-of-an-engine
- **[ALSO: D031#port-the-config, D047#engine]** | `launchApp: { arguments }` | `app.launchArguments` on the target, or `device.openApp(app, { relaunch: true, launchArguments })` for one launch; a list of strings, not a map |
    term `app.launchArguments` also in 5: D031#port-the-config, D035#launch-arguments-and-permissions, D035#physical-devices, D047#device-fixture, D047#engine
    term `device.openApp(app, { relaunch: true, launchArguments })` also in 1: D031#port-the-config
- **[ALSO: D031#port-the-config]** | `launchApp: { permissions }` | `app.permissions` on the target, set before every fresh launch, or `device.openApp(app, { relaunch: true, permissions })` for one; `grant`, `deny`, `reset` for `allow`, `deny`, `unset`; no `all`, nothing is granted unless named |
    term `app.permissions` also in 5: D031#port-the-config, D035#launch-arguments-and-permissions, D035#physical-devices, D047#device-fixture, D047#engine
    term `deny` also in 8: D031#port-the-config, D035#launch-arguments-and-permissions, D041#the-app-under-test, D042#app, D047#device, D047#device-fixture, D047#engine, D047#engine-options
    term `device.openApp(app, { relaunch: true, permissions })` also in 1: D031#port-the-config
- **[(short, not compared)]** | `stopApp`, then `launchApp` | `app.restart()` |
    term `launchApp` also in 4: D031#map-each-detox-call, D031#port-the-config, D031#rewrite-one-spec, D032#rewrite-one-flow
- **[ONLY HERE]** | `clearKeychain` | `device.clearKeychain()`, the whole simulator's keychain; iOS only |
    term `clearKeychain` also in 3: D035#physical-devices, D035#the-device-fixture, D047#device
    term `device.clearKeychain()` also in 2: D035#the-device-fixture, D047#device
- **[ALSO: D047#device]** | `openLink` | `device.openLink(url, { app })`; on iOS the link opens into `app`, default the pinned app |
    term `openLink` also in 9: D035#expo-development-builds, D035#physical-devices, D035#the-device-fixture, D035#what-differs-from-the-web, D041#the-app-under-test, D047#device, D047#engine, D047#replay-cache-on-a-device, D051#navigation
- **[(short, not compared)]** | `back` | `app.back()`, or `device.back()` |
    term `app.back()` also in 6: D033#map-each-api, D034#map-each-webdriver-call, D039#back, D042#capabilities, D042#session, D060#capabilities
    term `device.back()` also in 2: D031#map-each-detox-call, D047#device
- **[ONLY HERE]** | `tapOn: "Text"` | `screen.getByText('Text').tap()`; exact, see [Rewrite selectors](#rewrite-selectors) |
- **[ONLY HERE]** | `tapOn: { id: x }` | `screen.getByTestId('x').tap()` |
- **[ONLY HERE]** | `tapOn: { text, index: 2 }` | `.nth(2)` |
    term `.nth(2)` also in 1: D050#refinement
- **[ONLY HERE]** | `tapOn: { below: "Email" }`, `above`, `leftOf`, `rightOf`, `containsDescendants` | No equivalent, see [Rewrite selectors](#rewrite-selectors) |
    term `containsDescendants` also in 1: D032#rewrite-selectors
    term `leftOf` also in 1: D032#rewrite-selectors
    term `rightOf` also in 1: D032#rewrite-selectors
- **[ALSO: D033#map-each-api]** | `tapOn: { point: "x,y" }` | `screen.tapAt({ x, y })`; inside a node, `.tap({ position: { x, y } })` |
    term `.tap({ position: { x, y } })` also in 1: D031#map-each-detox-call
    term `screen.tapAt({ x, y })` also in 1: D033#map-each-api
- **[ONLY HERE]** | `retryTapIfNoChange`, `waitToSettleTimeoutMs` | `mobile({ settle, transition })`, engine-wide; no per-call knob |
- **[ONLY HERE]** | `doubleTapOn`, `longPressOn` | `.doubleTap()`, `.longPress({ duration })` |
    term `.doubleTap()` also in 3: D030#map-each-command, D031#map-each-detox-call, D050#locator-actions
- **[ONLY HERE]** | `inputText` | `screen.getByTestId('field').fill('text')` |
    term `inputText` also in 1: D032#rewrite-one-flow
- **[ONLY HERE]** | `inputRandomEmail`, `inputRandomText`, `faker` | `unique()` around a value in `act` params so the cache still replays; any npm faker for the rest |
    term `unique()` also in 5: D007#what-must-match, D014#goals, D038#agent-act, D038#types, D038#unique
- **[ONLY HERE]** | `pressKey: Enter` | `.press('Enter')` on the field |
    term `.press('Enter')` also in 5: D026#check-app-compatibility, D030#map-each-command, D031#map-each-detox-call, D034#map-each-webdriver-call, D050#locator-actions
- **[ONLY HERE]** | `pressKey: Home`, `back` | `device.home()`, `device.back()` |
    term `device.back()` also in 2: D031#map-each-detox-call, D047#device
    term `device.home()` also in 3: D031#map-each-detox-call, D035#known-device-limitations, D047#device
- **[ONLY HERE]** | `pressKey: lock`, `power`, `volume up`, TV remote keys | Not yet |
    term `power` also in 1: D043#credentials-and-secrets
- **[ONLY HERE]** | `copyTextFrom`, `pasteText` | `await locator.textContent()`, then `.fill(text)` |
    term `await locator.textContent()` also in 1: D030#map-each-command
- **[ONLY HERE]** | `setClipboard` | `device.setClipboard(text)`; `device.clipboard()` reads it |
    term `device.clipboard()` also in 1: D047#device
    term `setClipboard` also in 2: D035#physical-devices, D047#device
- **[ONLY HERE]** | `label: "..."` on a command | Not yet. Every `screen`, `device`, and `agent` call is a report step named by the call |
- **[ALSO: D031#map-each-detox-call]** | `swipe: { direction: UP }` | `screen.swipe({ direction: 'down' })`, or `locator.swipe(...)` inside one node; Maestro names the finger's direction, e2e the content's |
    term `screen.swipe({ direction: 'down' })` also in 1: D031#map-each-detox-call
- **[ONLY HERE]** | `swipe: { start, end }` | `screen.swipe({ from: { x, y }, to: { x, y } })` |
- **[(short, not compared)]** | `scroll` | `screen.swipe({ direction: 'down' })` |
    term `screen.swipe({ direction: 'down' })` also in 1: D031#map-each-detox-call
- **[ONLY HERE]** | `scrollUntilVisible: { element }` | `screen.scrollUntilVisible(locator, { direction })` |
- **[ONLY HERE]** | `waitForAnimationToEnd` | an assertion on the settled state; `mobile({ settle, transition })` for the engine |
- **[ONLY HERE]** | `assertVisible`, `assertNotVisible` | `await expect(locator).toBeVisible()`, `.toBeHidden()` |
    term `.toBeHidden()` also in 2: D031#map-each-detox-call, D059#resize-inside-a-test
    term `assertVisible` also in 1: D032#rewrite-one-flow
    term `await expect(locator).toBeVisible()` also in 2: D030#map-each-command, D034#map-each-webdriver-call
- **[ONLY HERE]** | `assertVisible: { text, enabled: true }` | `.toBeVisible()` and `.toBeEnabled()` |
    term `.toBeEnabled()` also in 2: D045#locator-matchers, D045#soft-assertions
- **[ONLY HERE]** | `assertVisible: { checked, selected, focused }` | `.toBeChecked()`, `.toBeSelected()`, `.toBeFocused()` |
    term `.toBeChecked()` also in 4: D031#map-each-detox-call, D033#map-each-api, D033#what-differs-on-purpose, D045#locator-matchers
    term `.toBeFocused()` also in 1: D045#locator-matchers
    term `.toBeSelected()` also in 1: D045#locator-matchers
- **[ONLY HERE]** | `assertTrue: ${...}` | `expect(value).toBe(true)`, or `expect.poll` for a value that is still changing |
- **[ONLY HERE]** | `extendedWaitUntil: { visible, timeout }` | `.toBeVisible({ timeout })` |
- **[ONLY HERE]** | `assertScreenshot: { path, thresholdPercentage }` | `await expect(screen).toHaveScreenshot(name, { maxDiffPixelRatio })`, see [Visual comparison](/visual-testing) |
- **[ONLY HERE]** | `assertDarkMode`, `assertLightMode` | Not yet. Assert on a themed control |
- **[ONLY HERE]** | `retry: { maxRetries, commands }` | `expect.poll` for a value, `{ retries }` on the test for the flow |
- **[ALSO: D031#map-each-detox-call]** | `takeScreenshot` | `app.screenshot('label')`, redacted, withheld after a secret fill |
    term `app.screenshot('label')` also in 3: D015#artifacts, D031#map-each-detox-call, D034#map-each-webdriver-call
    term `takeScreenshot` also in 1: D031#map-each-detox-call
- **[(short, not compared)]** | `setLocation` | `device.setLocation({ latitude, longitude })` |
    term `device.setLocation({ latitude, longitude })` also in 1: D031#map-each-detox-call
    term `setLocation` also in 3: D031#map-each-detox-call, D035#physical-devices, D047#device
- **[ONLY HERE]** | `travel: { points }` | `device.setLocation` in a loop |
    term `device.setLocation` also in 3: D031#map-each-detox-call, D035#physical-devices, D047#device
- **[ONLY HERE]** | `setAirplaneMode`, `toggleAirplaneMode` | `device.setAirplaneMode(true)` or `false`, the state you want; `true` is Android only |
    term `device.setAirplaneMode(true)` also in 2: D035#the-device-fixture, D047#device
    term `setAirplaneMode` also in 2: D035#the-device-fixture, D047#device
- **[ONLY HERE]** | `setDarkMode`, `toggleDarkMode` | `device.setAppearance('dark')` or `'light'` |
    term `'light'` also in 2: D047#device, D053#options
    term `device.setAppearance('dark')` also in 3: D035#write-a-device-test, D047#device, D047#reference-mobile
- **[ALSO: D047#device]** | `setPermissions` | `device.setPermission(name, 'grant' \| 'deny' \| 'reset')`, one permission per call, on the target's app, which need not be running; call it before `app.open()` |
- **[ONLY HERE]** | platform-specific selectors | `device.locator('role=text label="..."')`, agent-device's selector terms |
- **[ONLY HERE]** | `assertWithAI`, `assertNoDefectsWithAI` | `agent.assert('...')`, `agent.assert('...', { vision: true })` |
- **[ALSO: D030#map-each-command]** | `runFlow: file.yaml` | a function, or a fixture from `test.extend` |
- **[ONLY HERE]** | `runFlow: { when: { visible } }` | `if (await locator.isVisible()) { ... }`, see [Rewrite selectors](#rewrite-selectors) |
- **[ONLY HERE]** | `optional: true` on a command | the same `isVisible()` check |
    term `isVisible()` also in 8: D032#rewrite-selectors, D033#map-each-api, D033#what-differs-on-purpose, D034#map-each-webdriver-call, D035#troubleshooting, D050#locator-reads, D050#match-rules, D050#queries
- **[ONLY HERE]** | `repeat: { times: n }`, `repeat: { while }` | a `for` or `while` loop |
- **[ONLY HERE]** | `runScript`, `evalScript`, `${output.x}` | TypeScript in the test |
- **[ALSO: D033#map-each-api]** | `http.get`, `http.post`, `json()` | Node `fetch`, see [API](/api-testing) |
    term `json()` also in 9: D003#api-testing, D005#recording-on-the-provider, D005#write-a-provider, D033#map-each-api, D035#hosted-devices, D045#value-matchers, D045#valueexpectation, D048#custom-reporters, D053#the-browser-fixture
- **[(short, not compared)]** | `onFlowStart`, `onFlowComplete` | `beforeEach`, `afterEach` |
- **[ONLY HERE]** | `startRecording`, `stopRecording` | `test('x', { video: 'on' }, ...)` records that test's whole attempts; no start and stop inside a test |

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D030#map-each-command: Both map test commands to e2e equivalents such as doubleTap, toBeHidden and a fixture from test.extend.
- D031#rewrite-one-spec: Both point to mobile({ settle, transition }) as the engine-wide way to handle slow-settling screens and state app.open() must start the test.
- D030#map-each-command: Both map reusable flows and text reads to a function or test.extend fixture and locator.textContent.
- D031#port-the-config: Both map launch permissions and launch arguments to app.permissions, app.launchArguments or device.openApp options (grant, deny, reset).
- D031#map-each-detox-call: Both map launch/clear state, setLocation, setOrientation, swipe direction (finger vs content), scrollUntilVisible and screenshots to e2e calls.
- D032#rewrite-one-flow: Both show Maestro launchApp clearState, tapOn, inputText and scrollUntilVisible rewritten as app.clearState, agent.act and screen.scrollUntilVisible.
- D032#rewrite-selectors: Both state that spatial selectors (below, above, leftOf, rightOf) have no equivalent and that isVisible() replaces optional and runFlow when.
- D033#map-each-api: Both map framework calls to e2e equivalents, including screenshots, expect.poll, test.extend, hooks, video and the rule that screen, app, agent and expect run on every target.
- D034#map-each-webdriver-call: Both map reusable page-object or flow code to a test.extend fixture.
- D035#launch-arguments-and-permissions: Both state app.launchArguments and app.permissions apply to every fresh launch with grant, deny and reset values.
- D035#the-device-fixture: Both describe device.clearKeychain, device.openLink, device.openApp and device.setAirplaneMode behaviour.
- D035#physical-devices: Both state which device calls (clipboard, keychain, location, permission, appearance, openLink) work on which devices.
- D035#what-differs-from-the-web: Both state app.open() launches the app fresh and device.openLink(url) opens a link.
- D038#unique: Both say unique() around a value in act params keeps the replay cache working.
- D039#restart: Both give app.restart() as the way to restart the app.
- D039#clearstate: Both give app.clearState() as the way to clear app state.
- D039#screenshot: Both say app.screenshot output is redacted and withheld after a secret fill.
- D041#the-app-under-test: Both describe app.launchArguments and app.permissions set on the target and applied to each fresh launch.
- D041#recording: Both say a test option video: 'on' records that test.
- D045#screenshot-matchers: Both cover toHaveScreenshot with maxDiffPixelRatio tolerance.
- D045#polling-a-value: Both give expect.poll for a value that is still changing.
- D047#reference-mobile: Both say a test using device declares requires: ['device'] so other targets skip it.
- D047#engine: Both cover launchArguments and permissions on fresh launches, app.open fresh launch, and the settle and transition engine options.
- D047#device: Both list device methods such as clearKeychain, openLink, setClipboard, setLocation, setAirplaneMode, setOrientation and dismissKeyboard.
- D047#device-fixture: Both describe device.openApp relaunch with launchArguments and permissions replacing the target's values for one launch.
- D052#hooks: Both map flow start and complete hooks to beforeEach and afterEach.
- D032#rewrite-selectors: Both state that spatial Maestro selectors (below, above, leftOf, rightOf, containsDescendants) have no equivalent and isVisible() replaces optional and runFlow when.
- D033#map-each-api: Both map screenshots, expect.poll, test.extend, hooks, app.back and retries to e2e equivalents.
- D035#expo-development-builds: Both describe launch arguments for a fresh launch and device.openLink for links.
- D039#restart: Both give app.restart() for stopping and relaunching the app.
- D039#clearstate: Both give app.clearState() for Maestro's launchApp clearState.
- D047#device: Both map device.openApp, closeApp, clearKeychain (iOS only), openLink and locator, with launch arguments and permissions.
- D047#engine-options: Both map Maestro permissions to grant, deny, reset.
- D047#device-fixture: Both give the permission states grant, deny, reset and openApp relaunch options.
- D050#refinement: Both use nth(index) to select one match by zero-based position.
- D050#locator-actions: Both describe longPress with a duration option and fill replacing content.

## S21 · multi-section · D050#locator-actions  (screen and Locator › Reference › Locator actions; page title: screen and Locator)

Regel: mindestens zwei Abschnitte, jeder liefert einen nötigen Teil; enthaltene oder umschließende Abschnitte zählen nicht als zweiter; H1 nur mit Grund in `notes`.

**Typ-Eignung:** Trägt `factual` oder `procedural`: „Each action resolves one node, waits for actionability, and performs one operation. The timeout is `config.actionTimeout`, and every action takes `{ timeout }`“. Für `multi-section` braucht es einen zweiten nötigen Teil, z. B. die Definition von `actionTimeout` in D041 oder Actionability in D042#capabilities. „actionability“ steht in acht Abschnitten; prüfe, welcher Teil wirklich nötig ist.

- **[ONLY HERE]** ### Locator actions Each action resolves one node, waits for actionability, and performs one operation.
- **[ONLY HERE]** The timeout is [`config.actionTimeout`](/reference/config#actiontimeout), and every action takes `{ timeout }` to override it.
    term `config.actionTimeout` also in 5: D047#device, D050#locator-reads, D050#screen-actions, D050#types, D053#the-browser-fixture
    term `{ timeout }` also in 7: D015#common-errors, D032#map-each-command, D033#browser-timeouts-and-artifacts, D033#map-each-api, D045#negation, D045#timeouts-and-failures, D053#the-browser-fixture
- **[ONLY HERE]** An action takes only the options its signature names. #### `tap` The options are [`TapOptions`](#types):
    term `TapOptions` also in 1: D050#types
- **[ONLY HERE]** - `modifiers`: the browser engine holds them.
    term `modifiers` also in 10: D018#what-the-context-holds, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D042#capabilities, D042#engine, D046#the-catalog, D047#engine, D050#types
- **[ALSO: D033#map-each-api]** - `position`: an offset from the node's top-left corner, in CSS pixels.
- **[ONLY HERE]** The engine scrolls the node into view when it lists `scrollIntoView`.
    term `scrollIntoView` also in 7: D025#what-does-not-work, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D042#capabilities, D047#engine
- **[ALSO: D050#screen-actions]** Then it reads the node's box and dispatches the pointer at the point.
- **[ONLY HERE]** No node is behind the gesture, so the platform's other actionability checks (enabled, not covered) do not run. #### `doubleTap` Takes `timeout` and `modifiers`, with the same rules and errors as [`tap`](#tap). #### `secondaryTap` Takes `timeout` and `modifiers`, with the same rules and errors as [`t
    term `longPress` also in 9: D018#what-the-context-holds, D031#map-each-detox-call, D032#map-each-command, D035#troubleshooting, D038#action-tools, D042#actions, D042#capabilities, D047#engine, D050#types
    term `modifiers` also in 10: D018#what-the-context-holds, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D042#capabilities, D042#engine, D046#the-catalog, D047#engine, D050#types
    term `secondaryTap` also in 10: D018#what-the-context-holds, D030#map-each-command, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D042#capabilities, D042#engine, D047#engine, D050#types
- **[(short, not compared)]** Anything else is `INVALID_ARGUMENT`.
- **[ALSO: D047#engine]** - Without it the engine's default applies: 500 ms on the browser engine, one second on the mobile engine, past a React Native `Pressable`'s `delayLongPress`. #### `fill` Replaces the input's current content.
    term `Pressable` also in 1: D047#engine
    term `delayLongPress` also in 1: D047#engine
- **[ONLY HERE]** A `Secret` is resolved on the host right before the call and never logged, reported, or sent to a model.
- **[ONLY HERE]** **Note** `fill` sets the value directly and fires no key events.
- **[ONLY HERE]** An autocomplete, a search-as-you-type box, or a masked input wired to `keydown` or `keyup` never reacts to it.
    term `keydown` also in 1: D060#keyboard
    term `keyup` also in 1: D060#keyboard
- **[ONLY HERE]** Use [`pressSequentially`](#presssequentially) for those. #### `pressSequentially` Types through the engine's keyboard and appends to the current content.
    term `pressSequentially` also in 4: D033#map-each-api, D042#capabilities, D050#types, D060#keyboard
- **[ONLY HERE]** - `delay` waits that many milliseconds between characters, each sent in its own keyboard call.
    term `delay` also in 3: D033#map-each-api, D047#engine, D050#types
- **[ONLY HERE]** Without it the whole text goes in one call.
- **[ONLY HERE]** - Focus, pauses, and keystrokes share the one action deadline: a pause is cut short at it and no character is sent past it.
- **[ONLY HERE]** - It relies on the [keyboard contract](/reference/engine#engine):
- **[ALSO: D042#capabilities]** `type` must deliver text as a person typing would, so key events reach the app where the platform has them.
- **[ALSO: D033#map-each-api, D042#actions, D060#keyboard]** - The step records the locator, not the text, like `fill`. #### `clear` #### `press` A key is zero or more modifiers and one key, joined with `+`, as the [key grammar](/reference/engine#keys) lists them.
- **[ONLY HERE]** `Shift++` presses `+`. #### `check` #### `uncheck` #### `selectOption` Pass a label string, or an object with exactly one of `label`, `value` (the value attribute, which the form submits), or `index` (zero-based). #### `focus` #### `hover` #### `setInputFiles` #### `dragTo` #### `scrollIntoView` ###
    term `dragTo` also in 6: D033#map-each-api, D034#map-each-webdriver-call, D038#action-tools, D042#actions, D042#capabilities, D047#engine
    term `scrollIntoView` also in 7: D025#what-does-not-work, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D042#capabilities, D047#engine
    term `setInputFiles` also in 8: D005#reach-into-an-iframe, D030#map-each-command, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D042#capabilities, D047#engine
    term `{ direction, momentum? }` also in 1: D050#screen-actions
- **[ONLY HERE]** It has no `{ from, to }` form.
    term `{ from, to }` also in 4: D033#map-each-api, D042#capabilities, D042#engine, D047#engine
- **[(short, not compared)]** | [`tap`](#tap) | `Promise<void>` |
- **[(short, not compared)]** | [`click`](#tap) | `Promise<void>` |
- **[(short, not compared)]** | [`doubleTap`](#doubletap) | `Promise<void>` |
- **[(short, not compared)]** | [`dblclick`](#doubletap) | `Promise<void>` |
    term `dblclick` also in 3: D030#map-each-command, D033#map-each-api, D050#types
- **[(short, not compared)]** | [`secondaryTap`](#secondarytap) | `Promise<void>` |
    term `secondaryTap` also in 10: D018#what-the-context-holds, D030#map-each-command, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D042#capabilities, D042#engine, D047#engine, D050#types
- **[(short, not compared)]** | [`longPress`](#longpress) | `Promise<void>` |
    term `longPress` also in 9: D018#what-the-context-holds, D031#map-each-detox-call, D032#map-each-command, D035#troubleshooting, D038#action-tools, D042#actions, D042#capabilities, D047#engine, D050#types
- **[(short, not compared)]** | [`fill`](#fill) | `Promise<void>` |
- **[(short, not compared)]** | [`pressSequentially`](#presssequentially) | `Promise<void>` |
    term `pressSequentially` also in 4: D033#map-each-api, D042#capabilities, D050#types, D060#keyboard
- **[(short, not compared)]** | [`clear`](#clear) | `Promise<void>` |
- **[(short, not compared)]** | [`press`](#press) | `Promise<void>` |
- **[(short, not compared)]** | [`check`](#check) | `Promise<void>` |
- **[(short, not compared)]** | [`uncheck`](#uncheck) | `Promise<void>` |
    term `uncheck` also in 7: D033#map-each-api, D033#what-differs-on-purpose, D038#action-tools, D042#actions, D042#capabilities, D045#asyncexpectation-and-textmatcheroptions, D047#engine
- **[(short, not compared)]** | [`selectOption`](#selectoption) | `Promise<void>` |
    term `selectOption` also in 8: D030#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D035#write-a-device-test, D038#action-tools, D042#actions, D042#capabilities, D047#engine
- **[(short, not compared)]** | [`focus`](#focus) | `Promise<void>` |
- **[(short, not compared)]** | [`hover`](#hover) | `Promise<void>` |
- **[(short, not compared)]** | [`setInputFiles`](#setinputfiles) | `Promise<void>` |
    term `setInputFiles` also in 8: D005#reach-into-an-iframe, D030#map-each-command, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D042#capabilities, D047#engine
- **[(short, not compared)]** | [`dragTo`](#dragto) | `Promise<void>` |
    term `dragTo` also in 6: D033#map-each-api, D034#map-each-webdriver-call, D038#action-tools, D042#actions, D042#capabilities, D047#engine
- **[(short, not compared)]** | [`scrollIntoView`](#scrollintoview) | `Promise<void>` |
    term `scrollIntoView` also in 7: D025#what-does-not-work, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D042#capabilities, D047#engine
- **[(short, not compared)]** | [`swipe`](#swipe) | `Promise<void>` |
- **[ALSO: D050#screen-actions]** | `UNSUPPORTED_CAPABILITY` | The engine does not list the action's kind in `actions`; thrown before reaching the engine. |
- **[ALSO: D045#screenshot-matchers, D053#the-browser-fixture]** | `INVALID_ARGUMENT` | An option key the action does not take, Playwright's `trial`, `force`, or `noWaitAfter` included. Thrown before the node is resolved, so the control is never touched. |
    term `noWaitAfter` also in 1: D033#map-each-api
    term `trial` also in 4: D014#assertions, D033#map-each-api, D037#add-an-agent-step, D038#agent-assert
- **[ONLY HERE]** | `LOCATOR_NOT_FOUND` | No match before the timeout. |
- **[ONLY HERE]** | `LOCATOR_AMBIGUOUS` | More than one match. |
- **[ONLY HERE]** | `ACTION_FAILED` | The action may already have committed; it is never repeated. |
- **[ONLY HERE]** | `INVALID_ARGUMENT` | An unknown or repeated modifier, or `modifiers` beside `position`. |
    term `modifiers` also in 10: D018#what-the-context-holds, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D042#capabilities, D042#engine, D046#the-catalog, D047#engine, D050#types
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | `modifiers` on an engine that does not declare `tapModifiers`, the mobile engine among them; thrown before it acts. |
    term `modifiers` also in 10: D018#what-the-context-holds, D033#map-each-api, D035#write-a-device-test, D038#action-tools, D042#actions, D042#capabilities, D042#engine, D046#the-catalog, D047#engine, D050#types
    term `tapModifiers` also in 9: D018#what-the-context-holds, D038#action-tools, D042#actions, D042#capabilities, D042#defineengine, D042#engine, D046#the-catalog, D047#engine, D050#types
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | `position` on an engine without the `tap` pointer action. |
- **[ONLY HERE]** | `ACTION_FAILED` | `position` on a node the browser engine cannot bring into view; its scroll waits for visibility. Other engines fail as they report it. |
- **[ONLY HERE]** | `LOCATOR_NOT_FOUND` | `position` on a node that resolves but never shows a visible box within the timeout. |
- **[ONLY HERE]** | `ACTION_FAILED` | The deadline passed mid-text; the error names how many characters landed. |
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | The engine lacks the `focus` action or the `keyboard` capability; thrown before any node resolves. |
- **[ONLY HERE]** | `INVALID_ARGUMENT` | A `Secret` at runtime (a type error at compile time): a secret is filled, never typed as keystrokes. |
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | A key the platform lacks. |
- **[ONLY HERE]** | `INVALID_ARGUMENT` | More than one option per call: an array, or an object with more than one of those keys. Also a negative or fractional `index`. Thrown before the engine acts. |
- **[ONLY HERE]** | `INVALID_ARGUMENT` | An empty list or a blank entry. |
- **[ALSO: D050#refinement, D050#screen-actions]** | `INVALID_LOCATOR` | `target` is not a runner locator, or was made by another target's screen. |
    term `INVALID_LOCATOR` also in 8: D033#map-each-api, D042#errors, D042#shared-semantics, D044#runner-codes, D050#queries, D050#refinement, D050#screen-actions, D053#the-browser-fixture

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D030#map-each-command: Both list locator actions tap, doubleTap, secondaryTap, clear, selectOption and setInputFiles, and LOCATOR_AMBIGUOUS on several matches.
- D033#map-each-api: Both describe locator actions tap, doubleTap, secondaryTap, fill, pressSequentially, press, check, selectOption, setInputFiles and tap position or modifiers.
- D042#capabilities: Both state modifiers need tapModifiers and unlisted action kinds fail with UNSUPPORTED_CAPABILITY before the engine.
- D015#common-errors: Both explain LOCATOR_NOT_FOUND, LOCATOR_AMBIGUOUS and ACTION_FAILED causes for an action.
- D018#what-the-context-holds: Both say tapModifiers is true when tap, doubleTap and secondaryTap accept modifiers.
- D030#map-each-command: Both show doubleTap/dblclick, secondaryTap, selectOption and setInputFiles as the click, select and file actions.
- D031#map-each-detox-call: Both describe tap, doubleTap, longPress and fill replacing content.
- D032#map-each-command: Both describe longPress with a duration option and fill replacing content.
- D033#map-each-api: Both say Playwright trial, force and noWaitAfter options are rejected as INVALID_ARGUMENT, and describe fill, pressSequentially and secondaryTap.
- D034#map-each-webdriver-call: Both show selectOption by label and dragTo for dragging to a target.
- D035#write-a-device-test: Both say the mobile engine lacks selectOption, setInputFiles, scrollIntoView, secondaryTap and tap modifiers.
- D038#action-tools: Both say modifiers on tap, doubleTap and secondaryTap need tapModifiers and map actions to fill, selectOption and scrollIntoView.
- D042#capabilities: Both describe tapModifiers and the tap pointer action capability needed for modifiers and position.
- D042#actions: Both list the node actions (tap, doubleTap, secondaryTap, longPress, fill, selectOption, setInputFiles, dragTo, scrollIntoView) and longPress duration.
- D042#errors: Both map not-actionable, may-have-committed and timeout failures to ACTION_FAILED and unsupported actions to UNSUPPORTED_CAPABILITY.
- D044#agenterror: Both define LOCATOR_NOT_FOUND, LOCATOR_AMBIGUOUS and ACTION_FAILED, including an action that may already have committed.
- D046#the-catalog: Both list the modifiers Shift, Control, Alt, Meta, ControlOrMeta held for a click when the engine declares tapModifiers.
- D047#engine: Both describe mobile longPress default hold time and delayLongPress, plus modifiers unsupported on mobile.
- D050#screen-actions: Both describe tap position versus screen.tapAt and swipe parameters and action timeout.
- D050#locator-reads: Both say the timeout defaults to config.actionTimeout and several matches give LOCATOR_AMBIGUOUS.
- D050#types: Both define TapOptions, ClickOptions modifiers, LongPressOptions duration 100 to 10000 ms, PressSequentiallyOptions delay and SelectOption.
- D060#keyboard: Both say pressSequentially types through the engine keyboard hook so key events reach the app.
- D050#types: Both define TapOptions position, ClickOptions modifiers, LongPressOptions duration 100 to 10000 ms, delay and SelectOption.
- D060#capabilities: Both say a node action the engine does not declare throws UNSUPPORTED_CAPABILITY.

## S22 · detail · D050#refinement  (screen and Locator › Reference › Refinement; page title: screen and Locator)

Regel: genau ein Abschnitt, ein einzelnes Faktum, Referenzantwort höchstens 30 Wörter; das Faktum muss nur hier stehen.

**Typ-Eignung:** Trägt `conceptual`: „Refinement returns a new locator without querying the app.“ (nur hier) oder `limitation`: `nth` mit negativem oder nicht ganzzahligem Index ist `INVALID_LOCATOR` (nur hier). Nicht `comparative` über `hasText` gegen Abfragetext: die Hälfte „query text matches exactly“ steht in D050#queries, damit zwei Abschnitte, `detail` gebrochen.

- **[ONLY HERE]** ### Refinement Refinement returns a new locator without querying the app. #### `filter` - `hasText` with a string is a case-insensitive substring match over the match and its descendants, unlike a query text, which matches exactly.
    term `hasText` also in 7: D005#shadow-dom, D014#locators, D030#map-each-command, D032#rewrite-selectors, D033#map-each-api, D046#the-catalog, D053#the-browser-fixture
- **[ONLY HERE]** Pass a `RegExp` for anything stricter.
- **[ONLY HERE]** - `has` keeps a match whose subtree resolves the inner locator. #### `first` #### `last` #### `nth`
- **[ONLY HERE]** | `INVALID_LOCATOR` | Neither `hasText` nor `has` is given. |
    term `INVALID_LOCATOR` also in 8: D033#map-each-api, D042#errors, D042#shared-semantics, D044#runner-codes, D050#locator-actions, D050#queries, D050#screen-actions, D053#the-browser-fixture
    term `hasText` also in 7: D005#shadow-dom, D014#locators, D030#map-each-command, D032#rewrite-selectors, D033#map-each-api, D046#the-catalog, D053#the-browser-fixture
- **[ONLY HERE]** | `INVALID_LOCATOR` | Any other key, even beside them: `hasNot`, `hasNotText`, and `visible` are not filters here. |
    term `INVALID_LOCATOR` also in 8: D033#map-each-api, D042#errors, D042#shared-semantics, D044#runner-codes, D050#locator-actions, D050#queries, D050#screen-actions, D053#the-browser-fixture
    term `hasNot` also in 1: D033#map-each-api
    term `hasNotText` also in 1: D033#map-each-api
- **[ALSO: D050#locator-actions, D050#screen-actions]** | `INVALID_LOCATOR` | `has` is not a runner locator, or was made by another target's screen. |
    term `INVALID_LOCATOR` also in 8: D033#map-each-api, D042#errors, D042#shared-semantics, D044#runner-codes, D050#locator-actions, D050#queries, D050#screen-actions, D053#the-browser-fixture
- **[ONLY HERE]** | `INVALID_LOCATOR` | A negative or non-integer index. |
    term `INVALID_LOCATOR` also in 8: D033#map-each-api, D042#errors, D042#shared-semantics, D044#runner-codes, D050#locator-actions, D050#queries, D050#screen-actions, D053#the-browser-fixture

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D032#rewrite-selectors: Both name filter, first() and hasText as ways to narrow several matches.
- D014#locators: Both show filter({ hasText }) and say first(), nth() or filter() narrow a locator matching several nodes.
- D030#map-each-command: Both map Cypress contains, first and eq to filter({ hasText }), first() and nth(n).
- D031#map-each-detox-call: Both map atIndex to nth(n) and say to narrow multiple matches with filter, first or nth.
- D032#map-each-command: Both use nth(index) to select one match by zero-based position.
- D032#rewrite-selectors: Both describe filter({ has, hasText }) and first() for narrowing locator matches.
- D033#map-each-api: Both say filter takes hasText and has, hasNot and hasNotText are not supported (INVALID_LOCATOR), and first, last, nth exist.
- D033#what-differs-on-purpose: Both say a locator with several matches must be narrowed with filter, first or nth.
- D034#map-each-webdriver-call: Both use nth(n) to pick one of several matches and say to narrow with filter, first or nth.
- D050#queries: Both cover case-insensitive substring text matching and combining first, last and nth with scopes and filter.
- D053#the-browser-fixture: Both describe filter({ has }) to find an element that contains another and filter({ hasText }).

## S23 · paraphrase · D052#fixtures  (test › Reference › Fixtures; page title: test)

Regel: genau ein Abschnitt; die Frage teilt kein Inhaltswort mit der Abschnittsüberschrift oder dem Seitentitel (auch keine Wortformen).

**Typ-Eignung:** Trägt `conceptual`: Jede Definition einer `extend`-Kette läuft für jeden Fall, „whether or not the test names it“ (nur hier), deshalb verschiedene Ketten für verschiedene Setups; daneben lazy (eingebaute) gegen nicht lazy (eigene) Fixtures und die Reihenfolge Setup → Hooks → Teardown in umgekehrter Reihenfolge. Wortsperre: „test“ (Seitentitel!), „tests“, „testing“, „fixture(s)“, „reference“ dürfen nicht in die Frage.

- **[ONLY HERE]** ### Fixtures `agent`, `app`, and `screen` reach test bodies, `beforeEach`, and `afterEach`.
- **[ONLY HERE]** `platform` reaches every hook too, and `session` only `test.setup` bodies. [`TestFixtures`](#testfixtures) describes each one.
    term `TestFixtures` also in 5: D042#engine, D049#session, D052#function-types, D052#testapi, D052#testfixtures
- **[ALSO: D044#agenterror]** Everything else is a fixture the target's engine contributes, or one of [your own](#your-own-fixtures).
- **[ONLY HERE]** `@e2e-dev/web` contributes [`browser`](/reference/web); a device engine contributes `device`.
- **[ONLY HERE]** **Note** The fixtures above are lazy.
- **[ONLY HERE]** Destructuring in the parameter list acquires them before the body's first statement. [Your own fixtures](#your-own-fixtures) are not lazy. #### Your own fixtures `test.extend(fixtures)` defines resources set up before each test and cleaned up afterward, including after a failure.
- **[ONLY HERE]** In each fixture function, code before `await use(value)` sets up the resource.
    term `await use(value)` also in 1: D052#fixturedefinitions
- **[ONLY HERE]** The test receives `value`, and code after `use` tears it down.
- **[ALSO: D052#fixturedefinitions]** A definition is typed against the fixtures of the `test` it extends, not its siblings in the same call.
- **[ALSO: D033#map-each-api, D052#fixturedefinitions]** A fixture that needs another goes in a chained second `extend`:
- **[ONLY HERE]** `base.extend({ a }).extend({ b })` gives `b` a fixture object that already has `a`.
- **[ALSO: D052#testapi]** Each definition in the `extend` chain the test was registered through runs in declaration order, after the engine's fixtures, until it calls `use`.
- **[ONLY HERE]** It runs whether or not the test names it.
- **[ONLY HERE]** A fixture that opens a page or changes app state does so for every test of that `test`.
- **[ONLY HERE]** So a file whose tests need different setups registers them through different `extend` chains.
- **[ONLY HERE]** Setup counts against the test `timeout`.
- **[ONLY HERE]** A failure is reported in phase `beforeEach`, before any `beforeEach` hook has run. 2.
- **[ONLY HERE]** `beforeEach` hooks, the body, then `afterEach` hooks run with the same fixture object.
- **[ONLY HERE]** The fixture set is the test's own chain: a hook that reads `workspace` around a test registered through `base` fails with `UNSUPPORTED_CAPABILITY`. 3.
- **[ALSO: D052#fixturedefinitions]** Teardowns run in reverse order after the last `afterEach`, whether or not the body passed, each with its own `cleanupTimeout` budget.
- **[ONLY HERE]** An error there fails a passing attempt in phase `afterEach` and joins `secondaryErrors` after a body failure.
    term `secondaryErrors` also in 3: D044#runner-codes, D045#polling-a-value, D045#soft-assertions
- **[ONLY HERE]** **Note** A body or hook that hits the test `timeout` is abandoned, not cancelled, so teardown starts while it may still be running.
- **[ONLY HERE]** A setup abandoned this way that reaches `use` later gets an immediate resolve.
- **[ONLY HERE]** Its teardown runs detached from the run, so what it allocated is still released.
- **[ONLY HERE]** Later fixtures, hooks, and the test body do not start after an abandoned setup or hook finishes.
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | A test reaches for a fixture the engine does not contribute. Declare `requires: ['browser']` to skip such tests at selection instead. |
    term `requires: ['browser']` also in 5: D005#browser, D033#map-each-api, D033#port-page-objects, D053#options, D053#the-browser-fixture
- **[ALSO: D041#the-app-under-test, D042#shared-semantics, D043#engines, D043#telemetry, D044#runner-codes]** | A value that is not a plain object of functions, an empty name, a core name (`agent`, `app`, `screen`, `platform`, `session`), or a name an earlier `extend` in the chain defined | At import, `COLLECTION_ERROR` naming the fixture |
- **[ALSO: D044#agenterror]** | A name the target's engine contributes (`browser` on a Playwright target) | The attempt, in `beforeEach`, `TEST_SETUP_FAILED` |
    term `TEST_SETUP_FAILED` also in 3: D001#how-a-step-ends, D038#agent-act, D044#agenterror
- **[ONLY HERE]** | A definition that returns without calling `use` | The attempt, in `beforeEach`, `TEST_SETUP_FAILED` |
    term `TEST_SETUP_FAILED` also in 3: D001#how-a-step-ends, D038#agent-act, D044#agenterror
- **[ONLY HERE]** | A definition that calls `use` twice | The attempt, at teardown, `TEST_SETUP_FAILED` |
    term `TEST_SETUP_FAILED` also in 3: D001#how-a-step-ends, D038#agent-act, D044#agenterror
- **[ONLY HERE]** | A definition that throws before `use` | The attempt, in `beforeEach`, with that error |
- **[ONLY HERE]** | A definition that throws after `use` | The attempt, in `afterEach`, with that error |

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D030#map-each-command: Both say test.extend defines custom fixtures for setup and helpers.
- D033#map-each-api: Both cover test.extend fixtures and the declared requires for missing fixtures.
- D042#capabilities: Both state a test needing a missing fixture is skipped via requires, else UNSUPPORTED_CAPABILITY.
- D052#hooks: Both say teardown runs after failure with its own cleanupTimeout budget and hooks share the test timeout.
- D005#browser: Both advise requires: ['browser'] on tests in suites with device targets.
- D014#organize-tests: Both say to use test.extend for setup and cleanup and that fixtures hold per-test data.
- D033#map-each-api: Both say a fixture needing another goes in a chained extend and every fixture of the chain sets up for every test.
- D033#port-page-objects: Both say reaching for a browser fixture on a target without it fails with UNSUPPORTED_CAPABILITY; use requires: ['browser'].
- D041#top-level: Both describe cleanupTimeout as the budget of each afterEach hook and fixture teardown.
- D042#contributed-fixtures: Both say the target's engine contributes fixtures such as browser or device, and requires skips tests lacking one.
- D044#agenterror: Both say a test.extend fixture returning without use(), calling it twice, or redefining an engine fixture is TEST_SETUP_FAILED.
- D044#runner-codes: Both cover COLLECTION_ERROR for an invalid fixture definition and timeouts of abandoned bodies.
- D049#session: Both list the fixtures agent, app, screen and platform that a test or session receives.
- D052#members: Both describe test.extend returning a typed test with fixtures, and the core fixtures typed on hooks.
- D052#hooks: Both say fixture teardown and afterEach hooks each get their own cleanupTimeout budget after a failure.
- D052#testfixtures: Both list the core fixtures agent, app, screen, platform, and session for setup tests.
- D052#fixturedefinitions: Both describe test.extend fixture definitions where code before use() is setup and code after is teardown.
- D053#the-browser-fixture: Both say a suite also running on other targets declares requires: ['browser'] to skip tests lacking the browser fixture.

## S24 · detail · D050#types  (screen and Locator › Types; page title: screen and Locator)

Regel: genau ein Abschnitt, ein einzelnes Faktum, Referenzantwort höchstens 30 Wörter; das Faktum muss nur hier stehen.

**Typ-Eignung:** Trägt `conceptual`: geschlossenes `Role`-Vokabular, „Every engine maps its platform's element types onto these names, so a role query reads the same against a browser and a device.“ (nur hier). Alternative `limitation`: eine Rolle ohne Widget auf der Plattform „matches nothing there; it is never a type error“ (Wortlaut „matches nothing“ auch in D050#queries u. a., Inhalt prüfen).


Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D050#locator-actions: Both define TapOptions, ClickOptions modifiers, LongPressOptions duration 100 to 10000 ms, PressSequentiallyOptions delay and SelectOption.
- D032#rewrite-selectors: Both say visible: true handles a hidden twin of a node.
- D033#map-each-api: Both say a role query never matches hidden nodes and visible: true drops hidden twins on other queries.
- D042#capabilities: Both say modifiers on click actions require tapModifiers, else UNSUPPORTED_CAPABILITY.
- D042#actions: Both define ScrollDirection, Momentum, swipe direction and momentum and long-press duration.
- D042#exported-names: Both name KeyModifier, ScrollDirection, Momentum, SelectOption and ViewportPoint types.
- D042#semanticnode: Both describe heading level 1 through 6 for heading nodes.
- D050#queries: Both define the role vocabulary, the img alias, exact versus substring text matching, and visible: true to drop hidden twins.
- D050#screen-actions: Both define swipe direction and momentum options, swipe along a path with from, to and duration, and Point coordinates.
- D050#locator-actions: Both define TapOptions position, ClickOptions modifiers, LongPressOptions duration 100 to 10000 ms, delay and SelectOption.
