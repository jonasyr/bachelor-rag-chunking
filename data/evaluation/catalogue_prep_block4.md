# Vorbereitungsblatt Block 4 (S25–S32)

KI-Hilfe (Claude) vor dem Schreiben, offengelegt nach ADR 0031/0049. Mechanischer Teil wie bei Block 3: je Satz des
Ausgangsabschnitts (ohne Codeblöcke; Tabellenzeilen zählen je als ein Satz), ob eine Folge von 5 Wörtern auch im
eigenen Text eines anderen Abschnitts steht (außer umschließenden und enthaltenen Abschnitten), und für Begriffe in
Backticks, in welchen anderen Abschnitten sie vorkommen (nur bei höchstens 10 Treffern gelistet, dann vollständig).
Dazu die Zeilen aus `catalogue_overlap.csv` und je Slot die **Typ-Eignung** (ADR 0049, Nachtrag 10.11.2026): welche
Fragetypen der Text trägt, mit der Stelle, auf die sich der Typ stützt, und ob sie nur hier steht. Das ist ein
Vorschlag; den Typ wählt Jonas (ADR 0031). Das Blatt enthält keine Frage, keine Antwort und kein Relevanzurteil.
„ONLY HERE“ heißt nur: kein wörtlicher Treffer. Erstellt am 11.11.2026.

Typziel Block 4 ([Plan](../../docs/plan.md#zeitplan)): **2 conceptual, 2 comparative, 1 limitation, 2 procedural,
1 factual**. Vorschlag: S25 conceptual, S26 comparative, S27 limitation, S28 factual, S29 procedural, S30 conceptual,
S31 procedural, S32 comparative.

## S25 · detail · D038#agent-act  (agent › Reference › agent.act; page title: agent)

Regel: genau ein Abschnitt, ein einzelnes Faktum, Referenzantwort höchstens 30 Wörter; das Faktum muss nur hier stehen.

**Typ-Eignung:** Ziel `conceptual`: „`params` values come from your code, never from the model.“ und „Before the runner fills it, it checks the field the model picked: an enabled editable input, and a password field for a password. `locator.fill` runs no such check, since your code chose the field.“ (beide nur hier). Ein Grund in einem Satz passt zu `detail` (≤ 30 Wörter). Alternative `limitation`: failed gegen blocked verdict (`ACTION_FAILED` oder ein Code aus der Tabelle); prüfe dann D001 und D044#agenterror, die Verdikte ebenfalls beschreiben.

- **[ONLY HERE]** ### agent.act Plans and executes one bounded multi-action flow.
- **[ONLY HERE]** A passing verdict resolves with an `ActResult`.
    term `ActResult` also in 1: D038#types
- **[ONLY HERE]** A failing or blocked one throws an [`AgentError`](#agenterror) whose `code` and `blocked` flag say why.
    term `AgentError` also in 4: D038#agenterror, D044#agenterror, D044#exit-codes, D044#reference-errors
- **[ONLY HERE]** - `instruction` is 1 through 8192 UTF-8 bytes after NFC normalization.
- **[ONLY HERE]** - The [`ActResult`](#types) carries the step's `summary`, the `modelCalls` and `actions` it spent, and `cache`: how the [replay cache](/cache) took part.
    term `ActResult` also in 1: D038#types
    term `modelCalls` also in 3: D038#types, D048#step-progress, D049#host
- **[ALSO: D038#vision]** - The agent acts through the [action tools](#action-tools) and requests screenshots itself through the [pixel tools](#pixel-tools-screenshot-and-the-point-verbs).
- **[ONLY HERE]** `params` values come from your code, never from the model.
- **[ALSO: D007#how-a-replay-works, D038#unique]** Wrap a value that differs on every run in [`unique()`](#unique).
    term `unique()` also in 5: D007#what-must-match, D014#goals, D032#map-each-command, D038#types, D038#unique
- **[ONLY HERE]** The model sees a `Secret` as its name and purpose only.
- **[ALSO: D001#what-the-model-may-do]** Before the runner fills it, it checks the field the model picked: an enabled editable input, and a password field for a password.
- **[ONLY HERE]** `locator.fill` runs no such check, since your code chose the field.
    term `locator.fill` also in 3: D041#credentials, D041#secrets, D053#the-browser-fixture
- **[ONLY HERE]** A failed verdict is `ACTION_FAILED` unless the executor names a more specific code, such as `LOCATOR_NOT_FOUND` or `AUTHENTICATION_FAILED`.
    term `AUTHENTICATION_FAILED` also in 1: D044#agenterror
- **[ONLY HERE]** A blocked verdict means the step could not reach a product verdict.
- **[ONLY HERE]** It carries one of these codes:
- **[ONLY HERE]** The runner's own stops, and the checks on the call itself:
- **[(short, not compared)]** | `timeout` | `number` | `config.timeout`, 120000 |
    term `config.timeout` also in 4: D038#budgets, D038#types, D052#options, D052#testoptions
- **[ONLY HERE]** | `maxSteps` | `number` | `agents.<name>.maxSteps`, 25 |
    term `agents.<name>.maxSteps` also in 2: D038#budgets, D038#types
    term `maxSteps` also in 9: D002#define-named-agents, D007#limits-and-gaps, D015#common-errors, D018#what-the-executor-handles, D038#budgets, D038#types, D040#commands, D041#agentconfig, D041#agents
- **[ALSO: D038#agent-waitfor]** | `maxModelCalls` | `number` | `agents.<name>.maxModelCalls`, 25 |
    term `agents.<name>.maxModelCalls` also in 3: D038#agent-waitfor, D038#budgets, D038#types
- **[ALSO: D038#agent-assert, D038#agent-extract, D038#agent-waitfor]** | `agent` | `string` | the test's agent |
- **[(short, not compared)]** | credentials | `AUTH_CREDENTIAL_UNAVAILABLE`, `AUTH_CREDENTIAL_INVALID`, `SECRET_UNAVAILABLE` |
    term `AUTH_CREDENTIAL_INVALID` also in 2: D001#how-a-step-ends, D044#agenterror
    term `AUTH_CREDENTIAL_UNAVAILABLE` also in 3: D001#how-a-step-ends, D041#credentials, D044#agenterror
    term `SECRET_UNAVAILABLE` also in 4: D004#secrets-that-are-not-passwords, D041#secrets, D042#lifecycle, D044#agenterror
- **[(short, not compared)]** | environment | `ENVIRONMENT_UNAVAILABLE`, `APP_UNREACHABLE`, `APP_ALREADY_RUNNING` |
    term `APP_ALREADY_RUNNING` also in 4: D015#common-errors, D041#the-app-under-test, D044#agenterror, D059#let-the-runner-start-it
    term `APP_UNREACHABLE` also in 7: D008#upload-the-reports, D015#common-errors, D035#troubleshooting, D039#open, D041#the-app-under-test, D044#agenterror, D056#what-is-sent
    term `ENVIRONMENT_UNAVAILABLE` also in 2: D001#how-a-step-ends, D044#agenterror
- **[ONLY HERE]** | test setup | `TEST_SETUP_FAILED`, `APP_NOT_OPEN`, `POLICY_DENIED` |
    term `APP_NOT_OPEN` also in 6: D039#back, D042#errors, D044#agenterror, D047#device, D053#the-browser-fixture, D060#errors
    term `TEST_SETUP_FAILED` also in 3: D001#how-a-step-ends, D044#agenterror, D052#fixtures
- **[ONLY HERE]** | automation | `MODEL_UNAVAILABLE`, `AUTOMATION_UNSUPPORTED`, `STEP_BUDGET_EXHAUSTED`, `STEP_TIMEOUT`, `CONTEXT_OVERFLOW` |
    term `AUTOMATION_UNSUPPORTED` also in 5: D001#how-a-step-ends, D016#finishing-a-step, D016#limits, D018#replace-the-executor, D044#agenterror
    term `CONTEXT_OVERFLOW` also in 2: D007#when-a-recording-is-written, D044#agenterror
    term `MODEL_UNAVAILABLE` also in 9: D007#when-a-recording-is-written, D015#common-errors, D018#what-the-executor-handles, D036#what-fails-and-where, D040#commands, D041#resolution-order, D044#agenterror, D052#testfixtures, D055#pick-a-model
    term `STEP_BUDGET_EXHAUSTED` also in 5: D001#how-a-step-ends, D015#common-errors, D018#the-verdict, D038#agent-waitfor, D044#agenterror
    term `STEP_TIMEOUT` also in 9: D001#how-a-step-ends, D007#when-a-recording-is-written, D015#common-errors, D018#the-verdict, D020#the-comment, D035#troubleshooting, D038#agent-waitfor, D044#agenterror, D044#reference-errors
- **[ONLY HERE]** | `STEP_BUDGET_EXHAUSTED`, `STEP_TIMEOUT` | A budget or the deadline ran out. |
    term `STEP_BUDGET_EXHAUSTED` also in 5: D001#how-a-step-ends, D015#common-errors, D018#the-verdict, D038#agent-waitfor, D044#agenterror
    term `STEP_TIMEOUT` also in 9: D001#how-a-step-ends, D007#when-a-recording-is-written, D015#common-errors, D018#the-verdict, D020#the-comment, D035#troubleshooting, D038#agent-waitfor, D044#agenterror, D044#reference-errors
- **[ALSO: D044#agenterror]** | `CANCELLED` | The runner cancelled the step. |
    term `CANCELLED` also in 8: D018#the-verdict, D042#errors, D042#lifecycle, D044#agenterror, D045#polling-a-value, D046#several-sessions, D049#host, D053#options
- **[ONLY HERE]** | `STEP_NO_CONCLUSION` | The turns ran out without a conclusion. |
    term `STEP_NO_CONCLUSION` also in 1: D044#agenterror
- **[ALSO: D044#agenterror]** | `CONTEXT_OVERFLOW` | A request exceeded the model's context window. |
    term `CONTEXT_OVERFLOW` also in 2: D007#when-a-recording-is-written, D044#agenterror
- **[ONLY HERE]** | `MODEL_PROVIDER_FAILED` | The provider's transport failed after its retries. |
    term `MODEL_PROVIDER_FAILED` also in 6: D007#when-a-recording-is-written, D015#common-errors, D036#what-fails-and-where, D044#agenterror, D055#sign-in-help, D056#what-is-sent
- **[ONLY HERE]** | `MODEL_OUTPUT_INVALID` | A verdict outside the grammar. |
    term `MODEL_OUTPUT_INVALID` also in 6: D007#when-a-recording-is-written, D016#limits, D018#the-verdict, D038#agent-extract, D038#vision, D044#agenterror
- **[ONLY HERE]** | `REPLAY_STALE` | Under a strict cache, the step's recording no longer replays. |
    term `REPLAY_STALE` also in 6: D007#fail-on-a-stale-recording, D007#share-the-cache-across-checkouts, D040#commands, D041#cache, D041#cacheconfig, D044#agenterror
- **[ONLY HERE]** | `INVALID_ARGUMENT` | A malformed instruction, oversized `params`, an unknown option, or a budget above the configured limit. An unknown `agent` name fails before the step opens. |
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | `schema` or `vision`, which `act` does not take. |

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D037#add-an-agent-step: Both show agent.act with {placeholders} filled from params.
- D001#what-the-model-may-do: Both say the model sees a Secret only as a name and purpose and the runner fills it.
- D001#how-a-step-ends: Both describe failed versus blocked act verdicts and the codes for credentials, environment, seed data and budget limits.
- D002#define-named-agents: Both say maxSteps caps the actions of one step and maxModelCalls its model calls.
- D004#the-password-is-a-handle: Both say a Secret password param needs a password field and the model never sees the value.
- D007#fail-on-a-stale-recording: Both state REPLAY_STALE is raised under a strict cache when a recording no longer replays.
- D014#goals: Both show agent.act('invite {email} as an editor') with params.
- D015#common-errors: Both state that STEP_BUDGET_EXHAUSTED and STEP_TIMEOUT mean the agent ran out of actions, model calls or time.
- D038#agent-waitfor: Both give the per-call options timeout, maxModelCalls and agent with the agent's default maxModelCalls of 25.
- D038#budgets: Both give the act defaults: maxModelCalls 25, maxSteps 25 and a 120000 ms timeout.
- D038#types: Both describe act options and the ActResult returned by agent.act.
- D038#unique: Both say params values that differ on every run are wrapped in unique().
- D040#commands: Both mention the --max-steps and --max-model-calls limits (1 to 100) and step budgets.
- D041#agents: Both give the maxSteps and maxModelCalls defaults of 25 per agent.
- D041#credentials: Both show credentials.user supplying the username and password handle to agent.act params.
- D044#agenterror: Both list the act error codes such as STEP_BUDGET_EXHAUSTED, STEP_TIMEOUT, STEP_NO_CONCLUSION, CONTEXT_OVERFLOW, MODEL_OUTPUT_INVALID, REPLAY_STALE, APP_NOT_OPEN and credential and seed-data codes.
- D051#secret-fills: Both state the runner checks the target is an enabled, editable input (a password field for a password) before filling a Secret.
- D051#policy-denials: Both say the runner checks the model-picked field is an enabled editable input and a password field for a password.

## S26 · multi-section · D045#locator-matchers  (expect › Reference › Locator matchers; page title: expect)

Regel: mindestens zwei Abschnitte, jeder liefert einen nötigen Teil; enthaltene oder umschließende Abschnitte zählen nicht als zweiter; H1 nur mit Grund in `notes`.

**Typ-Eignung:** Ziel `comparative`: `toBeAttached` „waits for one match to exist, hidden or shown, where `toBeVisible` needs a shown one“ (zwei benannte Matcher). „hidden or shown“ steht auch in D050#locator-reads, das ist hier ein möglicher zweiter Abschnitt (`multi-section`). Alternative `conceptual`: wann ein Knoten als `disabled` gilt (`<fieldset disabled>` außer erste `<legend>`, `aria-disabled` an einem Vorfahren); `fieldset` steht auch in D050#queries. Für `multi-section` jeden Teil prüfen; die Abschnitte unter „Behavior“ (Strictness, Text matching) liefern weitere Teile.

- **[ONLY HERE]** ### Locator matchers `expect(locator)` returns an `AsyncExpectation`.
    term `AsyncExpectation` also in 2: D045#asyncexpectation-and-textmatcheroptions, D045#expectcall-softexpectcall-and-expect
    term `expect(locator)` also in 9: D007#when-a-recording-is-written, D030#map-each-command, D032#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D042#capabilities, D045#screenshot-matchers, D058#visual-testing, D060#capabilities
- **[ONLY HERE]** Each matcher polls until it holds or its timeout passes, under the rules in [Behavior](#behavior): [Strictness](#strictness), [Text matching](#text-matching), and [Secure fields](#secure-fields) among them.
- **[ALSO: D045#asyncexpectation-and-textmatcheroptions]** The options are in [`AsyncExpectation`](#asyncexpectation-and-textmatcheroptions). #### `toBeVisible` and `toBeHidden` `toBeVisible` waits for the one match to be shown.
    term `AsyncExpectation` also in 2: D045#asyncexpectation-and-textmatcheroptions, D045#expectcall-softexpectcall-and-expect
    term `toBeHidden` also in 10: D030#map-each-command, D031#map-each-detox-call, D032#map-each-command, D033#map-each-api, D035#known-device-limitations, D045#asyncexpectation-and-textmatcheroptions, D045#strictness, D050#queries, D059#resize-inside-a-test, D060#nodes-and-refs
- **[ALSO: D045#asyncexpectation-and-textmatcheroptions]** `toBeHidden` waits for a hidden or absent state. #### `toBeAttached` Waits for one match to exist, hidden or shown, where `toBeVisible` needs a shown one.
    term `toBeAttached` also in 4: D033#map-each-api, D035#known-device-limitations, D045#asyncexpectation-and-textmatcheroptions, D045#strictness
    term `toBeHidden` also in 10: D030#map-each-command, D031#map-each-detox-call, D032#map-each-command, D033#map-each-api, D035#known-device-limitations, D045#asyncexpectation-and-textmatcheroptions, D045#strictness, D050#queries, D059#resize-inside-a-test, D060#nodes-and-refs
- **[ONLY HERE]** Negated, or with `attached: false`, it waits for no match and passes once nothing matches. #### `toBeEnabled` and `toBeDisabled` `toBeEnabled` waits for an enabled node; `toBeDisabled` waits for a disabled one.
    term `attached: false` also in 2: D045#asyncexpectation-and-textmatcheroptions, D045#strictness
    term `toBeDisabled` also in 2: D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions
    term `toBeEnabled` also in 4: D032#map-each-command, D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions, D045#soft-assertions
- **[ONLY HERE]** A node is enabled unless it reports `disabled`.
- **[ONLY HERE]** On the web, `disabled` is the state the browser applies, not the attribute alone.
- **[ONLY HERE]** That is the reading Playwright's `toBeDisabled` gives:
    term `toBeDisabled` also in 2: D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions
- **[ONLY HERE]** - A control inside a `<fieldset disabled>` is disabled unless it sits in that fieldset's first `<legend>`.
    term `<legend>` also in 1: D050#queries
- **[ONLY HERE]** - `aria-disabled="true"` on an ancestor disables the widgets below it until an `aria-disabled="false"` cuts the chain. #### `toBeChecked`, `toBeSelected`, and `toBeExpanded` Each waits for its state: checked, selected, or expanded.
    term `toBeChecked` also in 7: D031#map-each-detox-call, D032#map-each-command, D033#map-each-api, D033#what-differs-on-purpose, D035#known-device-limitations, D045#asyncexpectation-and-textmatcheroptions, D045#option-validation
    term `toBeExpanded` also in 2: D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions
    term `toBeSelected` also in 4: D032#map-each-command, D033#map-each-api, D035#known-device-limitations, D045#asyncexpectation-and-textmatcheroptions
- **[ALSO: D033#what-differs-on-purpose, D045#asyncexpectation-and-textmatcheroptions, D050#locator-reads]** A missing `checked`, `selected`, or `expanded` state counts as `false`, so `.not.toBeChecked()` passes on a button or a heading. #### `toBeFocused` Waits for focused state. #### `toHaveText` and `toContainText` `toHaveText` waits for exact normalized text; `toContainText` waits for contained normali
    term `.not.toBeChecked()` also in 2: D033#map-each-api, D033#what-differs-on-purpose
    term `expanded` also in 7: D007#how-a-replay-works, D033#map-each-api, D042#semanticnode, D045#asyncexpectation-and-textmatcheroptions, D047#engine, D049#functions, D050#types
    term `toBeFocused` also in 3: D032#map-each-command, D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions
- **[ONLY HERE]** Both take a single `TextMatch` or a list.
    term `TextMatch` also in 8: D042#exported-names, D042#shared-semantics, D045#asyncexpectation-and-textmatcheroptions, D045#browserexpectation, D045#text-matching, D050#queries, D050#refinement, D050#types
- **[ONLY HERE]** A list form's failure message lists every text observed.
- **[ALSO: D045#asyncexpectation-and-textmatcheroptions]** **Note** Negated, `toContainText([...])` fails as soon as that ordered subsequence exists, so `not.toContainText(['Deleted'])` fails while any match contains `Deleted`. #### `toHaveValue` Waits for a form control's value, compared as it is.
    term `toContainText([...])` also in 1: D033#map-each-api
    term `toHaveValue` also in 9: D030#map-each-command, D031#map-each-detox-call, D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions, D045#secure-fields, D045#text-matching, D050#locator-reads, D050#queries, D051#policy-denials
- **[ONLY HERE]** - No normalization: newlines and trailing spaces count, and the failure message prints the value that way.
- **[ONLY HERE]** - A `contenteditable` editor's value is its rendered text, kept the same way.
    term `contenteditable` also in 2: D038#action-tools, D050#queries
- **[ALSO: D050#queries]** An empty editor reads as `''`.
- **[ONLY HERE]** - A control the platform reports without a value, such as a cleared field on a device, reads as `''`.
- **[ONLY HERE]** - A node whose role carries no value, such as a heading or a link, never satisfies `toHaveValue`, negated or not.
    term `toHaveValue` also in 9: D030#map-each-command, D031#map-each-detox-call, D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions, D045#secure-fields, D045#text-matching, D050#locator-reads, D050#queries, D051#policy-denials
- **[ALSO: D045#asyncexpectation-and-textmatcheroptions]** The message reads `no value (not a form control)`. #### `toHaveAttribute` Waits for the attribute to be present; with `value`, for it to match. #### `toHaveCount` Waits for an exact match count. #### `toHaveAccessibleName` Waits for an accessible name.
    term `toHaveAccessibleName` also in 5: D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions, D045#secure-fields, D045#text-matching, D050#queries
    term `toHaveAttribute` also in 5: D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions, D045#secure-fields, D045#text-matching, D051#policy-denials
    term `toHaveCount` also in 8: D014#core-concepts, D030#map-each-command, D030#rewrite-one-spec, D031#map-each-detox-call, D033#map-each-api, D035#known-device-limitations, D045#asyncexpectation-and-textmatcheroptions, D045#strictness
- **[ONLY HERE]** | [`toBeVisible`](#tobevisible-and-tobehidden) | Waits for visibility |
- **[ALSO: D045#asyncexpectation-and-textmatcheroptions]** | [`toBeHidden`](#tobevisible-and-tobehidden) | Waits for hidden or absent state |
    term `toBeHidden` also in 10: D030#map-each-command, D031#map-each-detox-call, D032#map-each-command, D033#map-each-api, D035#known-device-limitations, D045#asyncexpectation-and-textmatcheroptions, D045#strictness, D050#queries, D059#resize-inside-a-test, D060#nodes-and-refs
- **[ALSO: D045#asyncexpectation-and-textmatcheroptions]** | [`toBeAttached`](#tobeattached) | Waits for one match to exist |
    term `toBeAttached` also in 4: D033#map-each-api, D035#known-device-limitations, D045#asyncexpectation-and-textmatcheroptions, D045#strictness
- **[ONLY HERE]** | [`toBeEnabled`](#tobeenabled-and-tobedisabled) | Waits for enabled state |
    term `toBeEnabled` also in 4: D032#map-each-command, D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions, D045#soft-assertions
- **[ONLY HERE]** | [`toBeDisabled`](#tobeenabled-and-tobedisabled) | Waits for disabled state |
    term `toBeDisabled` also in 2: D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions
- **[ONLY HERE]** | [`toBeChecked`](#tobechecked-tobeselected-and-tobeexpanded) | Waits for checked state |
    term `toBeChecked` also in 7: D031#map-each-detox-call, D032#map-each-command, D033#map-each-api, D033#what-differs-on-purpose, D035#known-device-limitations, D045#asyncexpectation-and-textmatcheroptions, D045#option-validation
- **[ONLY HERE]** | [`toBeSelected`](#tobechecked-tobeselected-and-tobeexpanded) | Waits for selected state |
    term `toBeSelected` also in 4: D032#map-each-command, D033#map-each-api, D035#known-device-limitations, D045#asyncexpectation-and-textmatcheroptions
- **[ONLY HERE]** | [`toBeExpanded`](#tobechecked-tobeselected-and-tobeexpanded) | Waits for expanded state |
    term `toBeExpanded` also in 2: D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions
- **[ONLY HERE]** | [`toBeFocused`](#tobefocused) | Waits for focused state |
    term `toBeFocused` also in 3: D032#map-each-command, D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions
- **[ALSO: D045#asyncexpectation-and-textmatcheroptions]** | [`toHaveText`](#tohavetext-and-tocontaintext) | Waits for exact normalized text |
- **[ALSO: D045#asyncexpectation-and-textmatcheroptions]** | [`toContainText`](#tohavetext-and-tocontaintext) | Waits for contained normalized text |
- **[ALSO: D045#asyncexpectation-and-textmatcheroptions]** | [`toHaveValue`](#tohavevalue) | Waits for a form control's value |
    term `toHaveValue` also in 9: D030#map-each-command, D031#map-each-detox-call, D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions, D045#secure-fields, D045#text-matching, D050#locator-reads, D050#queries, D051#policy-denials
- **[ONLY HERE]** | [`toHaveAttribute`](#tohaveattribute) | Waits for an attribute |
    term `toHaveAttribute` also in 5: D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions, D045#secure-fields, D045#text-matching, D051#policy-denials
- **[ALSO: D045#asyncexpectation-and-textmatcheroptions]** | [`toHaveCount`](#tohavecount) | Waits for an exact match count |
    term `toHaveCount` also in 8: D014#core-concepts, D030#map-each-command, D030#rewrite-one-spec, D031#map-each-detox-call, D033#map-each-api, D035#known-device-limitations, D045#asyncexpectation-and-textmatcheroptions, D045#strictness
- **[ONLY HERE]** | [`toHaveAccessibleName`](#tohaveaccessiblename) | Waits for an accessible name |
    term `toHaveAccessibleName` also in 5: D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions, D045#secure-fields, D045#text-matching, D050#queries
- **[ONLY HERE]** | [`toHaveScreenshot`](#screenshot-matchers) | Compares with a stored screenshot |
- **[ONLY HERE]** | `toHaveText([...])` | The match count equals the list length, and the match at each position satisfies the entry there: a string exactly after normalization, a `RegExp` by test. An empty list holds when nothing matches |
    term `toHaveText([...])` also in 1: D050#locator-reads
- **[ALSO: D045#asyncexpectation-and-textmatcheroptions]** | `toContainText([...])` | Each entry is contained by a distinct match, in list order, as Playwright's does. Extra matches before, between, or after are fine, a repeated entry needs a match of its own, and an empty list always holds |
    term `toContainText([...])` also in 1: D033#map-each-api

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D030#map-each-command: Both list locator assertions toBeVisible, toHaveText, toContainText, toHaveCount and toHaveValue.
- D033#map-each-api: Both list locator matchers toBeVisible, toBeEnabled, toBeChecked, toHaveText, toHaveCount, toBeAttached and toBeSelected.
- D033#what-differs-on-purpose: Both state .not.toBeChecked() passes on a node with no checked state such as a button or heading.
- D033#map-each-api: Both state the Playwright matchers map the same, toBeChecked passing negated on non-checkable nodes, and toHaveText/toContainText list semantics.
- D033#what-differs-on-purpose: Both state .not.toBeChecked() passes on a button or heading and text matchers compare rendered text.
- D035#known-device-limitations: Both note toBeAttached and toHaveCount(0)/toBeHidden behaviour for matchers on devices.
- D045#strictness: Both state toBeHidden, toBeAttached({attached:false}) accept zero matches, and describe toHaveCount and list forms of toHaveText.
- D045#text-matching: Both state toHaveText/toContainText compare normalized text, ignoreCase, and toHaveValue compares as-is.
- D045#secure-fields: Both list which matchers (toHaveValue, toHaveText, toHaveAttribute, state matchers) work on secure fields.
- D045#option-validation: Both relate to options such as toBeChecked or useInnerText on toHaveText being validated.
- D045#asyncexpectation-and-textmatcheroptions: Both list the locator matchers and their options (visible, attached, enabled, checked, timeout).
- D050#queries: Both explain fieldset/legend accessible names and visible checks tied to toBeVisible and toHaveAccessibleName.
- D050#locator-reads: Both describe toHaveValue reading a checkbox/radio value like inputValue().
- D051#policy-denials: Both state toHaveValue, toHaveText, toContainText and toHaveAttribute on a secure field are POLICY_DENIED.
- D045#screenshot-matchers: Both list toHaveScreenshot as a locator matcher comparing with a stored screenshot.

## S27 · single · D045#screenshot-matchers  (expect › Reference › Screenshot matchers; page title: expect)

Regel: genau ein Abschnitt, dessen Hauptinhalt die Antwort ist; jeder Teil der Antwort muss nur hier stehen.

**Typ-Eignung:** Ziel `limitation`: „Written earlier in the run“: ohne `--update-snapshots` und immer bei `.not` besteht kein Vergleich gegen einen Screenshot, den derselbe Lauf geschrieben hat, `ASSERTION_FAILED` bis zum nächsten Lauf („same run wrote“ nur hier); oder die Fehlerfälle (`INVALID_ARGUMENT` für Playwrights `fullPage`, `animations`, `clip`; `POLICY_DENIED` nach einem Secret Fill). Vorsicht: Baselines anlegen ist schon Q002 (D058#stored-screenshots); `toHaveScreenshot`-Optionen stehen auch in D033#map-each-api, `POLICY_DENIED` nach Secret Fill in D051#screenshots-after-a-secret-fill und D051#policy-denials.

- **[ALSO: D058#visual-testing]** ### Screenshot matchers `expect(screen)` and `expect(locator)` compare against a PNG stored beside the test file, on every engine that captures pixels.
    term `expect(locator)` also in 9: D007#when-a-recording-is-written, D030#map-each-command, D032#map-each-command, D033#map-each-api, D034#map-each-webdriver-call, D042#capabilities, D045#locator-matchers, D058#visual-testing, D060#capabilities
    term `expect(screen)` also in 5: D031#map-each-detox-call, D032#map-each-command, D033#map-each-api, D058#tolerance-and-masks, D058#visual-testing
- **[ALSO: D045#asyncexpectation-and-textmatcheroptions, D045#screenexpectation-and-screenshotoptions]** The [Visual comparison](/visual-testing) guide shows the workflow. #### `toHaveScreenshot` Waits for the screen, or the one match of a locator, to look like its stored screenshot:
- **[ALSO: D045#screenexpectation-and-screenshotoptions]** `name`, or one named after the test.
- **[ONLY HERE]** Both forms take the [Screenshot options](#screenshot-options). #### Screenshot options [`ScreenshotOptions`](#screenexpectation-and-screenshotoptions) describes each option.
    term `ScreenshotOptions` also in 2: D045#asyncexpectation-and-textmatcheroptions, D045#screenexpectation-and-screenshotoptions
- **[ONLY HERE]** | [`expect(screen).toHaveScreenshot`](#tohavescreenshot) | Compares the whole screen |
    term `expect(screen).toHaveScreenshot` also in 5: D031#map-each-detox-call, D032#map-each-command, D033#map-each-api, D058#tolerance-and-masks, D058#visual-testing
- **[ONLY HERE]** | [`expect(locator).toHaveScreenshot`](#tohavescreenshot) | Compares a locator's one match |
    term `expect(locator).toHaveScreenshot` also in 1: D033#map-each-api
- **[ONLY HERE]** | Stored at | `<test file>-snapshots/<name>-<target>-<os>.png`; `.png` is added to a name without it |
- **[ONLY HERE]** | Unnamed | The test's title path, lowercase, and a count: `checkout-pays-by-card-1` |
- **[ALSO: D058#in-ci, D058#when-it-fails]** | Missing | Taken from two screenshots in a row that are the same within the tolerance, then `ASSERTION_FAILED`. Written beside the test; in CI without `--update-snapshots` only attached to the results, at `snapshots/<path in the project>` |
    term `--update-snapshots` also in 5: D033#map-each-api, D040#commands, D058#in-ci, D058#stored-screenshots, D058#when-it-fails
    term `snapshots/<path in the project>` also in 1: D058#in-ci
- **[ONLY HERE]** | Written earlier in the run | Without `--update-snapshots`, and always for `.not`, no comparison passes against a screenshot the same run wrote (a retry, a repeat, another test naming it): `ASSERTION_FAILED` until the next run. With `--update-snapshots` a positive matcher compares and may write it
    term `--update-snapshots` also in 5: D033#map-each-api, D040#commands, D058#in-ci, D058#stored-screenshots, D058#when-it-fails
- **[ONLY HERE]** | Different | Retried until one matches or the timeout; then `ASSERTION_FAILED` with `-expected`, `-actual`, and `-diff` images on the step |
    term `-actual` also in 2: D040#commands, D058#when-it-fails
    term `-diff` also in 5: D031#map-each-detox-call, D032#what-differs-on-purpose, D033#browser-timeouts-and-artifacts, D033#map-each-api, D058#when-it-fails
    term `-expected` also in 2: D040#commands, D058#when-it-fails
- **[ONLY HERE]** | `--update-snapshots`, `-u` | A missing or different stored screenshot is written from a screen that holds still, and the matcher passes |
    term `--update-snapshots` also in 5: D033#map-each-api, D040#commands, D058#in-ci, D058#stored-screenshots, D058#when-it-fails
- **[ONLY HERE]** | `.not` | Passes once the screen differs; with nothing stored it is `ASSERTION_FAILED` |
- **[ONLY HERE]** | Tolerance | Both `maxDiffPixels` and `maxDiffPixelRatio` set: the smaller wins |
    term `maxDiffPixelRatio` also in 4: D032#map-each-command, D033#map-each-api, D045#screenexpectation-and-screenshotoptions, D058#tolerance-and-masks
    term `maxDiffPixels` also in 3: D033#map-each-api, D045#screenexpectation-and-screenshotoptions, D058#tolerance-and-masks
- **[ALSO: D050#locator-actions, D053#the-browser-fixture]** | `INVALID_ARGUMENT` | Before the screen is read: a name with a path separator, an option the matcher does not take (Playwright's `fullPage`, `animations`, `clip`), a value out of range, or `expect` on a screen scoped to a frame. Compare a locator inside the frame instead |
    term `animations` also in 3: D012#ios-and-android, D033#map-each-api, D058#tolerance-and-masks
    term `clip` also in 6: D018#what-the-context-holds, D032#map-each-command, D033#map-each-api, D035#physical-devices, D042#lifecycle, D047#device
    term `fullPage` also in 1: D033#map-each-api
- **[ONLY HERE]** | `ASSERTION_FAILED` | A missing, different, or same-run stored screenshot, as in the table above |
- **[ALSO: D039#screenshot]** | `POLICY_DENIED` | A `Secret` was filled earlier, as for `app.screenshot()` |
    term `app.screenshot()` also in 4: D042#capabilities, D049#playwright-test-fixtures, D051#policy-denials, D051#screenshots-after-a-secret-fill

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D032#map-each-command: Both cover toHaveScreenshot with maxDiffPixelRatio tolerance.
- D033#map-each-api: Both cover toHaveScreenshot with threshold, maxDiffPixels, maxDiffPixelRatio, mask options and the always-viewport behaviour.
- D033#map-each-api: Both map toHaveScreenshot options (maxDiffPixels, threshold, maskColor, mask) and unsupported fullPage.
- D040#commands: Both describe -u/--update-snapshots writing missing or different stored screenshots.
- D045#locator-matchers: Both list toHaveScreenshot as a locator matcher comparing with a stored screenshot.
- D045#screenexpectation-and-screenshotoptions: Both define the screenshot options threshold, maxDiffPixels, maxDiffPixelRatio, mask, maskColor and timeout.
- D051#policy-denials: Both state toHaveScreenshot is denied after a Secret was filled.
- D051#screenshots-after-a-secret-fill: Both state toHaveScreenshot fails with POLICY_DENIED after a secret fill.
- D058#visual-testing: Both describe stored screenshot file paths and --update-snapshots writing missing screenshots.
- D058#stored-screenshots: Both give where stored screenshots live (-snapshots folder, name-target-os.png) and --update-snapshots writing missing ones.
- D058#in-ci: Both state that without --update-snapshots a CI run saves a missing screenshot in results/snapshots instead of writing into the project.
- D058#when-it-fails: Both describe a mismatch failing with -expected, -actual and -diff images and run with --update-snapshots.
- D058#tolerance-and-masks: Both give the screenshot tolerance options threshold 0.2, maxDiffPixels, maxDiffPixelRatio and maskColor #ff00ff.
- D058#stored-screenshots: Both describe toHaveScreenshot writing a missing baseline and failing, and update-snapshots rewriting differing ones.

## S28 · paraphrase · D046#exit-codes  (MCP server (e2e mcp) › Exit codes; page title: MCP server (e2e mcp))

Regel: genau ein Abschnitt; die Frage teilt kein Inhaltswort mit der Abschnittsüberschrift oder dem Seitentitel (auch keine Wortformen).

**Typ-Eignung:** Ziel `factual`: welcher Code bei welchem Ende (`0` Client trennt oder Signal, `1` unbehandelter Fehler, `2` ungültige Kommandozeile; „uncaught error“ und „The command line is invalid“ nur hier). Wortsperre: „exit(s)“, „code(s)“, „mcp“, „server“ (geprüft: „e2e“ zählt nicht als Inhaltswort). Der Abschnitt hat 105 Tokens; eine Frage reicht.

- **[ONLY HERE]** ## Exit codes Config and engine failures come back as tool errors with the same codes the CLI prints.
- **[ONLY HERE]** | `0` | The client disconnects, with or without a session open, or a signal ends it. |
- **[ONLY HERE]** | `1` | An uncaught error shuts the server down. |
- **[ONLY HERE]** | `2` | The command line is invalid. |
- **[ONLY HERE]** | The error's [category code](/reference/cli#exit-codes) | A startup failure. |

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D040#exit-codes: Both define CLI exit codes by error category (0, 1, 2, 3, 4, 130); the MCP server reuses the category code for startup failures.
- D044#exit-codes: Both relate exit codes to error class (test 1, configuration 2, infrastructure 3, interrupted 130).
- D044#runner-codes: Both state that config and engine failures carry the same runner codes and exit codes as the CLI.

## S29 · paraphrase · D040#commands  (CLI › Reference › Commands; page title: CLI)

Regel: genau ein Abschnitt; die Frage teilt kein Inhaltswort mit der Abschnittsüberschrift oder dem Seitentitel (auch keine Wortformen).

**Typ-Eignung:** Ziel `procedural`: Watch-Modus, wörtlich nur hier: „`--watch` runs the selection, prints the summary, and waits instead of exiting“, gespeicherte Testdateien oder Config lösen einen neuen Lauf aus, „Each rerun reads the project's files afresh“, „Ctrl-C or Ctrl-D interrupts the run and ends the session, from inside a `p` or `t` prompt too“. Der Abschnitt ist sehr lang (alle Befehle in einem H3); nimm einen Teil. Wortsperre: „commands“, „command“, „cli“, „reference“.

- **[ONLY HERE]** ### Commands An option with no default listed is off unless given. #### `e2e init` Scaffolds a project and adds `e2e` to `devDependencies`.
- **[ONLY HERE]** It skips existing config and test files.
- **[ONLY HERE]** **npm** **pnpm** **bun** - A flag answers its question and skips that prompt.
- **[ALSO: D040#help-and-version]** - `--engine`, `--gateway`, and `--endpoint` apply only to a new config. ##### Prompts On a terminal, the wizard opens with the e2e wordmark, written letter by letter over about a second, the way a pen writes it.
    term `--engine` also in 2: D031#migrate-detox, D032#migrate-maestro
- **[ONLY HERE]** With `--yes`, in CI, on a dumb terminal, or on a terminal under 11 rows, it prints at once.
    term `--yes` also in 7: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D037#set-up-with-your-coding-agent, D056#what-is-sent
- **[ONLY HERE]** Piped output never shows it.
- **[ONLY HERE]** For a new project, the wizard asks for:
- **[ONLY HERE]** - **The engine.** **Web** (Playwright, the default) adds `@e2e-dev/web`.
- **[ALSO: D035#set-up, D037#run-your-first-test]** **Mobile (iOS/Android)** adds `@e2e-dev/mobile`, defaults to iOS on macOS and Android elsewhere, and opens Settings.
- **[ALSO: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D036#next, D037#set-up-with-your-coding-agent, D055#subscriptions]** - **A model provider or subscription for agent steps:** Vercel AI Gateway, OpenRouter, an OpenAI-compatible endpoint, ChatGPT, GitHub Copilot, OpenCode Console, or SuperGrok.
- **[ONLY HERE]** None is for tests that use only locators.
- **[ONLY HERE]** The wizard adds the required packages and model config.
- **[ONLY HERE]** Subscription users then sign in with [`e2e login`](#e2e-login).
- **[ALSO: D043#model]** See [Models](/models) and [Subscriptions](/subscriptions).
- **[ONLY HERE]** - **Where to install the agent skill** (see [e2e guide](#e2e-guide)).
- **[ONLY HERE]** `.agents/skills/` serves Codex, Cursor, Copilot, Gemini CLI, OpenCode, and Zed; `.claude/skills/` serves Claude Code.
    term `.agents/skills/` also in 2: D013#generate-a-verification-skill-for-your-app, D013#install-the-skill
    term `.claude/skills/` also in 1: D013#install-the-skill
- **[ONLY HERE]** - **Where to register the [MCP server](/reference/mcp).** `.mcp.json` for Claude Code, `.cursor/mcp.json` for Cursor.
    term `.cursor/mcp.json` also in 2: D029#set-it-up, D046#setup
    term `.mcp.json` also in 3: D029#set-it-up, D046#reference-mcp, D046#setup
- **[ONLY HERE]** After you confirm the file changes, the wizard asks whether to install the selected dependencies.
- **[ONLY HERE]** The installer follows the project's `packageManager` field or lockfile, then the invoking package manager, then npm. ##### Files ##### Re-running init - An existing config is kept, and no packages are added for it.
- **[ONLY HERE]** - MCP registration keeps extra settings on the e2e server, such as environment variables and client timeouts, even when it repairs the launch command.
- **[ONLY HERE]** A current registration stays byte-for-byte unchanged.
- **[ONLY HERE]** - Once a skill directory exists, later runs refresh copies that differ from the installed version.
- **[ONLY HERE]** They never add a directory the project did not choose.
- **[ONLY HERE]** `--skills` and `--mcp` name the exact locations instead and leave the others as they are.
- **[ONLY HERE]** - A `.claude/skills/e2e/` copy from an earlier version becomes the symlink when it holds only the shipped files.
    term `.claude/skills/e2e/` also in 1: D013#install-the-skill
- **[ONLY HERE]** A copy with other files stays a copy and is refreshed.
- **[ONLY HERE]** - `init` never writes through a skill directory that is a symlink elsewhere, or sits under one.
- **[ONLY HERE]** `--yes` skips it with a warning naming the link and its target.
    term `--yes` also in 7: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D037#set-up-with-your-coding-agent, D056#what-is-sent
- **[ONLY HERE]** An interactive run offers to replace it with a copy, or with the link where the link goes.
- **[ONLY HERE]** - A copy with a directory where a file goes, or a file where a directory goes, is skipped with a warning naming the entry.
- **[ONLY HERE]** `init` removes nothing to repair it.
- **[ONLY HERE]** - An MCP config file reached through a symlink, or under a linked directory, is skipped with the same warning and left unchanged, so the server is not registered there.
- **[ONLY HERE]** A plain config is merged as usual. #### `e2e login` Signs in to a subscription and stores the credentials in `$XDG_CONFIG_HOME/e2e/oauth.json`, by default `~/.config/e2e/oauth.json`.
    term `$XDG_CONFIG_HOME/e2e/oauth.json` also in 1: D043#model
    term `~/.config/e2e/oauth.json` also in 1: D043#model
- **[ONLY HERE]** See [Subscriptions](/subscriptions) for the model configuration.
- **[ONLY HERE]** **npm** **pnpm** **bun** #### `e2e logout` Forgets the stored login of one provider.
    term `e2e logout` also in 4: D043#model, D044#exit-codes, D044#reference-errors, D055#sign-in-help
- **[ONLY HERE]** **npm** **pnpm** **bun** #### `e2e models` Asks the vendor which models the stored login serves and prints one line per model.
    term `e2e models` also in 5: D043#model, D044#exit-codes, D044#reference-errors, D051#outbound-connections, D055#pick-a-model
- **[ONLY HERE]** For OpenCode Console it asks with `OPENCODE_API_KEY` when set.
    term `OPENCODE_API_KEY` also in 3: D043#model, D055#ci, D055#pick-a-model
- **[ONLY HERE]** **npm** **pnpm** **bun** Each line holds:
- **[ONLY HERE]** - the id `chatgpt()`, `copilot()`, `opencodeConsole()`, or `grok()` takes; - the vendor's name for the model; - its notes: reasoning levels, vision, preview, hidden; for Copilot `not enabled` or `no chat or responses` when `copilot()` cannot call it; for OpenCode Console the plan that serves it, Zen
    term `not enabled` also in 1: D055#pick-a-model
    term `opencodeConsole()` also in 2: D043#model, D055#pick-a-model
- **[ONLY HERE]** Only a call finds out whether a Copilot account can use a listed model.
- **[ALSO: D013#install-the-skill, D015#common-errors, D036#what-fails-and-where]** See [Pick a model](/subscriptions#pick-a-model). #### `e2e guide` Prints the skill that `init` installs; `npx skills add tester-army/e2e` installs the same skill.
    term `e2e guide` also in 9: D006#what-the-agent-does, D013#install-the-skill, D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D037#set-up-with-your-coding-agent, D046#resources
    term `npx skills add tester-army/e2e` also in 4: D006#install-the-skill, D013#generate-a-verification-skill-for-your-app, D013#install-the-skill, D013#migrate-an-existing-suite
- **[(short, not compared)]** See [Coding agents](/coding-agents).
- **[ALSO: D013#let-the-agent-use-the-app, D032#port-the-config]** **npm** **pnpm** **bun** #### `e2e mcp` An MCP server on stdio that gives a coding agent a live session on the app.
- **[ALSO: D015#for-scripts-report-json, D051#sessions]** **npm** **pnpm** **bun** The [MCP server](/reference/mcp) page covers these options in full, plus the tools and the session rules. #### `e2e run` Runs the tests the config discovers and writes `report.json` under the [output directory](/reference/config#output).
- **[ALSO: D033#app-targets-and-output, D033#map-each-api, D041#e2econfig, D041#top-level, D053#options, D053#the-browser-fixture]** **npm** **pnpm** **bun** ##### Positional arguments Test files, directories, or globs relative to the project root:
- **[ONLY HERE]** - **Lines.** A line that names one member of a serial group runs the group whole.
- **[ONLY HERE]** Several lines of one file add up; the file without a line selects it whole.
- **[ONLY HERE]** When no test is declared at a named line, `NO_TESTS` names the positional and the lines the file declares tests at.
    term `NO_TESTS` also in 5: D008#sharding, D041#output, D041#top-level, D044#runner-codes, D049#functions
- **[ONLY HERE]** A positional that exists on disk as written is a path, even when it ends in `:12`.
    term `:12` also in 7: D014#run-one-test, D015#traces, D020#the-comment, D033#map-each-api, D036#ai-sdk-providers, D037#use-a-subscription-or-api-key, D049#functions
- **[ONLY HERE]** - **Globs.** Braces, character classes, and extglobs are `INVALID_GLOB` with a hint, not a pattern that matches nothing.
    term `INVALID_GLOB` also in 2: D041#top-level, D044#runner-codes
- **[ONLY HERE]** There is no expansion, so name one glob per alternative.
- **[ONLY HERE]** `./`, `..`, a trailing `/`, and an absolute path inside the project resolve as for any positional path.
    term `, a trailing ` also in 1: D046#the-catalog
- **[ONLY HERE]** An existing file or directory is selected by its path, whatever characters its name holds.
- **[ONLY HERE]** - Positionals narrow the config globs and the tag, platform, and capability filters; they never bypass them.
- **[ONLY HERE]** Names and globs are case-sensitive on every OS.
- **[ALSO: D018#what-the-context-holds, D038#action-tools, D041#output, D044#runner-codes, D046#the-catalog]** A path outside the project root is `COLLECTION_ERROR`.
- **[ONLY HERE]** - The runner imports every discovered test file, even when you select a few, so a selected test finds its session setup in another file.
- **[ONLY HERE]** Other ordinary tests stay unselected.
- **[ONLY HERE]** A collection error fails the run when it is in a selected file, or in any file of a run with no positionals.
- **[ONLY HERE]** A file the positionals left out that fails to import or register its tests is skipped with a notice.
- **[ONLY HERE]** So a half-written file elsewhere does not stop `npx e2e run tests/login.e2e.ts`.
    term `npx e2e run tests/login.e2e.ts` also in 1: D033#map-each-api
- **[ONLY HERE]** If a selected test's session then has no setup test, the error names that file as where the setup may be.
- **[ONLY HERE]** - A positional that starts with `-` and names no file is a usage error, exit 2.
- **[ONLY HERE]** `pnpm test:e2e -- --headed` produces it: the `--` reaches e2e, which would otherwise take `--headed` for a file.
- **[ONLY HERE]** The message names the direct form, `pnpm exec e2e run --headed`.
    term `pnpm exec e2e run --headed` also in 1: D015#watch-it-happen
- **[ONLY HERE]** For npm it is `npm exec -- e2e run --headed`; npm needs the separator before the binary to pass its flags through.
- **[ALSO: D015#traces, D015#watch-it-happen, D041#recording, D044#runner-codes]** - When nothing is left to run, `NO_TESTS` names the cause: no file matched the globs (with look-alikes such as `tests/login.test.ts`), a positional matched nothing (with the nearest path), a matched file registered no tests, or every test was filtered out. ##### Flags **Selection** **Execution** **O
    term `--trace` also in 6: D015#traces, D033#browser-timeouts-and-artifacts, D033#map-each-api, D041#recording, D052#options, D052#testoptions
    term `NO_TESTS` also in 5: D008#sharding, D041#output, D041#top-level, D044#runner-codes, D049#functions
- **[ONLY HERE]** A bare flag is `on`: bare `--trace` keeps a page for every test.
- **[ONLY HERE]** The value is optional and greedy:
- **[ONLY HERE]** `--trace tests/a.e2e.ts` reads the file as a mode and fails.
- **[ONLY HERE]** Write `--trace=<mode>`, or put test files before the flag.
- **[ALSO: D041#output]** The removed `--artifacts <dir>` fails with the `--output` it maps to:
    term `--artifacts <dir>` also in 1: D041#output
    term `--output` also in 6: D006#what-the-agent-does, D012#ios-and-android, D032#port-the-config, D033#map-each-api, D041#output, D051#artifacts
- **[ALSO: D041#output]** `--artifacts out/artifacts` is `--output out`, and a directory whose parent is the project root or outside it maps to `--output .e2e`.
    term `--artifacts out/artifacts` also in 1: D041#output
    term `--output .e2e` also in 1: D041#output
    term `--output out` also in 1: D041#output
- **[ALSO: D049#functions]** `--last-failed` selects the tests the previous run did not pass.
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D041#output, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
- **[ONLY HERE]** It reads them from the `report.json` this run overwrites, `<output>/report.json` (`--output`, else the config's [`output`](/reference/config#output)):
    term `--output` also in 6: D006#what-the-agent-does, D012#ios-and-android, D032#port-the-config, D033#map-each-api, D041#output, D051#artifacts
- **[ONLY HERE]** - Tests that failed, timed out, or were interrupted.
- **[ONLY HERE]** - Tests skipped because a setup, a serial predecessor, a hook, or the worker failed, or because `--max-failures` or `--max-duration` stopped the run first.
    term `--max-duration` also in 5: D008#gate-pull-requests, D020#rerunning-the-failed-tests, D033#app-targets-and-output, D041#top-level, D044#runner-codes
    term `--max-failures` also in 5: D008#gate-pull-requests, D020#rerunning-the-failed-tests, D033#app-targets-and-output, D033#map-each-api, D044#runner-codes
- **[ALSO: D020#rerunning-the-failed-tests]** - Every test a failed `beforeAll` or `afterAll` selected in its describe or file, on that target; for a setup, the tests that consume its session.
    term `afterAll` also in 10: D020#rerunning-the-failed-tests, D033#map-each-api, D044#runner-codes, D045#polling-a-value, D047#exported-types, D048#custom-reporters, D052#function-types, D052#hooks, D052#testapi, D053#types
- **[ONLY HERE]** A rerun that runs the hook again reports it again if it still fails.
- **[ONLY HERE]** A rerun that runs any test of its scope without it failing resolves it.
- **[ONLY HERE]** - A test another filter (`--grep`, `--tag`, `--target`, `--agent`, a positional) leaves out of the rerun stays owed.
    term `--agent` also in 10: D002#make-the-agent-yours, D002#one-flow-several-personas, D002#pick-an-agent-per-run, D002#pin-an-agent-in-the-suite, D006#what-the-agent-does, D019#choose-the-target-and-agent, D036#several-models-in-one-config, D041#agents, D052#options, D052#testoptions
    term `--grep` also in 5: D014#run-one-test, D033#map-each-api, D041#output, D049#functions, D051#redaction
    term `--tag` also in 7: D022#watch-a-run, D032#port-the-config, D033#map-each-api, D049#functions, D052#options, D052#testoptions, D056#what-is-sent
- **[ALSO: D048#custom-reporters]** The rerun's report carries its last result, and the hook failure whose scope holds it, under `run.carried`.
    term `run.carried` also in 1: D048#custom-reporters
- **[ONLY HERE]** The next `--last-failed` selects it again, and the [`@e2e-dev/github`](/github) page stays red until it passes (⏹️ for a test the run before interrupted).
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D041#output, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
    term `@e2e-dev/github` also in 9: D012#pull-request-comments, D020#github, D020#setup, D043#reporters, D048#built-in-reporters, D048#custom-reporters, D048#reference-reporters, D048#related, D051#outbound-connections
- **[ALSO: D020#rerunning-the-failed-tests]** The rerun's own exit code and summary count only what it ran.
- **[ALSO: D008#rerunning-failures, D015#artifacts, D041#output]** - The rerun keeps the artifacts the previous report names and writes its own under each test's `rerun-<n>/`, so no attempt overwrites an earlier one's files.
    term `rerun-<n>/` also in 3: D008#rerunning-failures, D015#artifacts, D041#output
- **[ONLY HERE]** - A test is named per target and agent.
- **[(short, not compared)]** - No report is `NO_LAST_RUN`.
    term `NO_LAST_RUN` also in 2: D041#output, D044#runner-codes
- **[ONLY HERE]** When nothing failed in the previous run, it selects nothing:
- **[ONLY HERE]** Out-of-range `--retries` and `--workers` fail with `INVALID_CONFIG` before anything starts, as the config value would.
    term `--retries` also in 2: D008#what-ci-changes, D033#map-each-api
    term `--workers` also in 2: D008#what-ci-changes, D033#map-each-api
- **[ONLY HERE]** `--target`, `--tag`, `--exclude-tag`, and `--agent` take each name once.
    term `--agent` also in 10: D002#make-the-agent-yours, D002#one-flow-several-personas, D002#pick-an-agent-per-run, D002#pin-an-agent-in-the-suite, D006#what-the-agent-does, D019#choose-the-target-and-agent, D036#several-models-in-one-config, D041#agents, D052#options, D052#testoptions
    term `--exclude-tag` also in 4: D006#repro-tests, D032#port-the-config, D033#map-each-api, D049#functions
    term `--tag` also in 7: D022#watch-a-run, D032#port-the-config, D033#map-each-api, D049#functions, D052#options, D052#testoptions, D056#what-is-sent
- **[ONLY HERE]** An empty value (`--tag ''`, or `--tag "$TAGS"` with the variable unset) is a usage error, exit 2, never a wider selection.
- **[ONLY HERE]** Filters only narrow, and each applies after the one before: positionals, then `.only`, `--tag`, `--exclude-tag`, `--grep`, `--grep-invert`, `--last-failed`, then the platform and capability rules, then `--shard`.
    term `--exclude-tag` also in 4: D006#repro-tests, D032#port-the-config, D033#map-each-api, D049#functions
    term `--grep` also in 5: D014#run-one-test, D033#map-each-api, D041#output, D049#functions, D051#redaction
    term `--grep-invert` also in 1: D033#map-each-api
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D041#output, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
    term `--shard` also in 4: D008#sharding, D032#port-the-config, D033#map-each-api, D049#functions
    term `--tag` also in 7: D022#watch-a-run, D032#port-the-config, D033#map-each-api, D049#functions, D052#options, D052#testoptions, D056#what-is-sent
    term `.only` also in 4: D008#what-ci-changes, D033#map-each-api, D041#ci, D052#members
- **[ONLY HERE]** When they leave nothing to run, `NO_TESTS` counts the tests each filter removed and names the tags and patterns.
    term `NO_TESTS` also in 5: D008#sharding, D041#output, D041#top-level, D044#runner-codes, D049#functions
- **[ONLY HERE]** It marks each tag no test declares and names the nearest declared one. ##### Debug output `--debug` appends two tables to stderr.
    term `--debug` also in 9: D001#what-a-step-costs, D002#make-the-agent-yours, D015#agent-steps, D015#artifacts, D018#what-the-context-holds, D030#map-each-command, D033#map-each-api, D043#diagnostics, D044#agenterror
- **[ONLY HERE]** Phase timings are summed across the runner and every worker.
- **[ALSO: D015#agent-steps]** The agent step table lists every agent step in execution order: its per-phase split, model calls, tokens, and cost when the provider reported one.
- **[ONLY HERE]** `cached` is the share of input tokens the provider served from its prompt cache, `-` when it reports no split.
- **[ALSO: D015#for-scripts-report-json, D051#sessions]** The report records the same per step (`model.cacheReadTokens`, `model.cacheWriteTokens`) and per run (`usage.modelCachedTokens`). ##### Output Every run that gets to its tests writes, under the [output directory](/reference/config#output) (`.e2e` by default):
- **[ALSO: D008#rerunning-failures, D033#browser-timeouts-and-artifacts]** - `report.json`, for scripts, whatever the reporters are; - the trace pages its [`trace`](/reference/config#trace) mode keeps, in each test's directory under `results/`; - the reporters' files beside the report.
- **[ALSO: D041#output]** A run that stops before its tests writes none of them and leaves the previous run's files in place.
- **[ALSO: D041#output]** That covers a config or collection error, `NO_TESTS`, `NO_LAST_RUN`, `UNSUPPORTED_ARTIFACT`, an app command that fails to start, and an interrupt.
    term `NO_LAST_RUN` also in 2: D041#output, D044#runner-codes
    term `NO_TESTS` also in 5: D008#sharding, D041#output, D041#top-level, D044#runner-codes, D049#functions
    term `UNSUPPORTED_ARTIFACT` also in 5: D015#watch-it-happen, D041#output, D041#recording, D044#runner-codes, D052#options
- **[ONLY HERE]** Its errors are on the terminal and in the exit code.
- **[ALSO: D044#runner-codes]** A `junit.xml` or `summary.md` that could not be written is a line on stderr, never a run error.
    term `summary.md` also in 8: D015#debugging, D020#the-comment, D032#port-the-config, D033#app-targets-and-output, D033#map-each-api, D041#output, D041#top-level, D048#built-in-reporters
- **[ONLY HERE]** `run.summary` in the report counts the results:
    term `run.summary` also in 2: D049#functions, D049#reference-runner
- **[ONLY HERE]** - `discovered` is every test-target pair the runner collected, and `selected` the ones this run chose.
    term `discovered` also in 5: D042#lifecycle, D046#flags, D046#tools, D049#functions, D056#what-is-sent
- **[ONLY HERE]** The left-out pairs are in `results` as `selected: false`, but in no other count.
- **[ONLY HERE]** - `passed`, `failed` (timed out included), `interrupted`, `flaky`, and `skipped` count the selected results and add up to `selected`.
    term `flaky` also in 10: D008#gate-pull-requests, D013#how-an-agent-reads-a-failure, D015#read-the-failure, D015#traces, D015#watch-it-happen, D020#rerunning-the-failed-tests, D020#the-comment, D040#exit-codes, D041#recording, D056#what-is-sent
- **[ONLY HERE]** - `interrupted` is a test the run stopped before its verdict (a signal, `--max-failures`, `--max-duration`, or a run-level error such as `MODEL_UNAVAILABLE`), never a failure.
    term `--max-duration` also in 5: D008#gate-pull-requests, D020#rerunning-the-failed-tests, D033#app-targets-and-output, D041#top-level, D044#runner-codes
    term `--max-failures` also in 5: D008#gate-pull-requests, D020#rerunning-the-failed-tests, D033#app-targets-and-output, D033#map-each-api, D044#runner-codes
    term `MODEL_UNAVAILABLE` also in 10: D007#when-a-recording-is-written, D015#common-errors, D018#what-the-executor-handles, D036#what-fails-and-where, D038#agent-act, D038#reference-agent, D041#resolution-order, D044#agenterror, D052#testfixtures, D055#pick-a-model
- **[ONLY HERE]** - `executed` is the selected results that ran at least one attempt.
    term `executed` also in 2: D041#output, D056#what-is-sent
- **[ONLY HERE]** With `--ai-trace`, the run also writes `<output>/ai-trace.json`, an AI SDK devtools database.
    term `--ai-trace` also in 6: D013#how-an-agent-reads-a-failure, D015#agent-steps, D041#output, D043#diagnostics, D051#artifacts, D051#outbound-connections
- **[ONLY HERE]** It holds one entry per model round trip: the exact prompt, tool definitions, response, usage, and provider metadata.
- **[ONLY HERE]** Observations in it are already redacted, and inline image and file bytes become byte counts.
- **[ALSO: D015#agent-steps]** Open it with [unbox-ai](https://github.com/tester-army/unbox-ai):
- **[ONLY HERE]** `npx unbox-ai runs .e2e/ai-trace.json` lists its runs.
    term `npx unbox-ai runs .e2e/ai-trace.json` also in 1: D015#agent-steps
- **[ONLY HERE]** See [Debugging a run](/debugging#agent-steps). ##### Watch mode `--watch` runs the selection, prints the summary, and waits instead of exiting.
    term `--watch` also in 2: D033#map-each-api, D056#what-is-sent
- **[ONLY HERE]** **npm** **pnpm** **bun** - A saved test file (one the config's [`tests`](/reference/config#top-level) globs match) runs again alone and whole, in place of the positionals.
- **[ONLY HERE]** - A saved source file near the tests (a helper or a fixture:
- **[ONLY HERE]** `.ts`, `.js`, or `.json` under the directories the globs name, or beside the config) or a saved config reruns the selection.
- **[ONLY HERE]** - Both keep the command line's other filters and the `p` and `t` filters.
- **[ONLY HERE]** - Changes during a run wait for it and run next, together.
- **[ONLY HERE]** During the first run only the config and its directory are watched, since the test directories come from the config.
- **[ONLY HERE]** - On a terminal the screen clears before each rerun, and a banner names the trigger.
- **[ONLY HERE]** - Each rerun reads the project's files afresh, including the helpers a test imports.
- **[ONLY HERE]** On a terminal, keys drive it as in vitest:
- **[ONLY HERE]** - During a run, any of these keys (and space or `c`) cancels it, as an interrupt would.
- **[ONLY HERE]** A second one forces it, and the session waits again.
- **[ONLY HERE]** - Ctrl-C or Ctrl-D interrupts the run and ends the session, from inside a `p` or `t` prompt too.
- **[ONLY HERE]** Escape does the same outside a prompt, and inside one only closes the prompt.
- **[ONLY HERE]** Ctrl-Z suspends the process as usual.
- **[ONLY HERE]** - Every rerun is a complete run: once the config loads, it writes `report.json` and the reporter files, and starts and stops the app command.
- **[ONLY HERE]** To keep a dev server up across reruns, start it yourself and set [`reuseExisting`](/reference/config#command) on the command.
- **[ONLY HERE]** - `--last-failed` applies to the first run only; a rerun that selects nothing passes empty.
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D041#output, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
- **[ONLY HERE]** - On quit, the exit code is that of the last run that finished.
- **[ONLY HERE]** - Without a terminal on stdin, only file changes rerun.
- **[ONLY HERE]** **Note** `--watch` is not for CI: a process that never exits on its own hangs the job, so it is refused when `CI` is set.
    term `--watch` also in 2: D033#map-each-api, D056#what-is-sent
- **[ONLY HERE]** It is also refused with `--reporter json`, and exits 2 after the first run when the config's `reporters` include `json`. ##### Signals Signals escalate. 1.
    term `--reporter json` also in 2: D015#for-scripts-report-json, D056#the-notice
- **[ONLY HERE]** The first `SIGINT` or `SIGTERM` interrupts.
    term `SIGINT` also in 1: D046#sessions
    term `SIGTERM` also in 1: D046#sessions
- **[ONLY HERE]** The running test ends `interrupted`; its `afterEach` hooks and session close run within the cleanup budget, and every worker disposes its engine.
- **[ALSO: D041#top-level]** Tests not started are skipped with cause `infrastructure-unavailable` and the reason `run interrupted before execution`.
- **[ONLY HERE]** So the report lists every planned test, and `--last-failed` reruns the interrupted and the unstarted ones.
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D041#output, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
- **[ONLY HERE]** The runner writes the report and exits 130.
- **[ONLY HERE]** An interrupt before any test starts (during collection, an engine's `prepare`, or app startup) writes no report and leaves the previous one in place. 2.
- **[(short, not compared)]** A second signal forces.
- **[ALSO: D042#artifacts, D042#lifecycle]** Workers dispose their engines at once and are killed when the cleanup budget is spent.
- **[ALSO: D041#output]** The report is still written, and so are `junit.xml` and `summary.md` when the `junit` and `markdown` reporters are on; a custom reporter's `onRunFinished` is abandoned. 3.
    term `onRunFinished` also in 2: D048#built-in-reporters, D048#custom-reporters
    term `summary.md` also in 8: D015#debugging, D020#the-comment, D032#port-the-config, D033#app-targets-and-output, D033#map-each-api, D041#output, D041#top-level, D048#built-in-reporters
- **[ONLY HERE]** A third signal exits on the spot, after killing the process groups of every app command the run started.
- **[ONLY HERE]** A process attached through `reuseExisting` is left alone.
- **[ONLY HERE]** A worker whose runner disappears disposes its engine and exits within the cleanup budget. #### `e2e explore` A run with no test file.
- **[ONLY HERE]** The agent gets a goal, plans one exploration step at a time, reports defects through its `report_finding` tool, and ends with an assessment.
    term `report_finding` also in 2: D044#runner-codes, D057#add-a-tool
- **[ALSO: D006#next]** See [Exploring without a test](/explore).
- **[ONLY HERE]** **npm** **pnpm** **bun** For `--trace` and `--video`, a bare flag is `on`, and `retain-on-failure` keeps the page or video only when the exploration did not pass.
    term `--trace` also in 6: D015#traces, D033#browser-timeouts-and-artifacts, D033#map-each-api, D041#recording, D052#options, D052#testoptions
- **[ALSO: D041#recording]** The exploration is one attempt, so a retry mode records nothing, and a plan-time notice says to pass `--trace on` (or `--video on`).
- **[ALSO: D041#recording]** Put the goal before the flag, or write `--trace=<mode>` or `--video=<mode>`. ##### Report - The run has one result, under the virtual file `explore`, titled by the goal.
    term `--video=<mode>` also in 1: D015#watch-it-happen
- **[ONLY HERE]** - The exploration opens the app first when the target declares `app.url`.
- **[ONLY HERE]** - With `--session`, the report also holds the setup test's result.
    term `--session` also in 2: D019#start-signed-in, D044#runner-codes
- **[ONLY HERE]** It lists the project's other tests as skipped with cause `filtered`, as `run` lists the tests of a file no positional named.
    term `filtered` also in 2: D049#functions, D052#members
- **[ONLY HERE]** - The exploration runs with the replay cache off and zero retries, whatever the config says.
- **[ONLY HERE]** A `--session` setup test runs as it would for `run`, with the config's agents, cache, and retries.
    term `--session` also in 2: D019#start-signed-in, D044#runner-codes
- **[ALSO: D056#what-is-sent]** - `<output>/report.json` gains `run.explore`: the goal, the budgets, why the run ended (`finished`, `step-limit`, `time`, `stuck`, or `aborted`), the assessment, the steps, and the findings.
    term `aborted` also in 6: D042#lifecycle, D044#agenterror, D044#runner-codes, D049#host, D053#the-browser-fixture, D056#what-is-sent
    term `run.explore` also in 1: D048#events
    term `step-limit` also in 1: D056#what-is-sent
    term `stuck` also in 1: D056#what-is-sent
- **[ONLY HERE]** - Artifacts go to a directory named from the goal's first words and a digest of the goal, target, and agent, such as `<output>/results/explore-check-the-cart-totals-1a2b3c4d5e6f7a8b/`.
- **[ONLY HERE]** A rerun of the same goal on the same target and agent writes to the same directory. ##### Step budgets Each step has its own budget: 40 actions and 40 model calls, unless the agent sets `maxSteps` or `maxModelCalls` (1 to 100).
    term `maxSteps` also in 9: D002#define-named-agents, D007#limits-and-gaps, D015#common-errors, D018#what-the-executor-handles, D038#agent-act, D038#budgets, D038#types, D041#agentconfig, D041#agents
- **[ONLY HERE]** A step that reaches its action or time budget is time-boxed, and its findings still count.
- **[ALSO: D019#start-an-exploration]** A failed step does not end the run.
- **[ONLY HERE]** Three failed or blocked steps in a row with no new finding do (`stuck`). ##### Findings - A finding of kind `issue` is a functional defect; a `warning` is cosmetic.
    term `issue` also in 7: D019#read-the-results, D020#the-comment, D020#when-nothing-is-posted, D025#what-does-not-work, D029#ask-the-agent, D045#value-matchers, D056#what-is-sent
    term `stuck` also in 1: D056#what-is-sent
- **[ONLY HERE]** - Severity runs from `trivial` (1) to `critical` (5).
    term `trivial` also in 1: D019#read-the-results
- **[ONLY HERE]** The report lists issues before warnings, the most severe first.
- **[ONLY HERE]** - Each finding has its location, the expected and observed behavior, the steps to reproduce, and a screenshot when capture is allowed and succeeds.
- **[ALSO: D004#the-password-is-a-handle, D018#what-the-context-holds, D019#start-signed-in, D051#policy-denials, D051#reference, D051#screenshots-after-a-secret-fill, D057#observe-from-a-tool]** After a secret fill, findings carry no screenshots; see [screenshots after a secret fill](/reference/security#screenshots-after-a-secret-fill). ##### Outcomes #### `e2e list` A dry run:
    term `e2e list` also in 4: D004#credentials, D033#map-each-api, D049#functions, D059#one-size-per-target
- **[ONLY HERE]** `list` selects tests exactly as `run` does, prints one line per test-target pair, and exits.
- **[ALSO: D049#functions]** It starts no app process, engine, or worker, and writes nothing.
- **[ONLY HERE]** **npm** **pnpm** **bun** Pairs a filter removed are not listed. [`list` from `e2e/runner`](/reference/runner) runs the same selection in process and also returns the removed pairs. #### `e2e cache` Inspects or clears the replay cache.
    term `e2e cache` also in 4: D007#inspect-the-cache, D007#next, D007#why-a-step-was-not-replayed, D043#replay-cache
    term `e2e/runner` also in 8: D044#runner-codes, D049#functions, D049#playwright-test-fixtures, D049#reference-runner, D049#types, D051#outbound-connections, D056#the-notice, D056#what-is-sent
- **[ONLY HERE]** Each subcommand loads the discovered config or `--config <path>`, reads the directory a run would, and exits 0 on an empty store.
    term `--config <path>` also in 3: D041#finding-the-config-file, D044#runner-codes, D046#flags
- **[ONLY HERE]** **npm** **pnpm** **bun** - An entry recorded before entries carried provenance prints `-` in those columns and still replays.
- **[ONLY HERE]** - A file the store cannot read (truncated, over the 1 MiB ceiling, or from a newer schema) is counted separately on stderr, treated as a miss by a run, and removed by `clear`.
- **[ONLY HERE]** - Files the runner never wrote are left alone.
- **[ONLY HERE]** **Note** These commands read the file store only.
- **[ONLY HERE]** With a custom `cache.store` they exit 2 and say so. #### `e2e feedback` Sends one report about e2e itself to the e2e team: something broke, the docs or the skill misled, or a capability is missing.
    term `cache.store` also in 8: D007#fail-on-a-stale-recording, D007#modes, D007#share-the-cache-across-checkouts, D041#cacheconfig, D043#replay-cache, D044#agenterror, D051#cache-trust, D051#reference
    term `e2e feedback` also in 4: D040#exit-codes, D051#outbound-connections, D054#what-leaves-your-computer, D056#feedback
- **[ONLY HERE]** A coding agent may send one when it hits a problem with e2e, not with the app under test.
- **[ONLY HERE]** It first shows the user the `--dry-run` output and gets their agreement.
    term `--dry-run` also in 2: D051#outbound-connections, D056#feedback
- **[ONLY HERE]** **npm** **pnpm** **bun** `--message` takes at most 2000 characters, `--command` and `--agent` 200, and `--task`, `--expected`, `--actual`, `--repro`, and `--approach` 1500.
    term `--agent` also in 10: D002#make-the-agent-yours, D002#one-flow-several-personas, D002#pick-an-agent-per-run, D002#pin-an-agent-in-the-suite, D006#what-the-agent-does, D019#choose-the-target-and-agent, D036#several-models-in-one-config, D041#agents, D052#options, D052#testoptions
    term `--repro` also in 2: D051#outbound-connections, D056#feedback
- **[ONLY HERE]** - **A bug needs `--repro`.** Without it, the command sends nothing and prints a prefilled [GitHub issue](https://github.com/tester-army/e2e/issues/new?template=bug_report.yml) instead, where the e2e team can ask for a reproduction.
    term `--repro` also in 2: D051#outbound-connections, D056#feedback
- **[ONLY HERE]** Add a minimal one and submit it yourself.
- **[ONLY HERE]** - **Outdated releases are refused.** Before sending, the command asks the npm registry for the latest e2e release.
- **[ONLY HERE]** When yours is older, it exits 2 and sends nothing, since the problem may be fixed already.
- **[ONLY HERE]** Upgrade, check that it still happens, and send it again, or pass `--allow-outdated`.
    term `--allow-outdated` also in 1: D051#outbound-connections
- **[ALSO: D056#feedback]** - **Where it goes.** One `e2e_feedback` event, to the same PostHog project as [telemetry](/telemetry#feedback), with the anonymous machine facts every telemetry event carries.
    term `e2e_feedback` also in 1: D056#feedback
- **[ALSO: D056#feedback]** - **Opting out.** Feedback is sent only when you run the command, so a saved `e2e telemetry disable` does not stop it.
    term `e2e telemetry disable` also in 3: D043#telemetry, D056#feedback, D056#opt-out
- **[ALSO: D056#feedback]** `E2E_TELEMETRY_DISABLED=1` and `DO_NOT_TRACK=1` do: with either set, the command exits 2 and sends nothing.
    term `DO_NOT_TRACK=1` also in 3: D043#telemetry, D056#feedback, D056#opt-out
    term `E2E_TELEMETRY_DISABLED=1` also in 5: D043#reference-environment, D043#telemetry, D056#feedback, D056#in-a-fleet, D056#opt-out
- **[ONLY HERE]** So a CI job or a fleet that opted out sends nothing, even when an agent runs it.
- **[ONLY HERE]** `E2E_TELEMETRY_DEBUG=1` prints the event like `--dry-run`.
    term `--dry-run` also in 2: D051#outbound-connections, D056#feedback
    term `E2E_TELEMETRY_DEBUG=1` also in 2: D043#telemetry, D056#see-what-would-be-sent
- **[ONLY HERE]** **Warning** Before sending, the value of every environment variable whose name holds `KEY`, `TOKEN`, `SECRET`, `PASS`, `_PWD`, `CREDENTIAL`, `AUTH`, `COOKIE`, or `PRIVATE` becomes `<secret:NAME>` when it is six or more characters long.
    term `<secret:NAME>` also in 1: D041#the-app-under-test
    term `AUTH` also in 6: D001#how-a-step-ends, D038#agent-act, D041#credentials, D043#model, D044#agenterror, D055#ci
    term `CREDENTIAL` also in 8: D001#how-a-step-ends, D036#ai-sdk-providers, D037#use-a-subscription-or-api-key, D038#agent-act, D041#credentials, D043#model, D044#agenterror, D055#ci
- **[ONLY HERE]** That is the minimum for a config secret; a shorter one would rewrite ordinary words.
- **[ONLY HERE]** Bearer tokens, URL credentials, private keys, JWTs, and common API key shapes become `<redacted>`.
- **[ONLY HERE]** Do not paste app data, page content, or test files. #### `e2e telemetry` Shows whether anonymous usage telemetry is on, and switches it. [Telemetry](/telemetry) lists every property sent.
    term `e2e telemetry` also in 4: D043#telemetry, D056#feedback, D056#opt-out, D056#the-notice
- **[ALSO: D056#feedback]** **npm** **pnpm** **bun** - `E2E_TELEMETRY_DISABLED=1` and `DO_NOT_TRACK=1` turn telemetry off without touching the file.
    term `DO_NOT_TRACK=1` also in 3: D043#telemetry, D056#feedback, D056#opt-out
    term `E2E_TELEMETRY_DISABLED=1` also in 5: D043#reference-environment, D043#telemetry, D056#feedback, D056#in-a-fleet, D056#opt-out
- **[ONLY HERE]** - `E2E_TELEMETRY_DEBUG=1` prints every event to stderr and sends nothing.
    term `E2E_TELEMETRY_DEBUG=1` also in 2: D043#telemetry, D056#see-what-would-be-sent
- **[ALSO: D056#the-notice]** - The first command on a machine, other than `e2e init` and `e2e telemetry`, prints a notice one time.
    term `e2e telemetry` also in 4: D043#telemetry, D056#feedback, D056#opt-out, D056#the-notice
- **[ONLY HERE]** In CI nothing is printed and no file is written.
- **[ONLY HERE]** | [`e2e init`](#e2e-init) | Scaffolds a project |
- **[ONLY HERE]** | [`e2e login`](#e2e-login) | Signs in to a model subscription |
- **[ONLY HERE]** | [`e2e logout`](#e2e-logout) | Forgets a stored login |
    term `e2e logout` also in 4: D043#model, D044#exit-codes, D044#reference-errors, D055#sign-in-help
- **[ONLY HERE]** | [`e2e models`](#e2e-models) | Lists a stored login's models |
    term `e2e models` also in 5: D043#model, D044#exit-codes, D044#reference-errors, D051#outbound-connections, D055#pick-a-model
- **[ONLY HERE]** | [`e2e guide`](#e2e-guide) | Prints the agent skill |
    term `e2e guide` also in 9: D006#what-the-agent-does, D013#install-the-skill, D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D037#set-up-with-your-coding-agent, D046#resources
- **[ONLY HERE]** | [`e2e mcp`](#e2e-mcp) | Serves live sessions over MCP |
- **[ONLY HERE]** | [`e2e run`](#e2e-run) | Runs the tests |
- **[ONLY HERE]** | [`e2e explore`](#e2e-explore) | Explores the app toward a goal |
- **[ONLY HERE]** | [`e2e list`](#e2e-list) | Prints the tests a run selects |
    term `e2e list` also in 4: D004#credentials, D033#map-each-api, D049#functions, D059#one-size-per-target
- **[ONLY HERE]** | [`e2e cache`](#e2e-cache) | Inspects or clears the replay cache |
    term `e2e cache` also in 4: D007#inspect-the-cache, D007#next, D007#why-a-step-was-not-replayed, D043#replay-cache
- **[ONLY HERE]** | [`e2e feedback`](#e2e-feedback) | Sends feedback to the e2e team |
    term `e2e feedback` also in 4: D040#exit-codes, D051#outbound-connections, D054#what-leaves-your-computer, D056#feedback
- **[ONLY HERE]** | [`e2e telemetry`](#e2e-telemetry) | Shows or switches usage telemetry |
    term `e2e telemetry` also in 4: D043#telemetry, D056#feedback, D056#opt-out, D056#the-notice
- **[ONLY HERE]** | `[directory]` | Where to scaffold; created when missing. Default: the working directory. |
- **[ONLY HERE]** | `-y`, `--yes` | Skips the prompts. Each answer not given as a flag takes its default: Web engine, Vercel AI Gateway, skill and MCP config in both locations, no install. |
    term `--yes` also in 7: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D037#set-up-with-your-coding-agent, D056#what-is-sent
- **[ALSO: D056#what-is-sent]** | `--engine <id>` | The engine for a new config: `web`, `mobile`, or `none`. Default: asked. |
- **[ALSO: D056#what-is-sent]** | `--gateway <id>` | The model gateway for agent steps in a new config: `vercel`, `openrouter`, `openai-compatible`, `chatgpt`, `copilot`, `opencode-console`, `grok`, or `none`. Default: asked. |
    term `chatgpt` also in 2: D055#set-up, D056#what-is-sent
    term `copilot` also in 6: D037#use-a-subscription-or-api-key, D043#telemetry, D055#pick-a-model, D055#set-up, D055#subscriptions, D056#what-is-sent
    term `grok` also in 5: D036#ai-sdk-providers, D037#use-a-subscription-or-api-key, D055#set-up, D056#what-is-sent, D059#protected-previews
    term `openai-compatible` also in 6: D036#ai-sdk-providers, D036#pick-a-gateway-or-a-provider, D037#use-a-subscription-or-api-key, D041#agents, D055#set-up, D056#what-is-sent
    term `opencode-console` also in 7: D037#use-a-subscription-or-api-key, D043#model, D055#pick-a-model, D055#set-up, D055#sign-in-help, D055#subscriptions, D056#what-is-sent
    term `openrouter` also in 8: D016#install-and-configure, D016#vision, D036#ai-sdk-providers, D036#pick-a-gateway-or-a-provider, D037#use-a-subscription-or-api-key, D041#agents, D043#model, D056#what-is-sent
- **[ONLY HERE]** | `--endpoint <url>` | Base URL for `--gateway openai-compatible`, and implies it. HTTPS, or HTTP on a loopback host. Default: asked; `http://127.0.0.1:11434/v1` with `--yes`. |
    term `--yes` also in 7: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D037#set-up-with-your-coding-agent, D056#what-is-sent
    term `http://127.0.0.1:11434/v1` also in 3: D036#ai-sdk-providers, D036#pick-a-gateway-or-a-provider, D037#use-a-subscription-or-api-key
- **[ONLY HERE]** | `--skills <dirs>` | Where to install the agent skill: `.agents/skills`, `.claude/skills`, or `none`. Comma-separated or repeated. Default: asked. |
    term `.agents/skills` also in 2: D013#generate-a-verification-skill-for-your-app, D013#install-the-skill
    term `.claude/skills` also in 1: D013#install-the-skill
- **[ONLY HERE]** | `--mcp <files>` | Where to register the MCP server: `.mcp.json`, `.cursor/mcp.json`, or `none`. Comma-separated or repeated. Default: asked. |
    term `.cursor/mcp.json` also in 2: D029#set-it-up, D046#setup
    term `.mcp.json` also in 3: D029#set-it-up, D046#reference-mcp, D046#setup
- **[ONLY HERE]** | `--install`, `--no-install` | Whether to install dependencies. Default: asked; `--no-install` with `--yes`. |
    term `--yes` also in 7: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D037#set-up-with-your-coding-agent, D056#what-is-sent
- **[ONLY HERE]** | 0 | The scaffold finished, or the wizard was cancelled. Cancelling leaves files untouched. |
- **[ONLY HERE]** | 2 | An unknown flag value. Exits before any write and lists the valid values. |
- **[ONLY HERE]** | 2 | An invalid `package.json`. Exits before any write. |
    term `package.json` also in 7: D007#share-the-cache-across-checkouts, D032#migrate-maestro, D034#migrate-selenium, D041#e2econfig, D041#import-resolution, D041#module-format, D041#top-level
- **[ONLY HERE]** | 2 | No terminal on stdin and stdout, and no `--yes`. The message names the flag. |
    term `--yes` also in 7: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D037#set-up-with-your-coding-agent, D056#what-is-sent
- **[ONLY HERE]** | 2 | The dependency installation failed. |
- **[ONLY HERE]** | 130 | Ctrl-C or SIGTERM while the wordmark is written, or SIGINT during the dependency installation. |
- **[ONLY HERE]** | `package.json` | Created as a private ESM package when missing; otherwise gets only the missing dependencies and scripts. Sibling packages (`@e2e-dev/web`, `@e2e-dev/mobile`) get the caret range of the version released with the CLI, or that exact version when the CLI is a prerelease. Adds a `test:
    term `package.json` also in 7: D007#share-the-cache-across-checkouts, D032#migrate-maestro, D034#migrate-selenium, D041#e2econfig, D041#import-resolution, D041#module-format, D041#top-level
- **[ONLY HERE]** | `e2e.config.ts` | One target for the selected engine, with the app in its `app`. Playwright reads `APP_URL` (default `http://localhost:3000`) into `app.url` and shows `app.command` in a comment. Mobile sets `app: { bundleId: 'Settings' }` on iOS and `com.android.settings` on Android. With a gatewa
    term `agents.default` also in 4: D036#ai-sdk-providers, D036#pick-a-gateway-or-a-provider, D037#use-a-subscription-or-api-key, D046#the-catalog
    term `app: { bundleId: 'Settings' }` also in 2: D037#run-your-first-test, D047#engine
    term `com.android.settings` also in 2: D037#run-your-first-test, D047#engine
- **[ONLY HERE]** | `tests/example.e2e.ts` | An app-open test that passes against any page, plus a commented agent test. Device setup gets a Settings check instead |
    term `tests/example.e2e.ts` also in 3: D031#migrate-detox, D032#migrate-maestro, D037#run-your-first-test
- **[ALSO: D008#gate-pull-requests, D008#mobile-jobs]** | `.gitignore` | Appends `node_modules/`, `.e2e/results/`, `.e2e/cache/`, `.e2e/sessions/`, `.e2e/report.json`, `.e2e/ai-trace.json`, `.e2e/junit.xml`, `.e2e/summary.md`, `.e2e/logs/`, and `.e2e/videos/`. Committing the cache is opt-in; see [commit the replay cache](/cache#commit-the-replay-cache) |
    term `.e2e/ai-trace.json` also in 1: D015#agent-steps
    term `.e2e/cache/` also in 6: D007#commit-the-replay-cache, D007#what-a-recording-holds, D015#traces, D041#cache, D051#artifacts, D051#cache-trust
    term `.e2e/junit.xml` also in 6: D008#upload-the-reports, D009#workflow, D010#workflow, D012#web, D032#port-the-config, D048#custom-reporters
    term `.e2e/logs/` also in 2: D041#the-app-under-test, D059#let-the-runner-start-it
    term `.e2e/report.json` also in 4: D010#workflow, D012#web, D013#how-an-agent-reads-a-failure, D015#for-scripts-report-json
    term `.e2e/results/` also in 9: D010#workflow, D013#how-an-agent-reads-a-failure, D015#artifacts, D015#read-the-failure, D032#port-the-config, D033#browser-timeouts-and-artifacts, D033#map-each-api, D041#recording, D058#when-it-fails
    term `.e2e/sessions/` also in 1: D051#sessions
    term `.e2e/summary.md` also in 5: D015#debugging, D020#the-comment, D032#port-the-config, D033#app-targets-and-output, D033#map-each-api
    term `.gitignore` also in 3: D007#commit-the-replay-cache, D041#cache, D041#output
    term `node_modules/` also in 1: D013#install-the-skill
- **[ONLY HERE]** | `.agents/skills/e2e/`, `.claude/skills/e2e/` | `SKILL.md` and one `references/<topic>.md` per `e2e guide` topic. With both chosen, the Claude Code directory is a relative symlink (`../../.agents/skills/e2e`) to the copy, the layout `npx skills add` produces |
    term `.agents/skills/e2e/` also in 1: D013#install-the-skill
    term `.claude/skills/e2e/` also in 1: D013#install-the-skill
    term `SKILL.md` also in 1: D013#install-the-skill
    term `e2e guide` also in 9: D006#what-the-agent-does, D013#install-the-skill, D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D037#set-up-with-your-coding-agent, D046#resources
    term `npx skills add` also in 4: D006#install-the-skill, D013#generate-a-verification-skill-for-your-app, D013#install-the-skill, D013#migrate-an-existing-suite
- **[ONLY HERE]** | `.mcp.json`, `.cursor/mcp.json` | Registers `e2e mcp` without changing other servers |
    term `.cursor/mcp.json` also in 2: D029#set-it-up, D046#setup
    term `.mcp.json` also in 3: D029#set-it-up, D046#reference-mcp, D046#setup
- **[ONLY HERE]** | `[provider]` | The subscription: `openai`, `github-copilot`, `opencode-console`, or `spacexai`. Default: a picker. |
    term `github-copilot` also in 3: D037#use-a-subscription-or-api-key, D055#set-up, D055#subscriptions
    term `opencode-console` also in 7: D037#use-a-subscription-or-api-key, D043#model, D055#pick-a-model, D055#set-up, D055#sign-in-help, D055#subscriptions, D056#what-is-sent
    term `spacexai` also in 3: D037#use-a-subscription-or-api-key, D055#set-up, D055#subscriptions
- **[ONLY HERE]** | `--device` | ChatGPT: shows a code to enter on another device instead of opening a browser. |
    term `--device` also in 3: D012#ios-and-android, D032#port-the-config, D055#sign-in-help
- **[ONLY HERE]** | `--from-gh` | GitHub Copilot: reuses the signed-in GitHub CLI's token. |
- **[ONLY HERE]** | `--client-id <id>` | GitHub Copilot: the client id of your GitHub OAuth App, with the device flow enabled. |
- **[ONLY HERE]** | `--enterprise-url <host>` | GitHub Copilot: the GitHub Enterprise host. |
- **[(short, not compared)]** | 1 | The sign-in failed. |
- **[(short, not compared)]** | 2 | An unknown provider. |
- **[ONLY HERE]** | 130 | The sign-in was cancelled. |
- **[ONLY HERE]** | `[provider]` | The login to forget: `openai`, `github-copilot`, `opencode-console`, or `spacexai`. Default: a picker over the stored logins. |
    term `github-copilot` also in 3: D037#use-a-subscription-or-api-key, D055#set-up, D055#subscriptions
    term `opencode-console` also in 7: D037#use-a-subscription-or-api-key, D043#model, D055#pick-a-model, D055#set-up, D055#sign-in-help, D055#subscriptions, D056#what-is-sent
    term `spacexai` also in 3: D037#use-a-subscription-or-api-key, D055#set-up, D055#subscriptions
- **[ONLY HERE]** | `[provider]` | `openai`, `github-copilot`, `opencode-console`, or `spacexai`. Default: every stored login, plus OpenCode Console when only `OPENCODE_API_KEY` is set. |
    term `OPENCODE_API_KEY` also in 3: D043#model, D055#ci, D055#pick-a-model
    term `github-copilot` also in 3: D037#use-a-subscription-or-api-key, D055#set-up, D055#subscriptions
    term `opencode-console` also in 7: D037#use-a-subscription-or-api-key, D043#model, D055#pick-a-model, D055#set-up, D055#sign-in-help, D055#subscriptions, D056#what-is-sent
    term `spacexai` also in 3: D037#use-a-subscription-or-api-key, D055#set-up, D055#subscriptions
- **[ONLY HERE]** | 1 | No credential, or none for the named provider. The message names the sign-in command. |
- **[ONLY HERE]** | 1 | One of several logins failed to list. The others still print. |
- **[(short, not compared)]** | 2 | An unknown provider. |
- **[ALSO: D046#resources]** | `[topic]` | One of `setup`, `writing-tests`, `agent`, `running`, `explore`, `debugging`, `mcp`, or `bug-bash`. Default: the overview. An unknown topic exits 2 and names the valid ones. |
    term `[topic]` also in 1: D013#install-the-skill
    term `bug-bash` also in 5: D006#what-the-agent-does, D013#generate-a-verification-skill-for-your-app, D019#next, D046#resources, D046#several-sessions
    term `writing-tests` also in 1: D046#resources
- **[ALSO: D046#flags]** | `--config <path>` | The config every session loads unless `open_session` names one. Default: the nearest `e2e.config.ts` or `e2e.config.mts`. |
    term `--config <path>` also in 3: D041#finding-the-config-file, D044#runner-codes, D046#flags
    term `e2e.config.mts` also in 8: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D041#finding-the-config-file, D044#runner-codes, D049#functions
    term `open_session` also in 8: D044#agenterror, D044#runner-codes, D046#flags, D046#sessions, D046#setup, D046#several-sessions, D046#tools, D056#what-is-sent
- **[ONLY HERE]** | `--target <name>` | The target every session opens on. Default: the only target, or the one `open_session` names. |
    term `--target <name>` also in 2: D019#choose-the-target-and-agent, D046#flags
    term `open_session` also in 8: D044#agenterror, D044#runner-codes, D046#flags, D046#sessions, D046#setup, D046#several-sessions, D046#tools, D056#what-is-sent
- **[ALSO: D046#flags]** | `--headed` | Shows the UI in sessions whose `open_session` does not set `headed`, when the engine supports it. |
    term `open_session` also in 8: D044#agenterror, D044#runner-codes, D046#flags, D046#sessions, D046#setup, D046#several-sessions, D046#tools, D056#what-is-sent
- **[ALSO: D029#run-several-agents]** | `--max-sessions <n>` | Sessions open at once, each with its own browser or device, 1 through 16. Default: 4. |
    term `--max-sessions <n>` also in 1: D046#flags
- **[ONLY HERE]** | A file path (`tests/signup.e2e.ts`) | That file. |
    term `tests/signup.e2e.ts` also in 3: D014#run-one-test, D049#functions, D049#reference-runner
- **[ONLY HERE]** | A directory (`tests/agent`, `.`) | Every discovered test file beneath it. |
    term `tests/agent` also in 1: D037#add-an-agent-step
- **[ONLY HERE]** | A bare name (`signup.e2e.ts`, `agent/signup.e2e.ts`, `signup`) | Every discovered file whose path ends with it at a segment boundary; the first two both select `tests/agent/signup.e2e.ts`. Without a `/` or `.`, it matches the file name without extensions, so `signup` selects it too. |
    term `signup` also in 3: D014#run-one-test, D049#functions, D049#reference-runner
    term `signup.e2e.ts` also in 3: D014#run-one-test, D049#functions, D049#reference-runner
- **[ONLY HERE]** | Any of these with `:line` (`tests/signup.e2e.ts:12`, `signup:12`) | Only the test declared at that line of each file it names: the line its `test(` call opens on, as an editor or a report's `source` shows it. |
    term `:line` also in 1: D049#functions
    term `tests/signup.e2e.ts:12` also in 2: D014#run-one-test, D049#functions
- **[ONLY HERE]** | A quoted glob (`'tests/**/*.smoke.e2e.ts'`) | Every discovered file it matches, in the grammar of the config `tests` globs: `*`, `?`, and a whole `**` segment. |
    term `, and a whole ` also in 2: D041#e2econfig, D041#top-level
- **[ONLY HERE]** | `--config <path>` | Explicit config path. Default: the nearest `e2e.config.ts` or `e2e.config.mts` (see [Loading](/reference/config#loading)). A missing file is `CONFIG_NOT_FOUND`. |
    term `--config <path>` also in 3: D041#finding-the-config-file, D044#runner-codes, D046#flags
    term `CONFIG_NOT_FOUND` also in 2: D044#runner-codes, D056#what-is-sent
    term `e2e.config.mts` also in 8: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D041#finding-the-config-file, D044#runner-codes, D049#functions
- **[ONLY HERE]** | `--target <ids>` | Targets by name, comma-separated or repeated. Default: every configured target. Only selected targets' app commands start. An unknown ID is `UNKNOWN_TARGET`. |
    term `UNKNOWN_TARGET` also in 2: D044#runner-codes, D049#functions
- **[ONLY HERE]** | `--tag <tags>` | Only tests with the tags, comma-separated or repeated: any of them, or every one with `--tag-mode all`. |
- **[ONLY HERE]** | `--tag-mode <mode>` | How several tags combine: `any` or `all`. Default: `any`. |
- **[ONLY HERE]** | `--exclude-tag <tags>` | Leaves out tests with any of the tags, comma-separated or repeated, whatever `--tag` or a positional selected. A serial group still runs whole when any member is selected; tag the serial `describe` to exclude the flow. |
    term `--tag` also in 7: D022#watch-a-run, D032#port-the-config, D033#map-each-api, D049#functions, D052#options, D052#testoptions, D056#what-is-sent
- **[ALSO: D033#map-each-api]** | `--grep <pattern>` | Only tests whose title matches one of the regular expressions; repeatable. The title is the describe titles and the test title joined by one space (`checkout pays`), without the file or the tags. A bare pattern is case-sensitive; `'/pattern/i'` adds flags. A pattern that does
- **[ONLY HERE]** | `--grep-invert <pattern>` | Leaves out tests whose title matches one of the regular expressions; repeatable, with the text and forms of `--grep`. With both, the run keeps what `--grep` matches minus what `--grep-invert` matches. |
    term `--grep` also in 5: D014#run-one-test, D033#map-each-api, D041#output, D049#functions, D051#redaction
    term `--grep-invert` also in 1: D033#map-each-api
- **[ALSO: D049#functions]** | `--last-failed` | Only the tests the previous run did not pass; the list after these tables says which. |
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D041#output, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
- **[ALSO: D008#sharding]** | `--shard <index/total>` | Runs one contiguous slice of the selected tests, such as `2/3`, cut after every other filter. Slices differ by at most one test. A serial group counts as one and is never split. Each shard brings only the setup tests its own tests need. Skipped tests are not cut: the shar
    term `--pass-with-no-tests` also in 3: D008#sharding, D033#map-each-api, D044#runner-codes
    term `--shard <index/total>` also in 2: D008#sharding, D032#port-the-config
    term `2/3` also in 2: D015#agent-steps, D033#rewrite-one-spec
    term `NO_TESTS` also in 5: D008#sharding, D041#output, D041#top-level, D044#runner-codes, D049#functions
- **[ONLY HERE]** | `--pass-with-no-tests` | Exits 0 instead of `NO_TESTS` when nothing is selected. |
    term `--pass-with-no-tests` also in 3: D008#sharding, D033#map-each-api, D044#runner-codes
    term `NO_TESTS` also in 5: D008#sharding, D041#output, D041#top-level, D044#runner-codes, D049#functions
- **[ONLY HERE]** | `--headed` | Visible UI when the engine supports it. |
- **[ONLY HERE]** | `--agent <names>` | Runs unpinned tests once per selected agent, comma-separated or repeated. Default: `default`. For a test with `{ agent }`, it selects the shared names when they overlap, else keeps the test's own. An unknown name is `INVALID_CONFIG`. |
    term `{ agent }` also in 6: D002#instructions-and-vocabulary, D002#pin-an-agent-in-the-suite, D014#organize-tests, D038#reference-agent, D044#reference-errors, D052#options
- **[ONLY HERE]** | `--retries <n>` | Replaces `config.retries`; an integer 0-10. Default: the config. |
    term `config.retries` also in 2: D052#options, D052#testoptions
- **[ONLY HERE]** | `--workers <n>` | Replaces `config.workers`; an integer 1-1024. Default: the config. |
    term `config.workers` also in 2: D042#engine, D042#lifecycle
- **[ONLY HERE]** | `--max-failures <n>` | Stops the run once this many tests (at least 1) have failed or timed out. Nothing more is dispatched, and tests running on other workers end `interrupted`. Tests not started, including the rest of the file whose test reached the limit, are skipped with cause `failure-limit`
    term `--max-failures <n>` also in 2: D008#gate-pull-requests, D033#app-targets-and-output
- **[ONLY HERE]** | `--max-duration <ms>` | Overrides [`maxDuration`](/reference/config#maxduration) for one run; an integer 1-2147483647. Default: the config. Exits 1, not 130. |
    term `--max-duration <ms>` also in 3: D008#gate-pull-requests, D033#app-targets-and-output, D041#top-level
    term `maxDuration` also in 6: D022#options, D022#sessions, D033#app-targets-and-output, D041#e2econfig, D041#top-level, D044#runner-codes
- **[ONLY HERE]** | `--repeat-each <n>` | Runs every selected test this many times, at least 1. Default: `1`. Each run is its own result, with `repeat` 0 through `n - 1` and its own `id`. The list reporter titles later runs `(repeat #1)`, `(repeat #2)`, and puts their artifacts under a `repeat-<n>` directory. Setup t
    term ` 0 through ` also in 5: D041#e2econfig, D041#top-level, D052#options, D052#testoptions, D053#options
    term ` and its own ` also in 2: D041#the-app-under-test, D046#several-sessions
    term `--no-cache` also in 9: D007#modes, D007#what-must-match, D007#why-a-step-was-not-replayed, D013#how-an-agent-reads-a-failure, D013#how-an-agent-writes-and-runs-a-test, D015#agent-steps, D037#add-an-agent-step, D041#cache, D043#replay-cache
    term `Repeats` also in 1: D049#functions
- **[ONLY HERE]** | `--no-cache` | Turns the replay cache off for this run, whatever `config.cache` says. |
    term `--no-cache` also in 9: D007#modes, D007#what-must-match, D007#why-a-step-was-not-replayed, D013#how-an-agent-reads-a-failure, D013#how-an-agent-writes-and-runs-a-test, D015#agent-steps, D037#add-an-agent-step, D041#cache, D043#replay-cache
- **[ALSO: D007#fail-on-a-stale-recording, D041#cache, D044#agenterror]** | `--strict-cache` | Turns on `cache.strict` for this run. A step whose recording exists but no longer replays fails with `REPLAY_STALE` instead of handing off to the agent. Retries replay too, and the run never writes the cache. See [Fail on a stale recording](/cache#fail-on-a-stale-recording). |
    term `--strict-cache` also in 4: D007#fail-on-a-stale-recording, D007#why-a-step-was-not-replayed, D041#cache, D044#agenterror
    term `REPLAY_STALE` also in 6: D007#fail-on-a-stale-recording, D007#share-the-cache-across-checkouts, D038#agent-act, D041#cache, D041#cacheconfig, D044#agenterror
    term `cache.strict` also in 4: D007#fail-on-a-stale-recording, D007#share-the-cache-across-checkouts, D007#why-a-step-was-not-replayed, D044#agenterror
- **[ONLY HERE]** | `-u`, `--update-snapshots` | Writes each stored screenshot [`toHaveScreenshot`](/reference/expect#screenshot-matchers) finds missing or different, and passes the matcher. Without it, a missing one is written and fails; in CI it is only attached to the results. |
    term `--update-snapshots` also in 5: D033#map-each-api, D045#screenshot-matchers, D058#in-ci, D058#stored-screenshots, D058#when-it-fails
- **[ONLY HERE]** | `-w`, `--watch` | Runs, then reruns when a test file or the config changes, or on a key. See [Watch mode](#watch-mode). |
    term `--watch` also in 2: D033#map-each-api, D056#what-is-sent
- **[ONLY HERE]** | `--reporter <ids>` | Replaces the built-in IDs in `config.reporters`, comma-separated: `list`, `json`, `junit`, `markdown`. Default: the config. `json` with `list` is `INVALID_CONFIG`. [Reporter objects](/reference/reporters) in the config keep running. |
- **[ALSO: D033#map-each-api]** | `--output <dir>` | The results directory for this run, over the config's [`output`](/reference/config#output): the report, the reporter files, the AI trace, `results/`, and `sessions/`. Default: the config, else `.e2e`. Resolved from the project root; a directory the run cannot own is `INVALID_CON
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D041#output, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
    term `--output <dir>` also in 1: D041#output
    term `sessions/` also in 7: D005#recording-on-the-provider, D005#write-a-provider, D022#watch-a-run, D035#hosted-devices, D041#output, D051#artifacts, D051#sessions
- **[ALSO: D007#share-the-cache-across-checkouts, D018#what-the-context-holds, D033#map-each-api, D043#replay-cache, D044#runner-codes, D053#options]** | `--cache-dir <dir>` | The replay cache directory for this run, over [`E2E_CACHE_DIR`](/reference/environment#replay-cache) and [`cache.dir`](/reference/config#cache). Default: `E2E_CACHE_DIR`, else `cache.dir`, else `.e2e/cache`. Resolved from the project root; `~` or a leading `~/` is the home di
    term ` or a leading ` also in 3: D007#share-the-cache-across-checkouts, D043#replay-cache, D053#the-browser-fixture
    term `.e2e/cache` also in 8: D007#commit-the-replay-cache, D007#modes, D007#what-a-recording-holds, D015#traces, D041#cache, D041#cacheconfig, D051#artifacts, D051#cache-trust
    term `E2E_CACHE_DIR` also in 5: D007#share-the-cache-across-checkouts, D041#cache, D041#output, D043#reference-environment, D043#replay-cache
    term `cache.dir` also in 5: D007#share-the-cache-across-checkouts, D038#types, D041#output, D043#replay-cache, D051#artifacts
    term `cache.store` also in 8: D007#fail-on-a-stale-recording, D007#modes, D007#share-the-cache-across-checkouts, D041#cacheconfig, D043#replay-cache, D044#agenterror, D051#cache-trust, D051#reference
- **[ONLY HERE]** | `--debug` | Phase timings and an agent step table on stderr after the run; see [Debug output](#debug-output). |
    term `--debug` also in 9: D001#what-a-step-costs, D002#make-the-agent-yours, D015#agent-steps, D015#artifacts, D018#what-the-context-holds, D030#map-each-command, D033#map-each-api, D043#diagnostics, D044#agenterror
- **[ONLY HERE]** | `--ai-trace` | Records every model call to `<output>/ai-trace.json`; see [Output](#output). |
    term `--ai-trace` also in 6: D013#how-an-agent-reads-a-failure, D015#agent-steps, D041#output, D043#diagnostics, D051#artifacts, D051#outbound-connections
- **[ALSO: D033#browser-timeouts-and-artifacts, D041#e2econfig, D041#recording, D052#options]** | `--trace [mode]` | Which tests keep a trace page (`<output>/results/<test>/trace.md`): `off`, `on`, `retain-on-failure`, `on-first-retry`, or `on-all-retries`. Default: the config. `--trace off` writes none for a test without its own `trace`. See [trace](/reference/config#trace). |
    term `--trace [mode]` also in 3: D033#browser-timeouts-and-artifacts, D033#map-each-api, D041#recording
    term `--trace off` also in 1: D015#traces
    term `on-all-retries` also in 5: D033#browser-timeouts-and-artifacts, D041#artifacts, D041#recording, D052#options, D056#what-is-sent
    term `on-first-retry` also in 6: D015#watch-it-happen, D033#browser-timeouts-and-artifacts, D033#defaults-that-differ, D041#recording, D052#options, D056#what-is-sent
    term `retain-on-failure` also in 9: D015#watch-it-happen, D033#browser-timeouts-and-artifacts, D033#defaults-that-differ, D041#artifacts, D041#e2econfig, D041#recording, D041#top-level, D052#options, D056#what-is-sent
- **[ALSO: D015#watch-it-happen, D041#e2econfig, D041#recording]** | `--video [mode]` | Which attempts record a video (WebM on a browser engine, MP4 on a device engine), with the modes of `--trace`. Default: the config. Only targets whose engine can record get one; the run names the others in one notice. See [video](/reference/config#video). |
    term `--trace` also in 6: D015#traces, D033#browser-timeouts-and-artifacts, D033#map-each-api, D041#recording, D052#options, D052#testoptions
    term `--video [mode]` also in 2: D033#browser-timeouts-and-artifacts, D041#recording
- **[ONLY HERE]** | `list` | Terminal progress, failures with code frames, and a run summary. On a TTY, live progress shows the current agent step, model turns, tool calls, and reasoning excerpts. Untrusted fields are capped at 8 KiB and stripped of control characters. |
- **[ONLY HERE]** | `json` | The report document to stdout, and nothing else there, so `e2e run --reporter json \| jq` works. It is the `<output>/report.json` document, described by `schema/report-v1.schema.json` in the package. The shape changes only with the `schemaVersion` field (`report-1` today). |
    term `report-1` also in 2: D044#runner-codes, D048#custom-reporters
- **[ONLY HERE]** | `junit` | `junit.xml` beside the report. One `<testsuite>` per file, one `<testcase>` per test-target pair named `title > path [target]`. A test-class error is a `<failure>`, any other an `<error>`, a skip a `<skipped>` with its reason. An interrupted test reached no verdict, so it is a `<skipped>
    term `interrupted:` also in 1: D059#let-the-runner-start-it
- **[ONLY HERE]** | `markdown` | `summary.md` beside the report: counts, cost, errors, and failure details, each naming its trace page when one was kept. Exploration runs show findings. [`@e2e-dev/github`](/github) uses this summary for pull request comments. |
    term `@e2e-dev/github` also in 9: D012#pull-request-comments, D020#github, D020#setup, D043#reporters, D048#built-in-reporters, D048#custom-reporters, D048#reference-reporters, D048#related, D051#outbound-connections
    term `summary.md` also in 8: D015#debugging, D020#the-comment, D032#port-the-config, D033#app-targets-and-output, D033#map-each-api, D041#output, D041#top-level, D048#built-in-reporters
- **[ONLY HERE]** | `a`, `enter` | every test the command line selected, with the `p` and `t` filters cleared |
- **[ONLY HERE]** | `r` | the selection again, under the `p` and `t` filters |
- **[ALSO: D049#functions]** | `f` | the tests the last run did not pass, read from its report as `--last-failed` does, wherever they are; the positionals and the `p` filter do not narrow it |
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D041#output, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
- **[ONLY HERE]** | `u` | the current selection with `--update-snapshots` |
- **[ONLY HERE]** | `p` | prompts for a positional (a file, a bare name, a glob) the next runs select with; empty clears it |
- **[ONLY HERE]** | `t` | prompts for a title pattern, as `--grep`; empty clears it |
- **[(short, not compared)]** | `h` | shows the keys |
- **[ALSO: D019#start-an-exploration]** | `[goal]` | What to explore, in a sentence. Default: `Explore the app and find bugs`. |
    term `Explore the app and find bugs` also in 1: D019#start-an-exploration
- **[ONLY HERE]** | `--config <path>` | Explicit config path, with the errors of `run`. Default: discovered. |
    term `--config <path>` also in 3: D041#finding-the-config-file, D044#runner-codes, D046#flags
- **[ONLY HERE]** | `--target <id>` | The one target to explore. Default: the first configured target; with several targets and no flag, it explores the first and says so on stderr. An unknown name is `UNKNOWN_TARGET`. |
    term `UNKNOWN_TARGET` also in 2: D044#runner-codes, D049#functions
- **[ONLY HERE]** | `--agent <name>` | The configured agent to explore as. Default: `default`. Its model, `system`, tools, and context are reused. The built-in agent replaces a hand-rolled `StepExecutor`, with a notice. An entry with no model, a custom executor's included, is `MODEL_UNAVAILABLE` before anything start
    term `--agent <name>` also in 3: D002#make-the-agent-yours, D019#choose-the-target-and-agent, D041#agents
    term `MODEL_UNAVAILABLE` also in 10: D007#when-a-recording-is-written, D015#common-errors, D018#what-the-executor-handles, D036#what-fails-and-where, D038#agent-act, D038#reference-agent, D041#resolution-order, D044#agenterror, D052#testfixtures, D055#pick-a-model
    term `StepExecutor` also in 8: D018#driving-the-page-yourself, D018#executors, D018#replace-the-executor, D018#replay-cache, D038#agent-assert, D041#agentconfig, D041#agents, D044#runner-codes
- **[ONLY HERE]** | `--session <name>` | Starts signed in. The setup test in the config's test files that declares this session runs first. The exploration restores what it saved, as a test with `{ session }` does. No other test runs. A name no setup test declares is `COLLECTION_ERROR`, naming the declared ones, befo
    term `--session <name>` also in 1: D019#start-signed-in
    term `{ session }` also in 7: D030#map-each-command, D031#map-each-detox-call, D032#what-differs-on-purpose, D033#browser-timeouts-and-artifacts, D033#what-differs-on-purpose, D034#port-the-config, D052#options
- **[ONLY HERE]** | `--max-steps <n>` | Exploration steps at most, an integer 1-12. Default: `8`. Out of range exits 2. |
    term `--max-steps <n>` also in 1: D019#if-the-run-stops-too-early
- **[ONLY HERE]** | `--timeout <ms>` | The run's wall clock, an integer 180000-900000. Default: `600000`. The last minute is kept for the closing assessment. Out of range exits 2. |
    term `--timeout <ms>` also in 1: D019#if-the-run-stops-too-early
- **[ONLY HERE]** | `--headed` | Requests visible UI when the engine supports it. |
- **[ONLY HERE]** | `--reporter <ids>` | As for `run`. Default: the resolved config value. `list` prints the exploration rows under its summary, `json` carries the record in the report, and `markdown` writes the findings to `<output>/summary.md`. |
    term `<output>/summary.md` also in 2: D041#top-level, D048#built-in-reporters
- **[ALSO: D039#screenshot]** | `--output <dir>` | As for `run`. Default: the config, else `.e2e`. A finding's evidence screenshot is an attempt artifact under `<output>/results`. |
    term `--output <dir>` also in 1: D041#output
    term `<output>/results` also in 3: D041#recording, D046#sessions, D049#session
- **[ALSO: D033#map-each-api]** | `--debug` | As for `run`: phase timings and the agent step table. |
    term `--debug` also in 9: D001#what-a-step-costs, D002#make-the-agent-yours, D015#agent-steps, D015#artifacts, D018#what-the-context-holds, D030#map-each-command, D033#map-each-api, D043#diagnostics, D044#agenterror
- **[(short, not compared)]** | `--ai-trace` | As for `run`. |
    term `--ai-trace` also in 6: D013#how-an-agent-reads-a-failure, D015#agent-steps, D041#output, D043#diagnostics, D051#artifacts, D051#outbound-connections
- **[ONLY HERE]** | `--trace [mode]` | As for `run`: a trace page of the exploration. Default: the config. |
    term `--trace [mode]` also in 3: D033#browser-timeouts-and-artifacts, D033#map-each-api, D041#recording
- **[ALSO: D041#recording]** | `--video [mode]` | As for `run`: one video of the whole exploration (WebM on a browser engine, MP4 on a device engine). Default: the config. An engine that cannot record prints a notice. |
    term `--video [mode]` also in 2: D033#browser-timeouts-and-artifacts, D041#recording
- **[ONLY HERE]** | Outcome | Run status | Exit code |
- **[ONLY HERE]** | Steps ran, no `issue` finding, and not every step was blocked | passed | 0 |
    term `issue` also in 7: D019#read-the-results, D020#the-comment, D020#when-nothing-is-posted, D025#what-does-not-work, D029#ask-the-agent, D045#value-matchers, D056#what-is-sent
- **[ONLY HERE]** | At least one `issue` finding | failed | 1 |
    term `issue` also in 7: D019#read-the-results, D020#the-comment, D020#when-nothing-is-posted, D025#what-does-not-work, D029#ask-the-agent, D045#value-matchers, D056#what-is-sent
- **[ONLY HERE]** | No step ran and nothing was found | blocked | 1 |
- **[ONLY HERE]** | Every step was blocked, with no `issue` finding | blocked | 1, 2, or 3, from the first blocker |
    term `issue` also in 7: D019#read-the-results, D020#the-comment, D020#when-nothing-is-posted, D025#what-does-not-work, D029#ask-the-agent, D045#value-matchers, D056#what-is-sent
- **[ONLY HERE]** | Config, engine, or model provider error | error | 2 or 3 |
- **[ONLY HERE]** | `[files...]` | As for [`run`](#positional-arguments). |
- **[ONLY HERE]** | `--config`, `--target`, `--tag`, `--tag-mode`, `--exclude-tag`, `--grep`, `--grep-invert`, `--last-failed`, `--shard`, `--pass-with-no-tests` | As for [`run`](#flags). `--last-failed` reads `report.json` under the config's [`output`](/reference/config#output). |
    term `--config` also in 8: D012#ios-and-android, D033#map-each-api, D041#finding-the-config-file, D044#runner-codes, D046#flags, D046#setup, D046#tools, D059#scoping-a-test-to-one-size
    term `--exclude-tag` also in 4: D006#repro-tests, D032#port-the-config, D033#map-each-api, D049#functions
    term `--grep` also in 5: D014#run-one-test, D033#map-each-api, D041#output, D049#functions, D051#redaction
    term `--grep-invert` also in 1: D033#map-each-api
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D041#output, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
    term `--pass-with-no-tests` also in 3: D008#sharding, D033#map-each-api, D044#runner-codes
    term `--shard` also in 4: D008#sharding, D032#port-the-config, D033#map-each-api, D049#functions
    term `--tag` also in 7: D022#watch-a-run, D032#port-the-config, D033#map-each-api, D049#functions, D052#options, D052#testoptions, D056#what-is-sent
    term `--tag-mode` also in 1: D049#functions
- **[ONLY HERE]** | `--reporter <id>` | `list` or `json`. Default: `list`. |
- **[ONLY HERE]** | `list` | One line per pair in selection order: `file › title [target]`, with the describe path joined by ` › ` (`tests/billing.e2e.ts › checkout › pays [web]`), then each declared tag as `#tag` (`tests/billing.e2e.ts › checkout › pays [web] #smoke #billing`). A skipped test keeps its line, with `(
    term `#tag` also in 1: D052#options
- **[ONLY HERE]** | `json` | `{ "pairs": [...] }` to stdout. Each pair carries `id`, `file`, `title`, `titlePath`, `kind` (`test` or `setup`), `tags` (the tags the test declares, `[]` when none), `source` when the declaration is known, `session` when the test consumes one, `sessions`, `serialId` when the test is in a
    term `disposition` also in 1: D049#functions
    term `serialId` also in 2: D048#events, D049#functions
    term `titlePath` also in 2: D049#functions, D049#playwright-test-fixtures
- **[ALSO: D007#inspect-the-cache]** | `e2e cache ls` | One row per entry: the test and target it was recorded for, the first 12 characters of its instruction digest, its age, and how many actions a replay would run (`(truncated)` when recording hit the action cap). Rows are grouped by test, then target, oldest first. |
    term `e2e cache ls` also in 2: D007#inspect-the-cache, D007#next
- **[ONLY HERE]** | `e2e cache stats` | The store directory, the number of readable entries, their total size, and the number of unreadable files when there are any. |
    term `e2e cache stats` also in 1: D007#inspect-the-cache
- **[ONLY HERE]** | `e2e cache clear` | Deletes every cache file, then the directory when nothing else is left in it, and reports how many files went. |
    term `e2e cache clear` also in 2: D007#inspect-the-cache, D007#why-a-step-was-not-replayed
- **[ONLY HERE]** | `--config <path>` | Explicit config path. Default: the nearest `e2e.config.ts` or `e2e.config.mts` (see [Loading](/reference/config#loading)). |
    term `--config <path>` also in 3: D041#finding-the-config-file, D044#runner-codes, D046#flags
    term `e2e.config.mts` also in 8: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D041#finding-the-config-file, D044#runner-codes, D049#functions
- **[ONLY HERE]** | `--cache-dir <dir>` | The store directory. Default: `E2E_CACHE_DIR`, else `cache.dir`, else `.e2e/cache/`. |
    term `.e2e/cache/` also in 6: D007#commit-the-replay-cache, D007#what-a-recording-holds, D015#traces, D041#cache, D051#artifacts, D051#cache-trust
    term `E2E_CACHE_DIR` also in 5: D007#share-the-cache-across-checkouts, D041#cache, D041#output, D043#reference-environment, D043#replay-cache
    term `cache.dir` also in 5: D007#share-the-cache-across-checkouts, D038#types, D041#output, D043#replay-cache, D051#artifacts
- **[ONLY HERE]** | `-m`, `--message <text>` | Required. One or two sentences on the problem. |
- **[ONLY HERE]** | `--type <type>` | `bug`, `docs`, `feature`, or `other`. Default: `other`. |
- **[ONLY HERE]** | `--task <text>` | What you were trying to do. |
- **[ONLY HERE]** | `--expected <text>` | What you expected to happen. |
- **[ONLY HERE]** | `--actual <text>` | What happened instead, with the error message. |
- **[ONLY HERE]** | `--error-code <code>` | The e2e error code involved, such as `LOCATOR_AMBIGUOUS`. |
- **[ONLY HERE]** | `--repro <text>` | For a bug: steps that reproduce it every time, without app content. |
- **[ONLY HERE]** | `--approach <text>` | What you tried, workarounds included. |
- **[ONLY HERE]** | `--command <text>` | The e2e command or API involved. |
- **[ONLY HERE]** | `--agent <text>` | The coding agent and model sending it. |
- **[ONLY HERE]** | `--allow-outdated` | Sends even when a newer e2e release exists. |
    term `--allow-outdated` also in 1: D051#outbound-connections
- **[ONLY HERE]** | `--dry-run` | Prints the event that would be sent and sends nothing. |
    term `--dry-run` also in 2: D051#outbound-connections, D056#feedback
- **[ONLY HERE]** | 0 | PostHog accepted the event, and the command printed a reference id. Also `--dry-run`, `E2E_TELEMETRY_DEBUG=1`, and `--type bug` without `--repro`: none of them send, so they exit 0 even with an opt-out variable set. The outdated-release check runs first, so an outdated install exits 2 on these
    term `--allow-outdated` also in 1: D051#outbound-connections
    term `--dry-run` also in 2: D051#outbound-connections, D056#feedback
    term `--repro` also in 2: D051#outbound-connections, D056#feedback
    term `E2E_TELEMETRY_DEBUG=1` also in 2: D043#telemetry, D056#see-what-would-be-sent
- **[ONLY HERE]** | 2 | A blank or too long text value, an outdated release without `--allow-outdated`, or `E2E_TELEMETRY_DISABLED=1` or `DO_NOT_TRACK=1` set. |
    term `--allow-outdated` also in 1: D051#outbound-connections
    term `DO_NOT_TRACK=1` also in 3: D043#telemetry, D056#feedback, D056#opt-out
    term `E2E_TELEMETRY_DISABLED=1` also in 5: D043#reference-environment, D043#telemetry, D056#feedback, D056#in-a-fleet, D056#opt-out
- **[ONLY HERE]** | 3 | PostHog did not confirm the event. The report may still have arrived, so the message names its reference id. |
- **[ONLY HERE]** | `e2e telemetry`, `e2e telemetry status` | Prints `Status: enabled`, or `Status: disabled` with the reason: the variable that is set, the saved choice, or a preferences directory that cannot be written. `status` is the default. |
    term `e2e telemetry` also in 4: D043#telemetry, D056#feedback, D056#opt-out, D056#the-notice
- **[ALSO: D043#telemetry]** | `e2e telemetry disable` | Saves the opt-out to `~/.config/e2e/telemetry.json` (`$XDG_CONFIG_HOME/e2e/` when set, `%APPDATA%\e2e\` on Windows) and prints the status. |
    term `$XDG_CONFIG_HOME/e2e/` also in 2: D043#model, D056#opt-out
    term `%APPDATA%\e2e\` also in 1: D056#opt-out
    term `e2e telemetry disable` also in 3: D043#telemetry, D056#feedback, D056#opt-out
    term `~/.config/e2e/telemetry.json` also in 1: D056#opt-out
- **[ONLY HERE]** | `e2e telemetry enable` | Saves the opt-in and prints the status. A variable set in the environment still wins, and the status says so. |
    term `e2e telemetry enable` also in 1: D056#opt-out

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D013#install-the-skill: Both say init installs SKILL.md into .agents/skills/e2e and .claude/skills/e2e (symlinked), and e2e guide prints the skill.
- D015#watch-it-happen: Both say --video [mode] chooses which attempts record a video, WebM on a browser engine and MP4 on a device engine.
- D015#agent-steps: Both describe --debug (phase timings and agent step table) and --ai-trace writing ai-trace.json, opened with unbox-ai.
- D019#start-signed-in: Both say e2e explore --session starts signed in by running only the setup test that saves the named session and restoring it.
- D033#browser-timeouts-and-artifacts: Both list the --trace [mode] values and trace.md location, and --headed.
- D033#map-each-api: Both list the CLI flags --grep, --grep-invert, --tag, --exclude-tag, --shard, --last-failed, --repeat-each, --max-failures, --update-snapshots, --trace and e2e list.
- D036#ai-sdk-providers: Both name the gateway choices vercel, openrouter and openai-compatible for the agent model.
- D037#use-a-subscription-or-api-key: Both give the npx e2e login commands for each subscription and the Copilot GitHub CLI login, and the init gateway choices.
- D037#add-an-agent-step: Both give npx e2e run, --headed and --no-cache for running a test.
- D038#agent-act: Both mention the --max-steps and --max-model-calls limits (1 to 100) and step budgets.
- D006#install-the-skill: Both describe installing the agent skill with e2e init or npx skills add.
- D007#why-a-step-was-not-replayed: Both describe --strict-cache and REPLAY_STALE, and e2e cache clear.
- D007#share-the-cache-across-checkouts: Both describe --cache-dir and E2E_CACHE_DIR.
- D007#inspect-the-cache: Both describe e2e cache ls, stats and clear.
- D008#gate-pull-requests: Both describe --max-failures and --max-duration limits and non-zero exit codes.
- D008#sharding: Both describe --shard index/total, --pass-with-no-tests and the per-shard report files.
- D008#rerunning-failures: Both describe --last-failed reading the previous report.json.
- D013#install-the-skill: Both describe e2e init installing the skill to .agents/skills and .claude/skills, with npx skills add as an alternative.
- D013#how-an-agent-reads-a-failure: Both describe --ai-trace and unbox-ai for reading an agent run.
- D015#read-the-failure: Both describe exit codes and flaky tests and the --last-failed rerun.
- D015#artifacts: Both describe results directories, --last-failed and --debug outputs.
- D015#agent-steps: Both describe --ai-trace and unbox-ai, and --debug phase timings.
- D019#explore: Both describe e2e explore running the agent against the app with a goal instead of a test file.
- D019#start-an-exploration: Both show running e2e explore with a goal.
- D019#read-the-results: Both describe exploration findings, issues and warnings with severity and the report.
- D019#start-signed-in: Both describe e2e explore --session starting signed in via a setup test.
- D019#if-the-run-stops-too-early: Both give --max-steps up to 12 and --timeout up to 900000 for explore, default 8 steps and 10 minutes.
- D019#choose-the-target-and-agent: Both say explore uses --target (first target by default) and --agent.
- D020#rerunning-the-failed-tests: Both describe --last-failed rerunning failed tests and those stopped by --max-failures or --max-duration.
- D029#set-it-up: Both describe registering the MCP server in .mcp.json.
- D032#port-the-config: Both cover --exclude-tag, --shard and --tag, and the markdown reporter's summary.md with trace pages.
- D033#map-each-api: Both list CLI flags --grep, --tag, --shard, --last-failed, --repeat-each, --max-failures, --update-snapshots, --trace, --reporter and e2e list, explore, mcp.
- D035#set-up: Both say the mobile wizard selects iOS on macOS and Android elsewhere and targets the Settings app.
- D037#set-up-with-your-coding-agent: Both describe e2e init and e2e guide for setting up with a coding agent.
- D037#run-your-first-test: Both describe the e2e init wizard choosing engine and model, writing a config and an example test.
- D037#use-a-subscription-or-api-key: Both give the npx e2e login commands per subscription and the init gateway choices.
- D040#exit-codes: Both give the CLI exit codes 0, 1, 2, 3, 4 and 130, and the precedence 130 > 4 > 3 > 2 > 1 > 0.
- D041#top-level: Both describe --max-duration, --last-failed, NO_TESTS and the markdown and junit reporter files.
- D041#output: Both describe the output directory: report.json, summary.md, junit.xml, results/ trace pages, --cache-dir and --ai-trace.
- D041#cache: Both describe --no-cache, --strict-cache and --cache-dir for the replay cache.
- D041#ci: Both describe exit codes in CI.
- D043#model: Both describe the stored login in oauth.json and that e2e login, logout and models use it.
- D043#replay-cache: Both describe --cache-dir and E2E_CACHE_DIR choosing the replay cache directory.
- D043#diagnostics: Both describe --debug and --ai-trace as flags and the init wordmark.
- D043#telemetry: Both describe E2E_TELEMETRY_DISABLED, DO_NOT_TRACK and E2E_TELEMETRY_DEBUG.
- D044#reference-errors: Both describe exit codes and login, logout and models failures.
- D044#exit-codes: Both give exit codes by error class (test 1, configuration 2, infrastructure 3, internal 4, interrupted 130) and that login, logout and models exit 1 or 130.
- D044#runner-codes: Both name runner codes such as NO_TESTS, INVALID_GLOB, UNKNOWN_TARGET, CONFIG_NOT_FOUND, NO_LAST_RUN, COLLECTION_ERROR and RUN_TIMEOUT.
- D046#flags: Both describe e2e mcp flags --config, --target, --headed and --max-sessions (default 4).
- D046#setup: Both describe registering e2e mcp in .mcp.json.
- D046#several-sessions: Both describe --max-sessions and open_session for several sessions.
- D048#built-in-reporters: Both list reporter ids and files (list, json, junit, markdown with summary.md) and --last-failed folding.
- D049#functions: Both describe run and list selection: positionals, tag, grep, last-failed, shard filters and NO_TESTS.
- D051#outbound-connections: Both describe e2e feedback, e2e models and --ai-trace network use.
- D055#subscriptions: Both give the e2e login commands for each subscription.
- D055#set-up: Both give the e2e login commands for each subscription.
- D055#pick-a-model: Both describe e2e models listing models and OPENCODE_API_KEY.
- D055#sign-in-help: Both describe Copilot --from-gh, --device and --enterprise-url, and e2e logout.
- D056#opt-out: Both describe e2e telemetry disable, E2E_TELEMETRY_DISABLED and DO_NOT_TRACK.
- D056#see-what-would-be-sent: Both say E2E_TELEMETRY_DEBUG=1 prints events and sends nothing.
- D056#what-is-sent: Both describe telemetry properties from init (engine, gateway), explore end reasons and e2e cache or telemetry commands.
- D056#feedback: Both describe e2e feedback and its dry-run.
- D056#the-notice: Both say a one-time notice is printed on the first command other than init and telemetry.
- D041#top-level: Both describe overriding retries, workers and maxDuration per run (--retries 0-10, --workers 1-1024, --max-duration) and INVALID_GLOB test globs.
- D041#output: Both describe --output overriding the output directory, the removed --artifacts flag mapping to --output, NO_LAST_RUN and gitignore entries.
- D041#recording: Both describe --trace and --video flags, their modes, bare flag meaning on, and overriding config and targets.
- D041#cache: Both describe --no-cache, --strict-cache, --cache-dir and the .gitignore entry for the cache.
- D041#commandconfig: Both mention reuseExisting on the command to keep a dev server up.
- D044#runner-codes: Both describe NO_TESTS, NO_LAST_RUN, INVALID_GLOB, UNKNOWN_TARGET and CONFIG_NOT_FOUND causes for the CLI.
- D045#screenshot-matchers: Both describe -u/--update-snapshots writing missing or different stored screenshots.
- D048#what-reporter-does-to-reporter-objects: Both state that --reporter replaces only built-in reporter IDs and configured reporter objects keep running.
- D049#functions: Both describe the list and run selection options: files, tags, grep, last-failed, shard, target, pass-with-no-tests, NO_TESTS.
- D051#outbound-connections: Both describe e2e feedback --dry-run, --allow-outdated and the npm registry check for a newer release.
- D052#hooks: Both describe tests skipped by a failed beforeAll or afterAll and afterEach hooks running on interrupt.
- D056#what-is-sent: Both mention the e2e feedback command sending an event with anonymous machine facts, and the flag names recorded.
- D058#stored-screenshots: Both describe -u/--update-snapshots writing each stored screenshot that is missing or different, and writing a missing one then failing.

## S30 · single · D051#policy-denials  (Security rules › Reference › Policy denials; page title: Security rules)

Regel: genau ein Abschnitt, dessen Hauptinhalt die Antwort ist; jeder Teil der Antwort muss nur hier stehen.

**Typ-Eignung:** Ziel `conceptual`: die Spalte „Why“ der Tabelle. Nur hier stehen z. B. „would load local or inline content“ (nur `http:`/`https:`), „Purpose must match. A generic secret fills any editable input“, „Observe in a separate call“ (mutierendes Projekt-Tool), „Only a web origin holds cookies“. Vorsicht: „Assert the outcome, not the secret“ steht auch in D054 (übersprungen, zählt aber als Duplikat), Screenshots nach Secret Fill in D051#screenshots-after-a-secret-fill.

- **[ONLY HERE]** ### Policy denials These calls fail with `POLICY_DENIED`.
- **[ALSO: D042#contributed-fixtures]** | Navigation to any scheme but `http:` and `https:`, other than `about:blank` | `file:`, `data:`, `javascript:`, and wrappers such as `view-source:file:` would load local or inline content. |
    term `about:blank` also in 7: D005#cookies, D039#open, D041#the-app-under-test, D042#contributed-fixtures, D051#navigation, D053#options, D053#the-browser-fixture
    term `data:` also in 7: D041#the-app-under-test, D042#state, D046#the-catalog, D047#device, D051#navigation, D051#site-check, D056#telemetry
    term `javascript:` also in 4: D041#the-app-under-test, D046#the-catalog, D047#device, D051#navigation
- **[ONLY HERE]** | A malformed URL | Nothing is repaired. |
- **[ONLY HERE]** | A `Secret` reaching a JSON sink | Handles carry no value, and no value may be serialized. |
- **[ALSO: D054#what-can-still-leak]** | Reading a value, text, or attribute from a secure field, with a getter or a `toHaveValue`, `toHaveText`, `toContainText`, or `toHaveAttribute` matcher | Assert the outcome, not the secret. A withheld value is redacted, not empty or absent. |
    term `toHaveAttribute` also in 5: D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions, D045#locator-matchers, D045#secure-fields, D045#text-matching
    term `toHaveValue` also in 9: D030#map-each-command, D031#map-each-detox-call, D033#map-each-api, D045#asyncexpectation-and-textmatcheroptions, D045#locator-matchers, D045#secure-fields, D045#text-matching, D050#locator-reads, D050#queries
- **[ONLY HERE]** | `type_secret` with an undeclared name | Only secrets in the step's params can be filled. |
    term `type_secret` also in 10: D001#what-the-model-may-do, D029#secrets, D035#what-differs-from-the-web, D038#action-tools, D042#capabilities, D046#sessions, D046#the-catalog, D047#agent-tools, D051#secret-fills, D060#handle-secrets
- **[ONLY HERE]** | `type_secret` into a disabled or non-editable node | Sinks are `textbox`, `searchbox`, and `combobox`. |
    term `combobox` also in 2: D050#queries, D050#types
    term `searchbox` also in 1: D050#types
    term `textbox` also in 8: D015#traces, D033#map-each-api, D035#write-a-device-test, D047#device, D047#engine, D050#locator-actions, D050#queries, D050#types
    term `type_secret` also in 10: D001#what-the-model-may-do, D029#secrets, D035#what-differs-from-the-web, D038#action-tools, D042#capabilities, D046#sessions, D046#the-catalog, D047#agent-tools, D051#secret-fills, D060#handle-secrets
- **[ONLY HERE]** | A password into a field that isn't a password field | Purpose must match. A generic secret fills any editable input. |
- **[ONLY HERE]** | A mutating project tool requesting an observation | Observe in a separate call. |
- **[ONLY HERE]** | `vision: 'only'` when pixels are withheld | There is nothing to fall back to. |
    term `vision: 'only'` also in 4: D001#what-the-model-sees, D014#assertions, D016#vision, D038#vision
- **[ONLY HERE]** | `browser.setCookies` with a cookie URL that isn't `http:` or `https:` | Only a web origin holds cookies. |
    term `browser.setCookies` also in 9: D005#cookies, D025#what-does-not-work, D025#what-works, D030#map-each-command, D033#browser-timeouts-and-artifacts, D033#map-each-api, D034#map-each-webdriver-call, D051#screenshots-after-a-secret-fill, D053#the-browser-fixture
- **[ALSO: D004#the-password-is-a-handle, D019#start-signed-in, D040#commands, D041#artifacts, D051#screenshots-after-a-secret-fill]** | `app.screenshot()` or `toHaveScreenshot()` after a secret fill | See [Screenshots after a secret fill](#screenshots-after-a-secret-fill). |
    term `app.screenshot()` also in 4: D042#capabilities, D045#screenshot-matchers, D049#playwright-test-fixtures, D051#screenshots-after-a-secret-fill
    term `toHaveScreenshot()` also in 3: D033#map-each-api, D045#screenshot-matchers, D051#screenshots-after-a-secret-fill
- **[ALSO: D018#what-the-context-holds]** | `toHaveScreenshot()` when the engine can't prove every secure field is masked | The screenshot isn't kept. |
    term `toHaveScreenshot()` also in 3: D033#map-each-api, D045#screenshot-matchers, D051#screenshots-after-a-secret-fill
- **[ALSO: D038#action-tools, D046#the-catalog]** | An agent, executor, or MCP `upload` of a file outside the project root, a hidden file, or a file under a hidden directory | Only project files can leave the computer through a form. |
- **[ALSO: D046#the-catalog, D051#screenshots-after-a-secret-fill]** | An `act` or `vision: true` step whose semantic capture times out after a secret fill | It can't fall back to a screenshot. |

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D045#locator-matchers: Both state toHaveValue, toHaveText, toContainText and toHaveAttribute on a secure field are POLICY_DENIED.
- D045#screenshot-matchers: Both state toHaveScreenshot is denied after a Secret was filled.
- D001#what-the-model-may-do: Both describe type_secret limited to declared secrets with the runner checking the target field.
- D005#cookies: Both say a cookie URL with a scheme other than http or https is POLICY_DENIED.
- D016#how-text-gets-typed: Both say only typeSecret fills a secret and password fields never reach the text model.
- D018#what-the-context-holds: Both say upload refuses a path outside the project root or a hidden one with POLICY_DENIED.
- D038#agent-act: Both say the runner checks the model-picked field is an enabled editable input and a password field for a password.
- D038#action-tools: Both say upload refuses a file outside the project root, a hidden file or a file under a hidden directory with POLICY_DENIED.
- D038#vision: Both say pixels are withheld, so vision only has nothing to fall back to, after a secret fill (PIXEL_TAINTED).
- D039#open: Both say a URL whose scheme is not http or https (about:blank allowed) is POLICY_DENIED.
- D039#screenshot: Both say app.screenshot is POLICY_DENIED when a Secret was filled earlier.
- D041#the-app-under-test: Both say only http(s) URLs and about:blank may be opened, and file:, data:, javascript:, view-source: are refused.
- D041#secretconfig: Both say a password secret goes only into a password field while a generic secret fills any editable input.
- D042#contributed-fixtures: Both say app.resolveUrl rejects any scheme but http and https with POLICY_DENIED.
- D045#secure-fields: Both say reading value, text or attribute of a secure field via getters or matchers is POLICY_DENIED.
- D046#the-catalog: Both say upload refuses paths outside the project, hidden files and hidden directories with POLICY_DENIED.
- D047#device: Both list file:, data:, javascript:, view-source: links as POLICY_DENIED for device links.
- D050#locator-reads: Both say textContent, inputValue and getAttribute on a secure field throw POLICY_DENIED.
- D051#navigation: Both list navigation schemes other than http, https and about:blank (file, data, javascript, view-source) as denied.
- D051#secret-fills: Both state type_secret checks: declared secret, editable input, and a password goes only into a password field.
- D051#screenshots-after-a-secret-fill: Both say app.screenshot() and toHaveScreenshot() fail with POLICY_DENIED after a secret fill.
- D053#the-browser-fixture: Both state a forbidden URL scheme in goto or a cookie URL is POLICY_DENIED.
- D058#tolerance-and-masks: Both say toHaveScreenshot fails with POLICY_DENIED after a test fills a secret.

## S31 · single · D043#reporters  (Environment variables › Reference › Reporters; page title: Environment variables)

Regel: genau ein Abschnitt, dessen Hauptinhalt die Antwort ist; jeder Teil der Antwort muss nur hier stehen.

**Typ-Eignung:** Ziel `procedural`: was ein Lauf in GitHub Actions braucht, damit `@e2e-dev/github` einen Kommentar postet (`GITHUB_ACTIONS`, `GITHUB_TOKEN` oder `GH_TOKEN`, „the first one set wins“, nur hier; ohne Token wird trotzdem die Job-Summary geschrieben). Alternative `conceptual`: Workflow und Job „join the marker a rerun finds its own comment by“ (nur hier). Vorsicht: der read-only Token eines Forks steht in D020#when-nothing-is-posted.

- **[ONLY HERE]** ### Reporters `@e2e-dev/github` reads the variables GitHub Actions sets, when a run finishes:
    term `@e2e-dev/github` also in 9: D012#pull-request-comments, D020#github, D020#setup, D040#commands, D048#built-in-reporters, D048#custom-reporters, D048#reference-reporters, D048#related, D051#outbound-connections
- **[(short, not compared)]** | Variable | Example | Reading | Effect |
- **[ONLY HERE]** | `GITHUB_ACTIONS` | `GITHUB_ACTIONS=true` | value | Without it the reporter posts nothing and says so |
    term `GITHUB_ACTIONS` also in 1: D043#telemetry
- **[ONLY HERE]** | `GITHUB_REPOSITORY`, `GITHUB_RUN_ID`, `GITHUB_EVENT_NAME`, `GITHUB_WORKFLOW`, `GITHUB_JOB` | `GITHUB_REPOSITORY=acme/shop` | value | Always set by the runner. A missing one fails the reporter, naming the variable. The repository and run id build the artifacts link. The event name shows in the "not
- **[ONLY HERE]** | `GITHUB_TOKEN`, `GH_TOKEN` | `GITHUB_TOKEN=<token>` | value | Posts the comment; the first one set wins. Unset, the job summary is still written. A fork's `pull_request` token is read-only and cannot post; see [When nothing is posted](/github#when-nothing-is-posted) |
    term `GH_TOKEN` also in 1: D020#when-nothing-is-posted
    term `GITHUB_TOKEN` also in 5: D012#pull-request-comments, D020#rerunning-the-failed-tests, D020#setup, D020#when-nothing-is-posted, D043#telemetry
    term `pull_request` also in 7: D009#workflow, D010#workflow, D011#workflow, D012#ios-and-android, D012#pull-request-comments, D012#web, D020#when-nothing-is-posted
- **[ONLY HERE]** | `GITHUB_EVENT_PATH`, `GITHUB_REF` | `GITHUB_REF=refs/pull/42/merge` | value | The pull request number and head commit from the event payload, or the number from `refs/pull/N/merge` |
    term `GITHUB_REF` also in 1: D043#diagnostics
- **[ONLY HERE]** | `GITHUB_SHA` | `GITHUB_SHA=<commit>` | value | The commit source links point at when the event is not about a pull request |
    term `GITHUB_SHA` also in 1: D043#diagnostics
- **[ONLY HERE]** | `GITHUB_WORKSPACE` | `GITHUB_WORKSPACE=/home/runner/work/shop/shop` | value | The checkout root. Source links add the project's path inside it, so a suite in a subdirectory links to the right file |
    term `GITHUB_WORKSPACE` also in 1: D020#setup
- **[ONLY HERE]** | `GITHUB_SERVER_URL`, `GITHUB_API_URL` | `GITHUB_SERVER_URL=https://github.example.com` | value | The GitHub host, for Enterprise Server. Default `https://github.com` and `https://api.github.com` |
    term `GITHUB_API_URL` also in 1: D020#when-nothing-is-posted
    term `GITHUB_SERVER_URL` also in 1: D020#when-nothing-is-posted
- **[ONLY HERE]** | `GITHUB_STEP_SUMMARY` | `GITHUB_STEP_SUMMARY=<file>` | value | The job summary file the comment text is appended to |

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D012#pull-request-comments: Both state the reporter needs GITHUB_TOKEN and a fork's pull_request token is read-only so nothing is posted.
- D020#setup: Both describe GITHUB_TOKEN and GITHUB_WORKSPACE for the GitHub reporter and source links.
- D020#when-nothing-is-posted: Both describe GITHUB_TOKEN/GH_TOKEN, read-only fork tokens, job summary fallback and GITHUB_SERVER_URL for Enterprise.

## S32 · paraphrase · D041#recording  (E2EConfig › Reference › Recording; page title: E2EConfig)

Regel: genau ein Abschnitt; die Frage teilt kein Inhaltswort mit der Abschnittsüberschrift oder dem Seitentitel (auch keine Wortformen).

**Typ-Eignung:** Ziel `comparative`: zwei benannte Modi, z. B. `retain-on-failure` („every attempt, keeping those that did not pass“, nur hier) gegen `on-first-retry` (nur der erste Retry). `on-first-retry` steht auch in D015#watch-it-happen (CI-Empfehlung), D033 und D052#options; nimm den Vergleich aus der Modustabelle. Wortsperre: „recording“, „record“, „e2econfig“, „reference“; „video“ und „trace“ sind erlaubt.

- **[ONLY HERE]** ### Recording `trace` and `video` choose what is recorded, with one set of modes.
- **[ONLY HERE]** The names are Playwright's `use.trace` and `use.video` modes.
    term `use.trace` also in 1: D033#browser-timeouts-and-artifacts
    term `use.video` also in 1: D033#browser-timeouts-and-artifacts
- **[ONLY HERE]** Under a retry mode, a test with `retries: 0` records nothing, and neither does a failure the runner does not retry, such as `LAUNCH_TIMEOUT`.
    term `LAUNCH_TIMEOUT` also in 2: D035#troubleshooting, D044#runner-codes
- **[ONLY HERE]** When such a test runs, the run prints one notice per kind at plan time: no traces (or videos) will be recorded for it.
- **[ONLY HERE]** Four places set a mode, lowest first.
- **[ONLY HERE]** Each replaces the one before it, for `trace` and `video` alike: 1.
- **[ALSO: D033#browser-timeouts-and-artifacts]** `trace` or `video` at the top of the config. 2.
- **[ONLY HERE]** A target's `trace` or `video`. 3.
- **[ALSO: D040#commands, D041#output]** `--trace [mode]` or `--video [mode]` on [`e2e run`](/reference/cli#e2e-run), over the config and every target.
    term `--trace [mode]` also in 3: D033#browser-timeouts-and-artifacts, D033#map-each-api, D040#commands
    term `--video [mode]` also in 2: D033#browser-timeouts-and-artifacts, D040#commands
- **[ONLY HERE]** A bare flag is `on`. 4.
- **[ALSO: D040#commands]** A test's or describe's own [`trace` or `video` option](/reference/test#options), innermost wins:
- **[(short, not compared)]** `test('checkout', { video: 'on' }, ...)`.
    term `test('checkout', { video: 'on' }, ...)` also in 1: D015#watch-it-happen
- **[ONLY HERE]** - A serial group records as one unit, so its members cannot set `trace` or `video` (a `COLLECTION_ERROR`, like `retries`).
- **[ALSO: D052#options]** The value on the serial `describe`, or on a group around it, applies to every member.
- **[ALSO: D040#commands]** - `e2e explore` is one attempt and uses the target's mode, `--trace` and `--video` included, so a retry mode records nothing there.
    term `--trace` also in 6: D015#traces, D033#browser-timeouts-and-artifacts, D033#map-each-api, D040#commands, D052#options, D052#testoptions
- **[ALSO: D041#output]** - An `e2e mcp` session writes no trace and never records video from the configured mode.
- **[ONLY HERE]** Its recordings are the ones `start_recording` and `stop_recording` make.
    term `start_recording` also in 5: D029#secrets, D044#runner-codes, D046#the-catalog, D051#artifacts, D057#add-a-tool
    term `stop_recording` also in 3: D044#runner-codes, D046#the-catalog, D057#add-a-tool
- **[ONLY HERE]** - `trace` and `video`, at the top or on a target, enter neither the config digest nor a replay's [cache key](/cache#what-must-match).
- **[ONLY HERE]** Turning one on or off never invalidates cached replays.
- **[ALSO: D042#capabilities]** **Note** The old trace spellings fail with `INVALID_CONFIG` naming the mode they meant, wherever a mode goes (the config, a target, a test, `--trace`):
    term `--trace` also in 6: D015#traces, D033#browser-timeouts-and-artifacts, D033#map-each-api, D040#commands, D052#options, D052#testoptions
- **[ALSO: D040#commands, D041#e2econfig]** `'all'` and `{ record: 'all' }` are `'on'`, and `'retries'` and `{ record: 'retries' }` are `'on-all-retries'`. #### `trace` Which tests keep a trace page.
    term `'all'` also in 1: D049#functions
    term `'on'` also in 4: D015#watch-it-happen, D032#map-each-command, D033#browser-timeouts-and-artifacts, D052#options
    term `'on-all-retries'` also in 2: D033#browser-timeouts-and-artifacts, D041#artifacts
    term `'retries'` also in 1: D041#artifacts
- **[ONLY HERE]** - The default is the same locally and in CI.
- **[ALSO: D013#how-an-agent-reads-a-failure]** - A trace page is markdown, `trace.md` in the test's directory under `<output>/results/`, such as `.e2e/results/checkout-applies-the-coupon-1a2b3c4d5e6f7a8b/trace.md`: every step with what it did, the cache's decisions, what the app logged, and the screen at failure.
    term `<output>/results/` also in 3: D040#commands, D046#sessions, D049#session
- **[ONLY HERE]** - It works on every engine. [Debugging](/debugging#traces) shows one. #### `video` Which attempts record a video.
- **[ALSO: D040#commands]** - Where the mode is set decides what an engine that cannot record does.
- **[ONLY HERE]** See [Engines that cannot record](#engines-that-cannot-record).
- **[ONLY HERE]** - A video costs CPU and holds what the screen showed, secrets included, so it is always asked for. #### Engines that cannot record Before any test starts, the run grades every target.
- **[ALSO: D040#commands]** Where a `video` mode was set decides what an engine that cannot record video does:
- **[ALSO: D015#watch-it-happen, D033#browser-timeouts-and-artifacts, D040#commands]** - Set at the top of the config or with `--video`: the mode applies to the targets whose engine can record it.
- **[ONLY HERE]** The run prints one notice at plan time naming the targets that cannot, and runs them without video.
- **[ALSO: D044#runner-codes]** - Set on a target, or on a test that will run on that target: the mode is required.
- **[ONLY HERE]** A target whose engine cannot record it fails the run with `UNSUPPORTED_ARTIFACT`, naming the target and, for a test's, the test.
    term `UNSUPPORTED_ARTIFACT` also in 5: D015#watch-it-happen, D040#commands, D041#output, D044#runner-codes, D052#options
- **[ONLY HERE]** Only a mode that records on some attempt counts: a run whose tests all resolve to `off`, or to a retry mode with `retries: 0`, asks nothing of the engine. #### What a video writes - Each segment carries `startedAt`, so `step.startedAt - artifact.startedAt` is a step's offset into it.
    term `startedAt` also in 4: D005#recording-on-the-provider, D015#watch-it-happen, D041#artifactsconfig, D042#artifacts
- **[ONLY HERE]** - A recording masks nothing and is recorded with `redaction: 'incomplete'`.
    term `redaction: 'incomplete'` also in 2: D041#artifactsconfig, D042#artifacts
- **[ONLY HERE]** **Note** Under `retain-on-failure` a link is left out of the report of a passed attempt, but the service still holds the recording.
    term `retain-on-failure` also in 9: D015#watch-it-happen, D033#browser-timeouts-and-artifacts, D033#defaults-that-differ, D040#commands, D041#artifacts, D041#e2econfig, D041#top-level, D052#options, D056#what-is-sent
- **[(short, not compared)]** | [`trace`](#trace) | `RecordingMode` | `'retain-on-failure'` |
    term `'retain-on-failure'` also in 3: D033#browser-timeouts-and-artifacts, D041#top-level, D052#options
    term `RecordingMode` also in 6: D041#e2econfig, D041#target, D041#targets, D041#top-level, D052#options, D052#testoptions
- **[(short, not compared)]** | [`video`](#video) | `RecordingMode` | `'off'` |
    term `'off'` also in 7: D007#modes, D018#driving-the-page-yourself, D018#replace-the-executor, D018#replay-cache, D033#browser-timeouts-and-artifacts, D041#cache, D041#top-level
    term `RecordingMode` also in 6: D041#e2econfig, D041#target, D041#targets, D041#top-level, D052#options, D052#testoptions
- **[(short, not compared)]** | Mode | Trace page | Video |
- **[ONLY HERE]** | `on` | every test, passing ones included | every attempt |
- **[ALSO: D013#how-an-agent-reads-a-failure]** | `retain-on-failure` | each failed, timed-out, interrupted, or flaky test | every attempt, keeping those that did not pass |
    term `retain-on-failure` also in 9: D015#watch-it-happen, D033#browser-timeouts-and-artifacts, D033#defaults-that-differ, D040#commands, D041#artifacts, D041#e2econfig, D041#top-level, D052#options, D056#what-is-sent
- **[ONLY HERE]** | `on-first-retry` | each test whose first retry ran | the first retry only, the second attempt |
    term `on-first-retry` also in 6: D015#watch-it-happen, D033#browser-timeouts-and-artifacts, D033#defaults-that-differ, D040#commands, D052#options, D056#what-is-sent
- **[ONLY HERE]** | `on-all-retries` | each test that was retried | every attempt after the first |
    term `on-all-retries` also in 5: D033#browser-timeouts-and-artifacts, D040#commands, D041#artifacts, D052#options, D056#what-is-sent
- **[ALSO: D005#download-a-file]** | Recorder | Files under the attempt's artifact directory |
- **[ALSO: D042#artifacts]** | Browser engine, Playwright screencast | `video/video.webm`, one segment per page the attempt showed, later ones as `video/video-part<n>.webm`. [`web({ screencast })`](/reference/web#options) sets the frame size and quality |
- **[(short, not compared)]** | Mobile engine, agent-device | `video/video.mp4` |
    term `video/video.mp4` also in 3: D022#recordings, D026#choose-device-options, D047#engine
- **[ALSO: D035#hosted-devices, D041#artifacts]** | A provider's own recording ([`BrowserProvider.record`](/browser#recording-on-the-provider), [`DeviceProvider.record`](/mobile#hosted-devices)) | the file the provider wrote, as `video/<file>`: Kernel's is `video/replay.mp4`. Or a link to a recording the service keeps, recorded with `url` in place
    term `BrowserProvider.record` also in 2: D042#artifacts, D053#weboptions
    term `DeviceProvider.record` also in 1: D042#artifacts
    term `video/<file>` also in 3: D005#recording-on-the-provider, D035#hosted-devices, D042#artifacts
    term `video/replay.mp4` also in 1: D024#recordings

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D015#watch-it-happen: Both explain the video recording modes, their precedence (config, target, --video, test option), UNSUPPORTED_ARTIFACT, and using startedAt offsets.
- D032#map-each-command: Both say a test option video: 'on' records that test.
- D033#browser-timeouts-and-artifacts: Both describe the trace and video modes and that a trace page is markdown trace.md under the test's results directory.
- D033#map-each-api: Both describe trace and video modes and the trace.md page.
- D035#hosted-devices: Both describe a provider's own recording through DeviceProvider.record.
- D041#artifacts: Both say trace and video choose the recordings and describe a provider's own recording handled as a link.
- D005#recording-on-the-provider: Both describe a provider's own recording stored as video/<file> or a link, in place of the screencast.
- D008#upload-the-reports: Both say results/ holds a video per target whose engine can record when --video is used.
- D015#watch-it-happen: Both describe --video with optional recording mode and the WebM/MP4 files written per attempt.
- D022#recordings: Both state mobile recordings go through agent-device to video/video.mp4.
- D024#recordings: Both state a Kernel provider recording is saved as video/replay.mp4.
- D033#browser-timeouts-and-artifacts: Both list the trace and video modes (off, on, retain-on-failure, on-first-retry, on-all-retries) and where they can be set.
- D033#defaults-that-differ: Both give the default trace mode as retain-on-failure.
- D035#what-differs-from-the-web: Both state --video writes WebM on web and MP4 on mobile devices or a provider's recording.
- D040#commands: Both describe --trace and --video flags, their modes, bare flag meaning on, and overriding config and targets.
- D041#top-level: Both list the trace and video options with defaults retain-on-failure and off.
- D041#artifacts: Both describe provider-hosted recordings handed over as links, and trace and video choosing the recordings.
- D041#target: Both say a target's trace and video replace the config's trace and video.
- D041#artifactsconfig: Both state a recording masks nothing so a provider link is incomplete, and carry startedAt for segments.
- D042#capabilities: Both state a video mode on an engine without video recording prints a notice and records no video.
- D042#artifacts: Both describe video segments with startedAt and incomplete redaction.
- D044#runner-codes: Both state UNSUPPORTED_ARTIFACT when a target's engine cannot record a requested video mode.
- D046#the-catalog: Both describe e2e mcp start_recording and stop_recording as the way an MCP session records video.
- D046#sessions: Both say an e2e mcp session's videos go under the output videos directory.
- D047#engine: Both state mobile video is written as video/video.mp4 when the attempt's video mode records.
- D051#artifacts: Both say video is opt-in through video or --video and recorded as incomplete redaction.
- D052#options: Both describe a test's own trace and video option taking a recording mode, with innermost winning.
- D052#testoptions: Both state a test's trace and video options use the config's recording modes, innermost winning.
- D053#options: Both describe the web engine screencast option setting frame size and quality for recorded video.
- D056#what-is-sent: Both list the recording modes off, on, retain-on-failure, on-first-retry, on-all-retries.
- D041#target: Both say a target's trace and video modes replace the config's top-level modes.
- D042#artifacts: Both describe provider recordings stored as video/<file> or a link, per-attempt video segments with startedAt, and incomplete redaction.
- D044#runner-codes: Both state UNSUPPORTED_ARTIFACT for a video mode the engine cannot record, and LAUNCH_TIMEOUT.
- D052#options: Both describe trace and video recording modes with innermost value winning and serial groups recording as one unit.
- D052#testoptions: Both say trace and video options override the run's, innermost wins, and serial groups use the group's value.
