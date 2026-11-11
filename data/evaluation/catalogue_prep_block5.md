# Vorbereitungsblatt Block 5 (S33–S40)

KI-Hilfe (Claude) vor dem Schreiben, offengelegt nach ADR 0031/0049. Mechanischer Teil wie bei Block 3 und 4: je Satz
des Ausgangsabschnitts (ohne Codeblöcke; Tabellenzeilen zählen je als ein Satz), ob eine Folge von 5 Wörtern auch im
eigenen Text eines anderen Abschnitts steht (außer umschließenden und enthaltenen Abschnitten), und für Begriffe in
Backticks, in welchen anderen Abschnitten sie vorkommen (nur bei höchstens 10 Treffern gelistet, dann vollständig).
Dazu die Zeilen aus `catalogue_overlap.csv` und je Slot die **Typ-Eignung** (ADR 0049, Nachtrag 10.11.2026). Neu ab
Block 5: Jede Stelle, auf die sich ein Typ stützt, ist zusätzlich mit `catalogue.py find` auf ihre Kernformulierung
geprüft und gegen die Überschneidungsliste gelesen. In Block 4 hatte das Blatt zwei Stellen als „nur hier“
bezeichnet, die anders formuliert auch woanders standen (S25, S30). Die Typ-Eignung ist ein Vorschlag; den Typ wählt
Jonas (ADR 0031). Das Blatt enthält keine Frage, keine Antwort und kein Relevanzurteil. „ONLY HERE“ heißt nur: kein
wörtlicher Treffer. Erstellt am 11.11.2026.

Typziel Block 5 ([Plan](../../docs/plan.md#zeitplan)): **3 conceptual, 1 comparative, 1 limitation, 3 procedural,
0 factual**. Vorschlag: S33 procedural, S34 conceptual, S35 procedural, S36 limitation, S37 Sprung (`content-elsewhere`,
Reserve D051#outbound-connections), S38 conceptual, S39 comparative, S40 procedural. Das dritte `conceptual` trägt in
diesem Block wohl kein Slot sauber: Die Reserve für S37 passt eher zu `limitation` oder `factual`, und S33 als
`conceptual` fehlte dann bei `procedural`. Was hier fehlt, wandert nach Block 6.

## S33 · multi-section · D041#run-limits  (E2EConfig › Run limits; page title: E2EConfig)

Regel: mindestens zwei Abschnitte, jeder liefert einen nötigen Teil; enthaltene oder umschließende Abschnitte zählen nicht als zweiter; H1 nur mit Grund in `notes`.

**Typ-Eignung:** Ziel `procedural`: wie man die Obergrenzen anhebt, die `run.limits` für Beobachtungsgröße und Tokens pro Modellaufruf meldet. Hier stehen „`maxObservationBytes` | the largest `agents.<name>.maxObservationBytes`“ und „`maxModelTokensPerCall` | the largest `agents.<name>.maxInputTokens`“ (`run.limits` nur hier). Gesetzt werden die Budgets je Agent in D041#agents bzw. D041#agentconfig. „Per-call options may only lower an agent's budgets“ steht auch in D038#budgets und D038#types (`find "only lower"`). Damit sind D041#agents, D041#agentconfig und D038#budgets mögliche weitere Abschnitte für `multi-section`; jeder Abschnitt mit einem nötigen Teil gehört dazu. `maxObservationBytes` nennen auch D015#common-errors und D044#agenterror; enthalten sie einen nötigen Teil (etwa den Rat, das Budget anzuheben), gehören sie ebenfalls dazu. Die festen Werte 16384/8192/1000 stehen auch in D041#agents und D041#agentconfig. Alternative `conceptual`: warum es keinen `limits`-Schlüssel gibt („two fields come from the agents, and the runner fixes the rest“, nur hier).

- **[ONLY HERE]** ## Run limits The report's `run.limits` block records the ceilings a run enforced.
- **[ONLY HERE]** There is no `limits` key: two fields come from the agents, and the runner fixes the rest.
- **[ONLY HERE]** Per-call options may only lower an agent's budgets.
- **[ONLY HERE]** | `maxAgentContextBytes` | 16384: an agent's `context` and a test's `agentContext` |
    term `agentContext` also in 7: D002#instructions-and-vocabulary, D002#one-flow-several-personas, D007#what-must-match, D018#what-the-context-holds, D051#redaction, D052#options, D052#testoptions
    term `maxAgentContextBytes` also in 1: D041#agents
- **[ONLY HERE]** | `maxLedgerBytes` | 8192: the prior-step ledger an act step reads |
    term `maxLedgerBytes` also in 1: D041#agents
- **[ONLY HERE]** | `maxEventsPerStep` | 1000: events recorded per step |
    term `maxEventsPerStep` also in 1: D041#agents
- **[ONLY HERE]** | `maxObservationBytes` | the largest `agents.<name>.maxObservationBytes` |
    term `agents.<name>.maxObservationBytes` also in 2: D015#common-errors, D044#agenterror
    term `maxObservationBytes` also in 4: D015#common-errors, D041#agentconfig, D041#agents, D044#agenterror
- **[ONLY HERE]** | `maxModelTokensPerCall` | the largest `agents.<name>.maxInputTokens` |
    term `maxModelTokensPerCall` also in 1: D041#agents

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D041#agents: Both give the fixed 16384-byte agent context, 8192-byte ledger and 1000-event limits, and the observation and input-token budgets.
- D041#agentconfig: Both give the agent context limit of 16384 bytes and the maxObservationBytes and maxInputTokens budgets.
- D052#options: Both limit an agent's context and a test's agentContext in bytes.

## S34 · detail · D041#modelinstance  (E2EConfig › Types › `ModelInstance`; page title: E2EConfig)

Regel: genau ein Abschnitt, ein einzelnes Faktum, Referenzantwort höchstens 30 Wörter; das Faktum muss nur hier stehen.

**Typ-Eignung:** Ziel `conceptual`: wozu `doGenerate` in `ModelInstance` dient: „what tells a live instance from its three id strings“ (`find "doGenerate"` und `find "live instance"`: nur hier). Ein Grund in einem Satz passt zu `detail` (≤ 30 Wörter). Vorsicht: dass `model` eine AI-SDK-Modellinstanz ist, steht auch in D041#agents, D041#agentconfig und D036#ai-sdk-providers; `modelId` auch in D041#agents. Alternative `factual`: „An AI SDK LanguageModelV2+ instance“ (nur hier), aber `factual` hat nur noch einen Platz.

*(Nur Codeblock: der mechanische Teil prüft keine Codeblöcke. Die Kommentare im Code sind mit `catalogue.py find` und durch Lesen gegen den Korpus geprüft; das Ergebnis steht in der Typ-Eignung.)*

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D036#ai-sdk-providers: Both say a model provider implementing the AI SDK language model specification works.
- D041#agents: Both say the model option is an AI SDK model instance with no implicit default.
- D041#agentconfig: Both declare the model as an AI SDK ModelInstance.
- D044#agenterror: Both refer to the agent's model being an AI SDK model instance (MODEL_UNAVAILABLE when none).

## S35 · paraphrase · D041#output  (E2EConfig › Reference › output; page title: E2EConfig)

Regel: genau ein Abschnitt; die Frage teilt kein Inhaltswort mit der Abschnittsüberschrift oder dem Seitentitel (auch keine Wortformen).

**Typ-Eignung:** Wortsperre: „output“, „e2econfig“, „reference“. Ziel `procedural`: „With `output` set elsewhere, add that directory to `.gitignore` yourself.“ und „`e2e init` writes `.gitignore` entries for the default `.e2e/` paths only.“ (beide nur hier). Die einzelnen `.gitignore`-Einträge listet aber D040#commands; erfrage den Schritt, nicht die Liste. Alternative `conceptual`: „Paths are compared with symlinks resolved“ und `/tmp` gegen `/private/tmp` auf macOS (beide nur hier); der Satz zu einem Symlink mit noch fehlendem Ziel steht auch in D040#commands. Vorsicht: dass ein Lauf, der vor den Tests stoppt, die Dateien des vorigen Laufs stehen lässt, steht auch in D040#commands; nur die Begründung „so `--last-failed` still reads the last run that executed“ steht nur hier. Dass der Replay-Cache in `cache.dir` bleibt, steht auch in D041#cache.

- **[ALSO: D041#commandconfig, D041#the-app-under-test, D043#replay-cache]** ### output The directory everything a run writes about itself goes under, resolved from the project root.
- **[ALSO: D041#recording, D041#top-level]** `--output <dir>` on [`e2e run`](/reference/cli#e2e-run) and `e2e explore` overrides it for one run.
    term `--output <dir>` also in 1: D040#commands
- **[ALSO: D040#commands]** - A run that stops before its tests start writes nothing here.
- **[ALSO: D040#commands]** Such stops are a selection that matches no test (`NO_TESTS`, a mistyped `--grep`), a collection error, a target that cannot record what it asks for (`UNSUPPORTED_ARTIFACT`), `NO_LAST_RUN`, an app command that fails to start, or an interrupt.
    term `--grep` also in 5: D014#run-one-test, D033#map-each-api, D040#commands, D049#functions, D051#redaction
    term `NO_LAST_RUN` also in 2: D040#commands, D044#runner-codes
    term `NO_TESTS` also in 5: D008#sharding, D040#commands, D041#top-level, D044#runner-codes, D049#functions
    term `UNSUPPORTED_ARTIFACT` also in 5: D015#watch-it-happen, D040#commands, D041#recording, D044#runner-codes, D052#options
- **[ONLY HERE]** The previous run's `report.json`, `ai-trace.json`, and `results/` stay as they were, so `--last-failed` still reads the last run that executed.
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D040#commands, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
    term `ai-trace.json` also in 4: D015#agent-steps, D040#commands, D044#runner-codes, D051#artifacts
- **[ALSO: D041#recording]** - An `e2e mcp` session writes its attempt's artifacts under `results/mcp/` and never clears it.
    term `results/mcp/` also in 1: D046#sessions
- **[ONLY HERE]** - The replay cache stays in [`cache.dir`](#dir) whatever `output` says, so moving the results never moves the recordings.
    term `cache.dir` also in 5: D007#share-the-cache-across-checkouts, D038#types, D040#commands, D043#replay-cache, D051#artifacts
- **[ONLY HERE]** - `e2e init` writes `.gitignore` entries for the default `.e2e/` paths only.
    term `.gitignore` also in 3: D007#commit-the-replay-cache, D040#commands, D041#cache
- **[ONLY HERE]** With `output` set elsewhere, add that directory to `.gitignore` yourself.
    term `.gitignore` also in 3: D007#commit-the-replay-cache, D040#commands, D041#cache
- **[ONLY HERE]** A run clears and owns part of the output directory.
- **[ALSO: D004#override-a-value-per-run, D018#keep-the-loop-change-the-vocabulary, D041#secrets, D057#add-a-tool]** So the config load fails with `INVALID_CONFIG`, naming the reason, when the directory:
- **[ALSO: D040#commands, D049#host]** - is the project root, or outside it; - is a file, or a path under one (a missing directory is created); - is the cache directory (`cache.dir`, `--cache-dir`, or `E2E_CACHE_DIR`) or inside it, or would hold it under `results/`, `sessions/`, or `videos/`; - holds a directory a `tests` glob scans (`ou
    term `--cache-dir` also in 4: D007#share-the-cache-across-checkouts, D040#commands, D041#cache, D043#replay-cache
    term `E2E_CACHE_DIR` also in 5: D007#share-the-cache-across-checkouts, D040#commands, D041#cache, D043#reference-environment, D043#replay-cache
    term `cache.dir` also in 5: D007#share-the-cache-across-checkouts, D038#types, D040#commands, D043#replay-cache, D051#artifacts
    term `sessions/` also in 7: D005#recording-on-the-provider, D005#write-a-provider, D022#watch-a-run, D035#hosted-devices, D040#commands, D051#artifacts, D051#sessions
    term `tests/**/*.e2e.ts` also in 8: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D032#port-the-config, D033#app-targets-and-output, D033#migrate-playwright, D034#migrate-selenium, D041#top-level
    term `videos/` also in 4: D040#commands, D046#sessions, D046#the-catalog, D051#artifacts
- **[ONLY HERE]** Paths are compared with symlinks resolved.
- **[ONLY HERE]** An absolute path spelled through a symlink (`/tmp` for `/private/tmp` on macOS) names the same directory as its target.
- **[ALSO: D040#commands]** A symlink whose target does not exist yet is followed too, so an output through one that points outside the project root is refused.
- **[ALSO: D040#commands]** **Note** The removed `--artifacts <dir>` flag fails with the `--output` it maps to.
    term `--artifacts <dir>` also in 1: D040#commands
    term `--output` also in 6: D006#what-the-agent-does, D012#ios-and-android, D032#port-the-config, D033#map-each-api, D040#commands, D051#artifacts
- **[ONLY HERE]** The report used to go to the directory's parent, so `--artifacts out/artifacts` is `--output out`.
    term `--artifacts out/artifacts` also in 1: D040#commands
    term `--output out` also in 1: D040#commands
- **[ALSO: D040#commands]** A parent an output cannot be (the project root, or outside it) maps to `--output .e2e`.
    term `--output .e2e` also in 1: D040#commands
- **[ONLY HERE]** | Path under the output | What |
- **[ONLY HERE]** | `report.json` | The canonical report; `--last-failed` reads the one here |
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D040#commands, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
- **[ALSO: D040#commands]** | `junit.xml`, `summary.md` | The `junit` and `markdown` reporters' files |
    term `summary.md` also in 8: D015#debugging, D020#the-comment, D032#port-the-config, D033#app-targets-and-output, D033#map-each-api, D040#commands, D041#top-level, D048#built-in-reporters
- **[ALSO: D015#artifacts, D040#commands]** | `results/` | One directory per test: its [trace page](/debugging#traces), `trace.md`, when the [`trace`](#trace) mode keeps one, and its screenshots, videos, downloads, and logs, one `attempt-<n>/` per attempt. Cleared once a run's tests start, so it holds the latest run's evidence and nothing its
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D040#commands, D041#top-level, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
    term `rerun-<n>/` also in 3: D008#rerunning-failures, D015#artifacts, D040#commands
- **[ONLY HERE]** | `sessions/` | The run's encrypted `test.setup` sessions, deleted when it ends |
    term `sessions/` also in 7: D005#recording-on-the-provider, D005#write-a-provider, D022#watch-a-run, D035#hosted-devices, D040#commands, D051#artifacts, D051#sessions
- **[ONLY HERE]** | `videos/<session>/` | [`e2e mcp`](/reference/mcp#recording) session recordings |
    term `videos/<session>/` also in 2: D046#the-catalog, D051#artifacts

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D015#agent-steps: Both say --ai-trace produces the ai-trace.json file in the output directory.
- D033#browser-timeouts-and-artifacts: Both say each test's directory under results holds its trace.md page.
- D033#what-differs-on-purpose: Both state encrypted sessions are deleted when the run ends.
- D040#commands: Both describe the output directory: report.json, summary.md, junit.xml, results/ trace pages, --cache-dir and --ai-trace.
- D041#top-level: Both list output default .e2e and the junit and markdown reporter files.
- D008#upload-the-reports: Both list report.json, junit.xml and results/ under the output directory, which the output option moves.
- D015#artifacts: Both describe per-test results/ directories, cleared at run start, with --last-failed reruns in rerun-<n>/.
- D032#port-the-config: Both state junit writes .e2e/junit.xml and markdown writes .e2e/summary.md.
- D033#app-targets-and-output: Both state output (outputDir) defaults to .e2e and holds results/ cleared when a run starts.
- D033#map-each-api: Both map Playwright outputDir/--output to the results directory holding each test's trace page.
- D040#commands: Both describe --output overriding the output directory, the removed --artifacts flag mapping to --output, NO_LAST_RUN and gitignore entries.
- D041#cache: Both state the replay cache stays in cache.dir whatever output says, and .gitignore handling of .e2e paths.
- D044#runner-codes: Both describe NO_LAST_RUN, NO_TESTS and UNSUPPORTED_ARTIFACT stops that leave the previous run's files.
- D046#sessions: Both describe e2e mcp session artifacts under results/mcp/ and videos/ in the output directory.
- D048#built-in-reporters: Both state the junit and markdown reporters write junit.xml and summary.md in the output directory.
- D051#sessions: Both say encrypted sessions are stored under sessions/ in the output directory.
- D051#artifacts: Both list files written under the output directory (report.json, results/, ai-trace.json, sessions/).
- D041#cache: Both say the cache directory stays at cache.dir and is gitignored.
- D044#runner-codes: Both describe NO_TESTS, NO_LAST_RUN and UNSUPPORTED_ARTIFACT stops.
- D051#sessions: Both say the sessions directory holds the run's encrypted test.setup sessions, deleted when the run ends.

## S36 · paraphrase · D041#cache  (E2EConfig › Reference › cache; page title: E2EConfig)

Regel: genau ein Abschnitt; die Frage teilt kein Inhaltswort mit der Abschnittsüberschrift oder dem Seitentitel (auch keine Wortformen).

**Typ-Eignung:** Wortsperre: „cache“, „e2econfig“, „reference“ (also z. B. über gespeicherte Replays fragen). Der Abschnitt steht großteils auch anderswo: Modi und CI-Default in D007#modes, D008#what-ci-changes, D041#ci und D051#cache-trust; Aufzeichnen erst nach einer späteren Prüfung in D007#cache und D014#goals; „never writes“ unter `--strict-cache` in D007#fail-on-a-stale-recording; `--cache-dir` neben einem eigenen Store als `INVALID_CONFIG` auch in D040#commands; `E2E_CACHE_DIR` ignoriert auch in D043#replay-cache; der `.gitignore`-Teil in D007#commit-the-replay-cache. Ziel `limitation`: der eigene `store`: „Each worker constructs its own.“ und „it states its own trust through `writable`“ (`find "own trust"`: nur hier; „constructs its own“ steht auch in D041#artifacts und D041#agents, dort für andere Dinge). Dass ein eigener Store in CI nicht auf `read-only` fällt, steht auch in D007#modes und D051#cache-trust, gehört also nicht in die Antwort. Alternative `procedural`: „Set `'read-write'` explicitly when CI restores the cache from its own cache service.“ (`find "cache service"`: nur hier). Die Anweisung „`read-write` setzen“ steht aber als „CI stays `read-only` unless `cache: 'read-write'` is set“ auch in D007#commit-the-replay-cache, D008#what-ci-changes und D041#ci; nur der Anlass (eigener Cache-Dienst des CI) steht nur hier. Schwacher Slot.

- **[ONLY HERE]** ### cache Replay cache mode or options.
- **[ONLY HERE]** In `read-write` mode the replay cache records an `agent.act()` only after a later verification passes, such as a locator assertion or `agent.assert()`.
    term `agent.act()` also in 5: D007#cache, D007#why-a-step-was-not-replayed, D019#explore, D041#agentconfig, D041#agents
- **[ONLY HERE]** A bare string is shorthand for `{ mode }`:
- **[ONLY HERE]** The declarations are under [`CacheConfig`](#cacheconfig). #### `mode` What the replay cache reads and writes.
    term `CacheConfig` also in 3: D041#cacheconfig, D041#e2econfig, D041#top-level
- **[ONLY HERE]** - An explicit mode overrides the default.
- **[ONLY HERE]** Set `'read-write'` explicitly when CI restores the cache from its own cache service.
    term `'read-write'` also in 3: D007#commit-the-replay-cache, D007#modes, D041#top-level
- **[ONLY HERE]** - `--no-cache` wins over both and disables caching for the run. #### `store` A custom entry store that replaces the file store.
    term `--no-cache` also in 9: D007#modes, D007#what-must-match, D007#why-a-step-was-not-replayed, D013#how-an-agent-reads-a-failure, D013#how-an-agent-writes-and-runs-a-test, D015#agent-steps, D037#add-an-agent-step, D040#commands, D043#replay-cache
- **[ONLY HERE]** - Each worker constructs its own.
- **[ONLY HERE]** - Exempt from the CI demotion: it states its own trust through `writable`.
    term `writable` also in 2: D041#cacheconfig, D056#opt-out
- **[ALSO: D053#weboptions]** - `--cache-dir` beside it is `INVALID_CONFIG`, and `E2E_CACHE_DIR` is ignored.
    term `--cache-dir` also in 4: D007#share-the-cache-across-checkouts, D040#commands, D041#output, D043#replay-cache
    term `E2E_CACHE_DIR` also in 5: D007#share-the-cache-across-checkouts, D040#commands, D041#output, D043#reference-environment, D043#replay-cache
- **[ALSO: D041#cacheconfig, D041#the-app-under-test]** `CacheStore`, `CacheReadResult`, `TraceEntry`, and `ActionTrace` are exported from `e2e`. #### `dir` The file store directory, resolved against the project root.
    term `ActionTrace` also in 1: D041#cacheconfig
    term `CacheReadResult` also in 1: D041#cacheconfig
    term `CacheStore` also in 1: D041#cacheconfig
    term `TraceEntry` also in 1: D041#cacheconfig
- **[ONLY HERE]** - It stays where it is whatever `output` says.
- **[ALSO: D040#commands, D044#agenterror]** - `--cache-dir` and `E2E_CACHE_DIR` replace it. #### `strict` Fails a step whose recording exists but no longer replays with `REPLAY_STALE`, instead of handing it to the agent.
    term `--cache-dir` also in 4: D007#share-the-cache-across-checkouts, D040#commands, D041#output, D043#replay-cache
    term `E2E_CACHE_DIR` also in 5: D007#share-the-cache-across-checkouts, D040#commands, D041#output, D043#reference-environment, D043#replay-cache
    term `REPLAY_STALE` also in 6: D007#fail-on-a-stale-recording, D007#share-the-cache-across-checkouts, D038#agent-act, D040#commands, D041#cacheconfig, D044#agenterror
- **[ONLY HERE]** - `--strict-cache` turns it on for one run.
    term `--strict-cache` also in 4: D007#fail-on-a-stale-recording, D007#why-a-step-was-not-replayed, D040#commands, D044#agenterror
- **[ONLY HERE]** - The run then never writes the cache.
- **[ALSO: D007#commit-the-replay-cache, D007#fail-on-a-stale-recording, D040#commands]** See [Fail on a stale recording](/cache#fail-on-a-stale-recording). #### Commit the replay cache `e2e init` adds `.e2e/cache/` to `.gitignore`, so committing entries is opt-in.
    term `.e2e/cache/` also in 6: D007#commit-the-replay-cache, D007#what-a-recording-holds, D015#traces, D040#commands, D051#artifacts, D051#cache-trust
    term `.gitignore` also in 3: D007#commit-the-replay-cache, D040#commands, D041#output
- **[ONLY HERE]** Remove that line to share replays with CI and teammates.
- **[ONLY HERE]** CI stays `read-only` unless `cache: 'read-write'` is set.
    term `cache: 'read-write'` also in 1: D007#commit-the-replay-cache
- **[(short, not compared)]** See [Caching](/cache#commit-the-replay-cache).
- **[ONLY HERE]** | [`mode`](#mode) | `CacheMode` | `'read-write'`, `'read-only'` in CI |
    term `'read-only'` also in 2: D007#modes, D041#top-level
    term `'read-write'` also in 3: D007#commit-the-replay-cache, D007#modes, D041#top-level
    term `CacheMode` also in 3: D041#cacheconfig, D041#e2econfig, D041#top-level
- **[ONLY HERE]** | [`store`](#store) | `CacheStore` | the file store at `dir` |
    term `CacheStore` also in 1: D041#cacheconfig
- **[(short, not compared)]** | [`dir`](#dir) | `string` | `'.e2e/cache'` |
    term `'.e2e/cache'` also in 1: D007#modes
- **[(short, not compared)]** | [`strict`](#strict) | `boolean` | `false` |
- **[ONLY HERE]** | `'read-write'` | Replays entries and records new ones. |
    term `'read-write'` also in 3: D007#commit-the-replay-cache, D007#modes, D041#top-level
- **[ONLY HERE]** | `'read-only'` | Replays existing entries and writes none. |
    term `'read-only'` also in 2: D007#modes, D041#top-level

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D037#add-an-agent-step: Both say --no-cache disables caching for the run.
- D040#commands: Both describe --no-cache, --strict-cache and --cache-dir for the replay cache.
- D041#output: Both state the replay cache stays in cache.dir whatever output says, and .gitignore handling of .e2e paths.
- D007#cache: Both say the replay cache records an agent.act() only after a later verification passes.
- D007#why-a-step-was-not-replayed: Both describe cache.strict, --strict-cache and --no-cache.
- D007#modes: Both describe the cache modes read-write, read-only and off, the CI default and --no-cache.
- D007#share-the-cache-across-checkouts: Both describe --cache-dir and E2E_CACHE_DIR and cache.strict.
- D007#commit-the-replay-cache: Both say e2e init gitignores .e2e/cache/ so committing entries is opt-in and CI stays read-only unless read-write is set.
- D007#fail-on-a-stale-recording: Both describe cache.strict and --strict-cache failing with REPLAY_STALE.
- D008#what-ci-changes: Both state the cache is read-only in CI unless read-write is set.
- D008#mobile-jobs: Both refer to committing the replay cache.
- D008#gate-pull-requests: Both say to commit the replay cache for CI.
- D014#goals: Both say a goal is recorded only after a later check passes.
- D040#commands: Both describe --no-cache, --strict-cache, --cache-dir and the .gitignore entry for the cache.
- D041#top-level: Both list the cache option and its CacheMode.
- D041#output: Both say the cache directory stays at cache.dir and is gitignored.
- D041#ci: Both state the cache is read-only in CI unless read-write is set.
- D041#e2econfig: Both declare the cache option and CacheMode.
- D041#cacheconfig: Both declare the cache options mode, store, dir and strict with their defaults.
- D043#replay-cache: Both describe E2E_CACHE_DIR, --cache-dir, a custom cache.store and --no-cache.
- D044#agenterror: Both describe REPLAY_STALE under cache.strict or --strict-cache.
- D051#cache-trust: Both cover read-only cache mode and cache.store trust.

## S37 · single · D041#commandconfig  (E2EConfig › Types › `CommandConfig`; page title: E2EConfig)

Regel: genau ein Abschnitt, dessen Hauptinhalt die Antwort ist; jeder Teil der Antwort muss nur hier stehen.

**Typ-Eignung:** Keine Typ-Eignung für `single`: jedes Feld steht mit Bedeutung und Default auch in D041#the-app-under-test. Dazu gehören `executable` „never shell-interpreted“, `{port}` in `args` und `env`, `cwd`, `inheritEnv` mit `*`-Präfix, `startupTimeout` 60000, `shutdownTimeout` 10000 („grace period before force-kill“), `log` („output discarded“) und `reuseExisting` `false`. Geprüft mit `find` und durch Lesen; Teile stehen auch in D059#let-the-runner-start-it und D043#what-app-processes-inherit. Vorschlag: Sprung mit `content-elsewhere` ([ADR 0031, Nachtrag 11.11.2026](../../docs/adr/0031-stichprobenplan-und-ki-durchsicht.md)). Dafür braucht es eine angenommene `class`-Zeile in der Durchsicht, die D041#the-app-under-test nennt; entscheiden musst du. Dann übernimmt die nächste Reserve in Zugreihenfolge, `D051#outbound-connections` (Project, Zug 13), mit Klasse `single` (Abschnitt unten).

*(Nur Codeblock: der mechanische Teil prüft keine Codeblöcke. Die Kommentare im Code sind mit `catalogue.py find` und durch Lesen gegen den Korpus geprüft; das Ergebnis steht in der Typ-Eignung.)*

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D006#before-you-start: Both mention reuseExisting: true on the target's app.command.
- D008#what-ci-changes: Both say command.reuseExisting is ignored in CI.
- D015#common-errors: Both cover app.command never becoming ready (startupTimeout) and reuseExisting for an app already running.
- D029#run-tests-next-to-a-session: Both mention reuseExisting: true to share the app.
- D033#app-targets-and-output: Both map reuseExistingServer to app.command reuseExisting.
- D040#commands: Both mention reuseExisting on the command to keep a dev server up.
- D041#the-app-under-test: Both list the app.command options executable, args with {port}, cwd, env, inheritEnv, startupTimeout, shutdownTimeout, log and reuseExisting.
- D041#ci: Both say command.reuseExisting is ignored in CI.
- D043#run-mode: Both say reuseExisting on an app command is ignored in CI.
- D043#what-app-processes-inherit: Both describe command.inheritEnv selecting variables the app process inherits.
- D044#agenterror: Both cover APP_UNREACHABLE when the app command exceeds startupTimeout and APP_ALREADY_RUNNING with reuseExisting.
- D051#where-redaction-stops: Both describe command.log as the app's stdout and stderr captured verbatim.
- D051#artifacts: Both describe the command.log path for the app's output.
- D054#what-can-still-leak: Both describe command.log holding the app's stdout and stderr verbatim.
- D059#let-the-runner-start-it: Both describe command executable, args, env, inheritEnv, startupTimeout and the readiness probe.
- D059#let-the-runner-pick-the-port: Both say {port} is replaced in the command's args and env.

## S38 · detail · D041#top-level  (E2EConfig › Reference › Top level; page title: E2EConfig)

Regel: genau ein Abschnitt, ein einzelnes Faktum, Referenzantwort höchstens 30 Wörter; das Faktum muss nur hier stehen.

**Typ-Eignung:** Ziel `conceptual`: warum die `app`-Felder eines Targets `undefined` in ihren Typen annehmen („so they can read `process.env` directly“), vor „Under `exactOptionalPropertyTypes`, `undefined` is a type error“ und „At runtime, `undefined` counts as unset“ (`find "exactOptionalPropertyTypes"` und `find "counts as unset"`: nur hier). D041#the-app-under-test sagt nur, dass ein `undefined`-Wert in `env` wegfällt; das ist nicht dasselbe. Ein Grund in einem Satz, ≤ 30 Wörter. Alternative `limitation`: „`e2e explore` ignores it and keeps its own `--timeout`“ (zu `maxDuration`, nur hier). Vorsicht: der Höchstwert 2147483647 steht auch in D040#commands, `RUN_TIMEOUT` mit Exit 1 auch in D044#runner-codes, Glob-Fehler auch in D044#runner-codes und D040#commands, `node_modules` auch in D040#commands und D044#runner-codes.

- **[ONLY HERE]** ### Top level The full declaration is [`E2EConfig`](#e2econfig).
- **[ONLY HERE]** - An unknown key at any level is `INVALID_CONFIG`.
- **[ALSO: D041#the-app-under-test]** There is no top-level `app` key: each target declares [the app it tests](#the-app-under-test).
- **[ONLY HERE]** - Every numeric value must be a safe integer.
- **[ONLY HERE]** - An optional key takes a value or is left out.
- **[ONLY HERE]** Under `exactOptionalPropertyTypes`, `undefined` is a type error, so `store: process.env.CACHE_URL && createStore(...)` fails to compile.
- **[ONLY HERE]** At runtime, `undefined` counts as unset.
- **[ONLY HERE]** - The target's `app` fields also accept `undefined` in their types, so they can read `process.env` directly.
- **[ONLY HERE]** Spread any other key that depends on the environment in only when it has a value: #### `projectId` A stable id for the project.
    term `projectId` also in 5: D007#share-the-cache-across-checkouts, D022#link-the-expo-project, D022#options, D041#e2econfig, D048#events
- **[(short, not compared)]** - 1 through 256 characters.
- **[ALSO: D033#app-targets-and-output, D040#commands, D041#e2econfig]** - Without a `name` in the root `package.json`, it falls back to `unportable-<sha256 of the project root, 32 hex>`. #### `tests` The test file globs, relative to the project root.
    term `package.json` also in 7: D007#share-the-cache-across-checkouts, D032#migrate-maestro, D034#migrate-selenium, D040#commands, D041#e2econfig, D041#import-resolution, D041#module-format
- **[ONLY HERE]** - A glob takes `*`, `?`, and a whole `**` segment.
    term `, and a whole ` also in 2: D040#commands, D041#e2econfig
- **[ONLY HERE]** `?` matches one Unicode code point, including an emoji.
- **[ONLY HERE]** - An entry that starts with `!` excludes.
- **[ONLY HERE]** The example selects every test file except those under `tests/wip/`.
    term `tests/wip/` also in 1: D033#app-targets-and-output
- **[ONLY HERE]** - A file is selected when an including glob matches it and no exclusion does, whatever the order of the list.
- **[ONLY HERE]** - Discovery visits only directories that could match.
- **[ONLY HERE]** It never enters a directory an exclusion takes whole, skips `node_modules`, and ignores symlinks.
    term `node_modules` also in 5: D011#workflow, D013#install-the-skill, D027#run-the-app-in-the-machine, D040#commands, D044#runner-codes
- **[ALSO: D041#e2econfig]** - A dot directory is included only when a glob segment starts with a dot. #### `timeout` The deadline of one test attempt, in milliseconds. #### `launchTimeout` The budget for engine init and attempt start, in milliseconds. #### `actionTimeout` The budget of every engine operation, in milliseconds.
    term `launchTimeout` also in 5: D035#set-up, D041#e2econfig, D042#lifecycle, D044#runner-codes, D047#engine
- **[ALSO: D041#e2econfig]** A targeted agent action is bounded by the smaller of `actionTimeout` and 15 s. #### `assertionTimeout` The default `expect` deadline, in milliseconds. #### `cleanupTimeout` The budget of each `afterEach` hook, fixture teardown, and engine cleanup, in milliseconds. #### `retries` Retries per test.
    term `assertionTimeout` also in 10: D033#browser-timeouts-and-artifacts, D033#defaults-that-differ, D034#port-the-config, D041#e2econfig, D045#polling-a-value, D045#screenshot-matchers, D045#timeouts-and-failures, D053#the-browser-fixture, D058#tolerance-and-masks, D058#when-it-fails
- **[ALSO: D019#read-the-results, D041#e2econfig, D052#members]** - 0 through 10. #### `failOnSkippedFailure` Fails the run with exit code 1 when a test skips a retry after an earlier failed attempt.
    term `failOnSkippedFailure` also in 2: D041#e2econfig, D052#members
- **[ONLY HERE]** - The test keeps its `skipped` status and reason.
- **[ALSO: D052#members]** - Its failures remain in the report, and the CLI shows them under `Skipped After Failure` with either setting.
    term `Skipped After Failure` also in 1: D052#members
- **[ONLY HERE]** - Clean skips, successful retries, and engine cleanup diagnostics do not trigger it.
- **[ALSO: D041#e2econfig]** **Note** A skip after a failed `expect.soft` needs no option: it [fails the attempt](/reference/test#members). #### `maxDuration` The wall-clock budget for running the tests, in milliseconds.
    term `expect.soft` also in 8: D033#map-each-api, D045#expectcall-softexpectcall-and-expect, D045#reference, D045#reference-expect, D045#soft-assertions, D045#valueexpectation, D049#session, D052#members
    term `maxDuration` also in 6: D022#options, D022#sessions, D033#app-targets-and-output, D040#commands, D041#e2econfig, D044#runner-codes
- **[ONLY HERE]** It stops a run that takes too long.
- **[ONLY HERE]** - At most 2147483647 (about 24 days).
- **[ONLY HERE]** - The clock starts when the tests start.
- **[ONLY HERE]** The app command's [`startupTimeout`](#command) bounds app startup instead.
    term `startupTimeout` also in 5: D015#common-errors, D041#commandconfig, D041#the-app-under-test, D044#agenterror, D059#let-the-runner-start-it
- **[ONLY HERE]** - Once the time is spent, the runner dispatches nothing more.
- **[ALSO: D040#commands, D044#runner-codes]** The running tests end as `interrupted`, and the tests not started are skipped with cause `time-limit`.
    term `time-limit` also in 1: D044#runner-codes
- **[ONLY HERE]** The run records a `RUN_TIMEOUT` error and exits 1.
    term `RUN_TIMEOUT` also in 1: D044#runner-codes
- **[ONLY HERE]** - `--last-failed` runs the interrupted and skipped tests next.
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D040#commands, D041#output, D044#runner-codes, D048#built-in-reporters, D048#custom-reporters
- **[ALSO: D041#output]** - `--max-duration <ms>` overrides it for one run.
    term `--max-duration <ms>` also in 3: D008#gate-pull-requests, D033#app-targets-and-output, D040#commands
- **[ONLY HERE]** - `e2e explore` ignores it and keeps its own `--timeout`. #### `workers` Parallel workers.
    term `--timeout` also in 2: D019#if-the-run-stops-too-early, D040#commands
- **[ALSO: D041#ci]** - Locally the default is `max(1, floor(availableParallelism() / 2))`.
    term `max(1, floor(availableParallelism() / 2))` also in 1: D041#ci
- **[ALSO: D041#e2econfig]** - An engine may cap it lower:
- **[ONLY HERE]** `workers` never exceeds what a target's engine declares. #### `reporters` Output renderers and reporter objects.
- **[ONLY HERE]** An unknown id is `INVALID_CONFIG`.
- **[ONLY HERE]** | [`projectId`](#projectid) | `string` | `package.json` name |
    term `package.json` also in 7: D007#share-the-cache-across-checkouts, D032#migrate-maestro, D034#migrate-selenium, D040#commands, D041#e2econfig, D041#import-resolution, D041#module-format
    term `projectId` also in 5: D007#share-the-cache-across-checkouts, D022#link-the-expo-project, D022#options, D041#e2econfig, D048#events
- **[(short, not compared)]** | [`targets`](#targets) | `Target[]` | required |
    term `Target[]` also in 1: D041#e2econfig
- **[ONLY HERE]** | [`tests`](#tests) | `string \| string[]` | `'tests/**/*.e2e.ts'` |
    term `'tests/**/*.e2e.ts'` also in 2: D032#port-the-config, D033#app-targets-and-output
- **[(short, not compared)]** | [`timeout`](#timeout) | `number` | `120000` |
    term `120000` also in 4: D038#agent-act, D038#budgets, D039#reference, D041#e2econfig
- **[(short, not compared)]** | [`launchTimeout`](#launchtimeout) | `number` | `60000` |
    term `60000` also in 6: D038#agent-waitfor, D038#types, D040#commands, D041#commandconfig, D041#e2econfig, D041#the-app-under-test
    term `launchTimeout` also in 5: D035#set-up, D041#e2econfig, D042#lifecycle, D044#runner-codes, D047#engine
- **[(short, not compared)]** | [`actionTimeout`](#actiontimeout) | `number` | `30000` |
    term `30000` also in 10: D038#agent-assert, D038#agent-extract, D038#agent-waitfor, D038#budgets, D038#types, D039#reference, D041#agentconfig, D041#agents, D041#e2econfig, D050#screen-actions
- **[(short, not compared)]** | [`assertionTimeout`](#assertiontimeout) | `number` | `5000` |
    term `5000` also in 3: D041#e2econfig, D045#polling-a-value, D045#polloptions-and-pollexpectation
    term `assertionTimeout` also in 10: D033#browser-timeouts-and-artifacts, D033#defaults-that-differ, D034#port-the-config, D041#e2econfig, D045#polling-a-value, D045#screenshot-matchers, D045#timeouts-and-failures, D053#the-browser-fixture, D058#tolerance-and-masks, D058#when-it-fails
- **[(short, not compared)]** | [`cleanupTimeout`](#cleanuptimeout) | `number` | `30000` |
    term `30000` also in 10: D038#agent-assert, D038#agent-extract, D038#agent-waitfor, D038#budgets, D038#types, D039#reference, D041#agentconfig, D041#agents, D041#e2econfig, D050#screen-actions
- **[ONLY HERE]** | [`retries`](#retries) | `number` | `0`, `1` in CI |
- **[(short, not compared)]** | [`failOnSkippedFailure`](#failonskippedfailure) | `boolean` | `false` |
    term `failOnSkippedFailure` also in 2: D041#e2econfig, D052#members
- **[ONLY HERE]** | [`workers`](#workers) | `number` | half the cores, `1` in CI |
- **[ONLY HERE]** | [`reporters`](#reporters) | `(BuiltinReporter \| Reporter)[]` | `['list']` |
    term `['list']` also in 2: D041#e2econfig, D048#built-in-reporters
- **[(short, not compared)]** | [`output`](#output) | `string` | `'.e2e'` |
    term `'.e2e'` also in 2: D041#output, D049#functions
- **[ONLY HERE]** | [`artifacts`](#artifacts) | `ArtifactsConfig` | local only |
    term `ArtifactsConfig` also in 3: D041#artifacts, D041#artifactsconfig, D041#e2econfig
- **[(short, not compared)]** | [`trace`](#trace) | `RecordingMode` | `'retain-on-failure'` |
    term `'retain-on-failure'` also in 3: D033#browser-timeouts-and-artifacts, D041#recording, D052#options
    term `RecordingMode` also in 6: D041#e2econfig, D041#recording, D041#target, D041#targets, D052#options, D052#testoptions
- **[(short, not compared)]** | [`video`](#video) | `RecordingMode` | `'off'` |
    term `'off'` also in 7: D007#modes, D018#driving-the-page-yourself, D018#replace-the-executor, D018#replay-cache, D033#browser-timeouts-and-artifacts, D041#cache, D041#recording
    term `RecordingMode` also in 6: D041#e2econfig, D041#recording, D041#target, D041#targets, D052#options, D052#testoptions
- **[ONLY HERE]** | [`agents`](#agents) | `Record<string, AgentConfig>` | `default`, no model |
    term `Record<string, AgentConfig>` also in 1: D041#e2econfig
- **[ONLY HERE]** | [`cache`](#cache) | `CacheMode \| CacheConfig` | `'read-write'`, `'read-only'` in CI |
    term `'read-only'` also in 2: D007#modes, D041#cache
    term `'read-write'` also in 3: D007#commit-the-replay-cache, D007#modes, D041#cache
- **[ONLY HERE]** | [`credentials`](#credentials) | `Record<string, CredentialConfig>` | - |
    term `Record<string, CredentialConfig>` also in 1: D041#e2econfig
- **[ONLY HERE]** | [`secrets`](#secrets) | `Record<string, SecretConfig>` | - |
    term `Record<string, SecretConfig>` also in 1: D041#e2econfig
- **[ONLY HERE]** | `INVALID_CONFIG` | The list holds only exclusions. |
- **[ALSO: D044#runner-codes]** | `INVALID_GLOB` | An entry with no wildcard names a directory (`'!tests/wip'`). A glob names files; the error names the glob to write (`'!tests/wip/**'`). |
    term `'!tests/wip/**'` also in 1: D033#app-targets-and-output
    term `INVALID_GLOB` also in 2: D040#commands, D044#runner-codes
- **[ONLY HERE]** | `NO_TESTS` | A file passed to `e2e run` is taken out by an exclusion. The error names that entry. |
    term `NO_TESTS` also in 5: D008#sharding, D040#commands, D041#output, D044#runner-codes, D049#functions
- **[ONLY HERE]** | `'list'` | Terminal progress, failures, and a run summary. |
    term `'list'` also in 8: D020#matrix-jobs, D020#setup, D033#app-targets-and-output, D041#e2econfig, D048#built-in-reporters, D048#custom-reporters, D048#reference-reporters, D050#types
- **[(short, not compared)]** | `'junit'` | Writes `<output>/junit.xml`. |
    term `'junit'` also in 3: D033#app-targets-and-output, D048#built-in-reporters, D048#reference-reporters
    term `<output>/junit.xml` also in 1: D048#built-in-reporters
- **[(short, not compared)]** | `'markdown'` | Writes `<output>/summary.md`. |
    term `'markdown'` also in 1: D048#built-in-reporters
    term `<output>/summary.md` also in 2: D040#commands, D048#built-in-reporters
- **[ONLY HERE]** | `'json'` | Prints the report. Excludes `list`: the two together are `INVALID_CONFIG`. |
    term `'json'` also in 2: D041#what-fails-to-compile, D048#built-in-reporters
- **[ONLY HERE]** | a `Reporter` object | Runs beside the built-in ones. `--reporter` never removes it. |
    term `Reporter` also in 7: D040#commands, D041#e2econfig, D043#reporters, D048#built-in-reporters, D048#custom-reporters, D048#reference-reporters, D048#types

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D033#browser-timeouts-and-artifacts: Both give assertionTimeout, actionTimeout and the trace default of retain-on-failure.
- D040#commands: Both describe --max-duration, --last-failed, NO_TESTS and the markdown and junit reporter files.
- D007#share-the-cache-across-checkouts: Both say projectId falls back to the package.json name.
- D008#gate-pull-requests: Both say --max-duration limits test-running time and the clock starts with the tests.
- D020#rerunning-the-failed-tests: Both say tests stopped by maxDuration are run next by --last-failed.
- D033#app-targets-and-output: Both describe tests globs with ! exclusions, maxDuration (clock starts with tests) and reporters list/junit/json/markdown.
- D033#browser-timeouts-and-artifacts: Both give assertionTimeout, actionTimeout, retries, workers, timeout and the trace/video modes.
- D033#defaults-that-differ: Both give default action timeout 30 s, assertion timeout 5 s, retries 1 in CI, and workers half the cores.
- D039#reference: Both state actionTimeout defaults to 30000 ms and bounds engine operations.
- D040#commands: Both describe overriding retries, workers and maxDuration per run (--retries 0-10, --workers 1-1024, --max-duration) and INVALID_GLOB test globs.
- D041#output: Both list output default .e2e and the junit and markdown reporter files.
- D041#ci: Both give the retries default 1 in CI and workers default 1 in CI, half the cores locally.
- D041#e2econfig: Both list the config options with defaults for timeouts, retries, projectId, trace, video.
- D042#lifecycle: Both describe launchTimeout bounding engine init and attempt start, cleanupTimeout bounding cleanup, workers capped by engine.
- D044#runner-codes: Both describe INVALID_GLOB, RUN_TIMEOUT from maxDuration with time-limit skips, LAUNCH_TIMEOUT and CLEANUP_TIMEOUT.
- D045#polling-a-value: Both give the default assertion timeout of 5000 ms from assertionTimeout.
- D045#timeouts-and-failures: Both state expect's default timeout is assertionTimeout.
- D047#engine: Both state workers cannot exceed what the engine declares.
- D048#built-in-reporters: Both list built-in reporters list, junit, markdown, json and that json with list is INVALID_CONFIG.
- D052#members: Both describe failOnSkippedFailure failing the run when a retry is skipped after a failed attempt.
- D058#when-it-fails: Both state the assertionTimeout default of 5 s.
- D041#recording: Both list the trace and video options with defaults retain-on-failure and off.
- D041#cache: Both list the cache option and its CacheMode.
- D042#lifecycle: Both state init/startAttempt run within launchTimeout and cleanup hooks within cleanupTimeout.
- D044#runner-codes: Both describe INVALID_GLOB, NO_TESTS, RUN_TIMEOUT and INVALID_CONFIG.
- D048#what-reporter-does-to-reporter-objects: Both state that a Reporter object in the config runs beside built-ins and --reporter never removes it.
- D052#hooks: Both state cleanupTimeout is the budget of each afterEach hook.
- D052#fixtures: Both describe cleanupTimeout as the budget of each afterEach hook and fixture teardown.

## S39 · single · D044#runner-codes  (Errors › Reference › Runner codes; page title: Errors)

Regel: genau ein Abschnitt, dessen Hauptinhalt die Antwort ist; jeder Teil der Antwort muss nur hier stehen.

**Typ-Eignung:** Ziel `comparative`: `WORKER_EXIT` gegen `WORKER_CRASH`. `WORKER_EXIT`: „A worker exited unexpectedly while running a file. The test in flight fails with `WORKER_CRASH`, and the file's other tests are skipped. Attempts that finished before the exit stay in the report …“; `WORKER_CRASH`: „A worker exited during a specific test“ (`find`: beide nur hier). Für `single` muss die Antwort Hauptinhalt sein; die Codetabelle ist der Hauptinhalt. Vorsicht: Klassen und Exit-Codes (configuration 2, test 1, infrastructure 3, interrupted 130) stehen auch in D040#exit-codes und D044#exit-codes; viele einzelne Codes stehen auch anderswo (Liste unten). Alternative `limitation`: `NODE_UNSUPPORTED` (Node außerhalb `^22.22.3 || >=24.8.0`, Bun, Deno; nur hier) oder `SESSION_EXPIRED` mit Klasse „configuration or test“ (nur hier).

- **[ONLY HERE]** ### Runner codes These appear in terminal output and in the report as plain string codes. #### Test code errors
- **[ALSO: D044#agenterror]** | Code | When it happens | Class | Exit |
- **[ONLY HERE]** | `CONFIG_NOT_FOUND` | `--config <path>` names a file that does not exist, or no `e2e.config.ts` or `e2e.config.mts` exists from the working directory up to the repository root | configuration | 2 |
    term `--config <path>` also in 3: D040#commands, D041#finding-the-config-file, D046#flags
    term `CONFIG_NOT_FOUND` also in 2: D040#commands, D056#what-is-sent
    term `e2e.config.mts` also in 8: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D040#commands, D041#finding-the-config-file, D049#functions
- **[ONLY HERE]** | `CONFIG_AMBIGUOUS` | Both `e2e.config.ts` and `e2e.config.mts` in one directory | configuration | 2 |
    term `CONFIG_AMBIGUOUS` also in 1: D041#finding-the-config-file
    term `e2e.config.mts` also in 8: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D040#commands, D041#finding-the-config-file, D049#functions
- **[ONLY HERE]** | `CONFIG_LOAD_FAILED` | The config module failed to import: a package that is declared but not installed, an undeclared package, a wrong subpath, a removed export, or any other throw while it evaluates. The message names the fix. A config error raised while it evaluates keeps its own code: options
    term `CONFIG_LOAD_FAILED` also in 4: D036#ai-sdk-providers, D036#what-fails-and-where, D037#use-a-subscription-or-api-key, D051#tool-calls
    term `secrets.get()` also in 9: D004#secrets-that-are-not-passwords, D018#what-the-context-holds, D041#secrets, D041#the-app-under-test, D042#defineengine, D042#engine, D042#shared-semantics, D044#agenterror, D051#redaction
- **[ALSO: D003#without-a-browser, D004#secrets-that-are-not-passwords, D041#credentials, D041#secrets, D041#targets, D041#the-app-under-test, D042#shared-semantics, D043#credentials-and-secrets …]** | `INVALID_CONFIG` | A factory the config module calls (`web()`, `mobile()`, `defineEngine()`, `decisionExecutor()`) refused its options, with the factory's own message. Or: an unknown key, out-of-range value, invalid enum, or missing `targets`; a target key outside `{ name, platform, engine, app, t
    term ` (the message names ` also in 1: D044#agenterror
    term `E2E_USER_*` also in 1: D041#resolution-order
    term `E2E_USER_<NAME>_USERNAME` also in 3: D041#credentials, D041#environment-variables, D043#credentials-and-secrets
    term `String()` also in 3: D005#recording-on-the-provider, D041#secrets, D045#asymmetricmatcher
    term `agents.<name>.context` also in 1: D002#instructions-and-vocabulary
    term `api-key` also in 4: D036#models, D041#secrets, D042#app, D043#credentials-and-secrets
    term `api_key` also in 3: D041#secrets, D043#credentials-and-secrets, D043#model
    term `app.appPath` also in 10: D008#mobile-jobs, D028#setup, D035#hosted-devices, D035#physical-devices, D035#point-at-your-app, D041#the-app-under-test, D042#capabilities, D047#device, D047#engine, D052#options
    term `artifacts.kinds` also in 1: D041#artifacts
    term `artifacts.trace` also in 1: D041#artifacts
    term `artifacts.video` also in 1: D041#artifacts
    term `complete_step` also in 3: D018#executors, D044#agenterror, D057#add-a-tool
    term `defineEngine` also in 6: D041#targets, D042#defineengine, D042#reference-engine, D042#related, D060#the-shape-of-an-engine, D060#writing-an-engine
    term `defineTool` also in 9: D041#agentconfig, D041#agents, D042#actions, D046#the-catalog, D051#tool-calls, D057#add-a-tool, D057#declare-what-a-tool-does, D057#observe-from-a-tool, D060#ship-a-tool-pack
    term `interval` also in 4: D038#agent-waitfor, D038#types, D045#polling-a-value, D045#polloptions-and-pollexpectation
    term `judgmentTimeout` also in 8: D015#common-errors, D038#agent-assert, D038#agent-extract, D038#agent-waitfor, D038#budgets, D038#types, D041#agentconfig, D041#agents
    term `maxTurns` also in 1: D041#agents
    term `mobile()` also in 3: D008#mobile-jobs, D041#the-app-under-test, D047#engine
    term `report_finding` also in 2: D040#commands, D057#add-a-tool
    term `secrets.get()` also in 9: D004#secrets-that-are-not-passwords, D018#what-the-context-holds, D041#secrets, D041#the-app-under-test, D042#defineengine, D042#engine, D042#shared-semantics, D044#agenterror, D051#redaction
    term `start_recording` also in 5: D029#secrets, D041#recording, D046#the-catalog, D051#artifacts, D057#add-a-tool
    term `stop_recording` also in 3: D041#recording, D046#the-catalog, D057#add-a-tool
    term `web({ basicAuth })` also in 1: D033#browser-timeouts-and-artifacts
    term `web({ connect })` also in 3: D033#browser-timeouts-and-artifacts, D034#port-the-config, D051#outbound-connections
- **[ONLY HERE]** | `CONFIG_NOT_DETERMINISTIC` | A worker re-resolved the config module and got a different digest than the runner | configuration | 2 |
    term `CONFIG_NOT_DETERMINISTIC` also in 1: D041#agents
- **[ALSO: D039#baseurl, D039#open, D039#types, D042#app, D042#contributed-fixtures, D053#the-browser-fixture]** | `APP_URL_REQUIRED` | A navigation or relative URL on a target that declares no `app.url`, or an `app.command` with no `app.url` or `app.readyUrl` to poll | configuration | 2 |
    term `APP_URL_REQUIRED` also in 6: D039#open, D041#resolution-order, D041#the-app-under-test, D042#contributed-fixtures, D042#errors, D053#the-browser-fixture
    term `app.readyUrl` also in 1: D041#the-app-under-test
- **[ONLY HERE]** | `INVALID_APP_URL` | A base URL that is unparseable or has userinfo, a query, a fragment, a non-HTTP scheme, or plain HTTP on a non-loopback host; port 0 on a host other than a literal loopback address (`127.0.0.1`, `[::1]`); or a loopback address the run could not bind a free port on | configurati
    term `INVALID_APP_URL` also in 1: D041#the-app-under-test
    term `[::1]` also in 2: D041#the-app-under-test, D059#let-the-runner-pick-the-port
- **[ALSO: D007#share-the-cache-across-checkouts, D018#what-the-context-holds, D040#commands, D041#top-level, D053#options]** | `INVALID_GLOB` | An empty pattern; a first segment that starts with `!` beyond the one leading `!` of a `tests` exclusion (`!!tests/**`, `./!tests/**`); a bare `!`; braces, character classes, or extglobs; a backslash separator; an absolute path or a `..` segment; a trailing `/` or `.`; a `tests` e
    term `INVALID_GLOB` also in 2: D040#commands, D041#top-level
- **[ONLY HERE]** | `UNKNOWN_TARGET` | `--target`, `open_session.target`, or `openHost` (`e2e/runner`) named a target that is not configured | configuration | 2 |
    term `UNKNOWN_TARGET` also in 2: D040#commands, D049#functions
    term `e2e/runner` also in 8: D040#commands, D049#functions, D049#playwright-test-fixtures, D049#reference-runner, D049#types, D051#outbound-connections, D056#the-notice, D056#what-is-sent
    term `openHost` also in 5: D049#functions, D049#host, D049#playwright-test-fixtures, D049#reference-runner, D049#types
- **[ALSO: D049#functions]** | `TARGET_REQUIRED` | `e2e mcp` or `openHost` (`e2e/runner`): the config declares several targets and none was named | configuration | 2 |
    term `TARGET_REQUIRED` also in 2: D046#flags, D049#functions
    term `e2e/runner` also in 8: D040#commands, D049#functions, D049#playwright-test-fixtures, D049#reference-runner, D049#types, D051#outbound-connections, D056#the-notice, D056#what-is-sent
    term `openHost` also in 5: D049#functions, D049#host, D049#playwright-test-fixtures, D049#reference-runner, D049#types
- **[ALSO: D046#several-sessions]** | `NO_SESSION` | `e2e mcp`: `call` or `tools` before `open_session` or after the session ended (the message names why), or `call`, `tools`, or `close_session` naming a `session` id that is not open or is closing | configuration | 2 |
    term `NO_SESSION` also in 2: D046#sessions, D046#several-sessions
    term `close_session` also in 5: D046#sessions, D046#several-sessions, D046#the-catalog, D046#tools, D056#what-is-sent
    term `open_session` also in 8: D040#commands, D044#agenterror, D046#flags, D046#sessions, D046#setup, D046#several-sessions, D046#tools, D056#what-is-sent
- **[ALSO: D046#several-sessions]** | `SESSION_REQUIRED` | `e2e mcp`: `call`, `tools`, or `close_session` without a `session` while several sessions are open. The message lists them | configuration | 2 |
    term `SESSION_REQUIRED` also in 1: D046#several-sessions
    term `close_session` also in 5: D046#sessions, D046#several-sessions, D046#the-catalog, D046#tools, D056#what-is-sent
- **[ONLY HERE]** | `ENGINE_IN_USE` | `e2e mcp`: `open_session` on a target whose engine instance another open session drives, because the config gets it from a package every session shares. Create the engine in the config, or in a file it imports by path | configuration | 2 |
    term `ENGINE_IN_USE` also in 1: D046#several-sessions
    term `open_session` also in 8: D040#commands, D044#agenterror, D046#flags, D046#sessions, D046#setup, D046#several-sessions, D046#tools, D056#what-is-sent
- **[ALSO: D041#the-app-under-test]** | `CONFIG_IN_USE` | `e2e mcp`: `open_session` on a config other than the one the open sessions use. Credentials and secrets resolve process-wide, so open on that config or close those sessions first | configuration | 2 |
    term `CONFIG_IN_USE` also in 1: D046#several-sessions
    term `open_session` also in 8: D040#commands, D044#agenterror, D046#flags, D046#sessions, D046#setup, D046#several-sessions, D046#tools, D056#what-is-sent
- **[ALSO: D046#several-sessions]** | `SESSION_OPEN` | `e2e mcp`: `open_session` while every session slot (`--max-sessions`, default 4) holds an open, opening, or closing session, or while the server shuts down. Close one first | configuration | 2 |
    term `--max-sessions` also in 4: D040#commands, D046#flags, D046#several-sessions, D051#mcp-and-explore
    term `SESSION_OPEN` also in 1: D046#several-sessions
    term `open_session` also in 8: D040#commands, D044#agenterror, D046#flags, D046#sessions, D046#setup, D046#several-sessions, D046#tools, D056#what-is-sent
- **[ONLY HERE]** | `UNKNOWN_TOPIC` | `e2e mcp`: an `e2e://guide/{topic}` resource named a topic the skill does not have. The message lists them | configuration | 2 |
    term `e2e://guide/{topic}` also in 1: D046#resources
- **[ALSO: D046#the-catalog]** | `UNKNOWN_TOOL` | `e2e mcp`: `call` or `tools` named a tool the session's catalog does not have. The message lists the catalog. An action verb the engine does not declare is `UNSUPPORTED_CAPABILITY` instead | configuration | 2 |
    term `UNKNOWN_TOOL` also in 1: D046#the-catalog
- **[ALSO: D041#recording, D052#options]** | `UNSUPPORTED_ARTIFACT` | A [`video` mode](/reference/config#recording) set on a target, or on a test that will run there, records on some attempt, and the target's engine cannot record video. The message names the target, and the test for a test's mode. A mode from the config root or `--video` nev
    term `UNSUPPORTED_ARTIFACT` also in 5: D015#watch-it-happen, D040#commands, D041#output, D041#recording, D052#options
- **[ONLY HERE]** | `UNSUPPORTED_CAPABILITY` | A fixture, action, or tier the target's engine does not declare: a contributed fixture it does not contribute, `screen` without `locate`, state restore without `state`, screenshots without `artifacts`, `app.clearState()` on a persistent browser context (the message names
- **[ALSO: D040#commands]** | `NO_TESTS` | Zero runnable ordinary test-target pairs. The message names the cause: no file matched the `tests` globs (it lists look-alike files), a positional matched nothing (it names the `!` entry that excludes a file the positional names), a file registered no tests, or filters excluded everyt
    term `--pass-with-no-tests` also in 3: D008#sharding, D033#map-each-api, D040#commands
    term `NO_TESTS` also in 5: D008#sharding, D040#commands, D041#output, D041#top-level, D049#functions
- **[ONLY HERE]** | `RUNNER_BUSY` | A suite overlapped another suite, an opening or open host, or a live attempt; or a host opened during a suite. Await the suite and close existing hosts before you retry. | configuration | 2 |
    term `RUNNER_BUSY` also in 1: D049#functions
- **[ONLY HERE]** | `NO_LAST_RUN` | `--last-failed` found no `report.json` where the run writes it, or a file there that is not a `report-1` document. Run once without the flag first. | configuration | 2 |
    term `--last-failed` also in 10: D008#rerunning-failures, D012#ios-and-android, D015#artifacts, D020#rerunning-the-failed-tests, D033#map-each-api, D040#commands, D041#output, D041#top-level, D048#built-in-reporters, D048#custom-reporters
    term `NO_LAST_RUN` also in 2: D040#commands, D041#output
    term `report-1` also in 2: D040#commands, D048#custom-reporters
- **[ONLY HERE]** | `ONLY_IN_CI` | A focused test reached a CI run | configuration | 2 |
    term `ONLY_IN_CI` also in 7: D008#what-ci-changes, D033#map-each-api, D041#ci, D043#run-mode, D052#members, D052#options, D052#testoptions
- **[ALSO: D018#what-the-context-holds, D040#commands, D042#shared-semantics, D047#engine, D052#options, D053#options]** | `COLLECTION_ERROR` | Registration outside collection; an invalid title; a non-function body; an async `describe` body; nested serial groups; an option forbidden inside a serial group; a setup test inside `describe`; an invalid session name; a malformed test option, such as `tags` that is not a lis
    term `e2e explore --session` also in 1: D019#start-signed-in
- **[ONLY HERE]** | `SESSION_MISMATCH` | A stored session does not match the current run, target, engine, platform, or app identity | configuration | 2 |
- **[ONLY HERE]** | `SESSION_EXPIRED` | A stored session is past its expiry at restore time (configuration, exit 2), or a setup test saved state whose expiry is not after its creation (test, exit 1) | configuration or test | 2 or 1 |
- **[ONLY HERE]** | `SESSION_INVALID` | A stored session failed authentication. Tampered or corrupt. | configuration | 2 |
- **[ONLY HERE]** | `SESSION_UNAVAILABLE` | A test requires a session no selected setup test produced | configuration | 2 |
- **[ONLY HERE]** | `SESSION_CONTRACT` | A setup test saved a session twice, saved an undeclared name, or finished without saving a declared one | test | 1 |
    term `SESSION_CONTRACT` also in 2: D004#session-rules, D052#members
- **[ALSO: D052#hooks]** | `TEST_TIMEOUT` | The attempt exceeded the resolved test `timeout`. The body is not stopped: the harness operation it is in is cancelled, and its fixtures die with the attempt, so it cannot reach the next test. A test that blocks the event loop gets its worker killed once `cleanupTimeout` (at least
    term `TEST_TIMEOUT` also in 2: D049#session, D052#hooks
- **[ALSO: D045#polling-a-value]** | `STEP_NOT_AWAITED` | The test body settled while a step it started was still running: a step call without `await`. The step fails at the line of the call and is cancelled. The attempt fails with this code when the body returned. When the body threw, the attempt keeps the body's error and records t
    term `HOOK_FAILED` also in 2: D045#polling-a-value, D052#hooks
    term `STEP_NOT_AWAITED` also in 2: D014#core-concepts, D045#polling-a-value
    term `afterAll` also in 10: D020#rerunning-the-failed-tests, D033#map-each-api, D040#commands, D045#polling-a-value, D047#exported-types, D048#custom-reporters, D052#function-types, D052#hooks, D052#testapi, D053#types
    term `secondaryErrors` also in 3: D045#polling-a-value, D045#soft-assertions, D052#fixtures
- **[ONLY HERE]** | `UNHANDLED_REJECTION` | A promise rejected with no test running. Node cannot say which test created a promise, so an unhandled rejection is charged to the test running when it surfaces. Between tests it is this run error, naming the last test that finished in the worker as the likely source. Befor
    term `TEST_TIMEOUT` also in 2: D049#session, D052#hooks
- **[ONLY HERE]** | `HOOK_FAILED` | `beforeAll` or `afterAll` threw. Skips the suite's tests. | test | 1 |
    term `HOOK_FAILED` also in 2: D045#polling-a-value, D052#hooks
    term `afterAll` also in 10: D020#rerunning-the-failed-tests, D033#map-each-api, D040#commands, D045#polling-a-value, D047#exported-types, D048#custom-reporters, D052#function-types, D052#hooks, D052#testapi, D053#types
- **[ALSO: D041#top-level]** | `RUN_TIMEOUT` | The run spent its [`maxDuration`](/reference/config#maxduration) or `--max-duration`. The running tests end as `interrupted`, and the rest are skipped with cause `time-limit` | test | 1 |
    term `--max-duration` also in 5: D008#gate-pull-requests, D020#rerunning-the-failed-tests, D033#app-targets-and-output, D040#commands, D041#top-level
    term `RUN_TIMEOUT` also in 1: D041#top-level
    term `maxDuration` also in 6: D022#options, D022#sessions, D033#app-targets-and-output, D040#commands, D041#e2econfig, D041#top-level
    term `time-limit` also in 1: D041#top-level
- **[ONLY HERE]** | `LAUNCH_TIMEOUT` | Engine init or attempt start exceeded `config.launchTimeout` | infrastructure | 3 |
    term `LAUNCH_TIMEOUT` also in 2: D035#troubleshooting, D041#recording
- **[ONLY HERE]** | `CLEANUP_TIMEOUT` | Engine attempt end exceeded `config.cleanupTimeout`, or a route or dialog handler the engine ran for the test was still running when the attempt settled | infrastructure | 3 |
    term `CLEANUP_TIMEOUT` also in 1: D053#the-browser-fixture
- **[ONLY HERE]** | `BROWSER_INSTALL_FAILED` | Browser provisioning failed | infrastructure | 3 |
    term `BROWSER_INSTALL_FAILED` also in 1: D042#errors
- **[ONLY HERE]** | `WORKER_INIT_FAILED` | A worker process never became ready | infrastructure | 3 |
- **[ONLY HERE]** | `WORKER_EXIT` | A worker exited unexpectedly while running a file. The test in flight fails with `WORKER_CRASH`, and the file's other tests are skipped. Attempts that finished before the exit stay in the report, including a retry's earlier attempts and a serial group's finished members. The crash
    term `afterAll` also in 10: D020#rerunning-the-failed-tests, D033#map-each-api, D040#commands, D045#polling-a-value, D047#exported-types, D048#custom-reporters, D052#function-types, D052#hooks, D052#testapi, D053#types
- **[ONLY HERE]** | `WORKER_CRASH` | A worker exited during a specific test | infrastructure | 3 |
- **[ONLY HERE]** | `WORKER_ENTRY_MISSING` | The worker entry module could not be resolved. Packaging fault. | infrastructure | 3 |
- **[ONLY HERE]** | `NODE_UNSUPPORTED` | The runtime cannot run e2e's TypeScript loader: a Node.js outside `^22.22.3 \|\| >=24.8.0`, Bun (no `module.registerHooks`), or Deno. The CLI checks this before it starts and exits 2 with the same sentence. The loader checks again where it registers its hooks, for a host that
- **[ONLY HERE]** | `TYPESCRIPT_COMPILER_UNAVAILABLE` | oxc, which compiles e2e's TypeScript, could not be loaded; the message gives the cause. Most often its native bindings for this platform (`@oxc-transform/binding-<platform>-<arch>`, `@oxc-parser/binding-<platform>-<arch>`) are not installed. npm leaves them out
    term `node_modules` also in 5: D011#workflow, D013#install-the-skill, D027#run-the-app-in-the-machine, D040#commands, D041#top-level
    term `package-lock.json` also in 1: D012#ios-and-android
- **[ALSO: D035#troubleshooting, D044#agenterror]** | `ENGINE_FAILURE` | Any engine fault with no more specific mapping | infrastructure | 3 |
- **[ONLY HERE]** | `WORKER_PROTOCOL` | A worker reported the wrong unit, an attempt overlapped a live attempt, `openHost` tried to acquire an engine instance another host owns, or `host.openSession` tried to reuse a closed host or overlap an opening, live, or closing session | infrastructure | 3 |
    term `WORKER_PROTOCOL` also in 1: D049#host
    term `host.openSession` also in 3: D049#functions, D049#host, D049#session
    term `openHost` also in 5: D049#functions, D049#host, D049#playwright-test-fixtures, D049#reference-runner, D049#types
- **[ONLY HERE]** | `SESSION_KEY_INVALID` | A worker received a session key that is not 32 bytes. Packaging or IPC fault. | infrastructure | 3 |
- **[ALSO: D040#commands]** | `REPORT_WRITE_FAILED` | `report.json` or `ai-trace.json` could not be written. Recorded as a run error; the in-memory outcome is still complete. A `junit.xml` that could not be written is a line on the `junit` reporter's stderr instead | infrastructure | 3 |
    term `ai-trace.json` also in 4: D015#agent-steps, D040#commands, D041#output, D051#artifacts
- **[ONLY HERE]** | `EVALUATE_FAILED` | `browser.evaluate` threw inside the page (`@e2e-dev/web`) | test | 1 |
    term `EVALUATE_FAILED` also in 1: D053#the-browser-fixture
    term `browser.evaluate` also in 8: D005#read-from-the-page, D030#map-each-command, D033#map-each-api, D033#what-differs-on-purpose, D034#map-each-webdriver-call, D053#options, D053#the-browser-fixture, D059#scoping-a-test-to-one-size
- **[ALSO: D040#exit-codes]** | `INTERRUPTED` | A user or CI signal aborted the run. A test cut short by `--max-failures` or the time limit also ends with this code, and its message names the limit; that run exits 1, not 130 | interrupted | 130 |
    term `--max-failures` also in 5: D008#gate-pull-requests, D020#rerunning-the-failed-tests, D033#app-targets-and-output, D033#map-each-api, D040#commands
- **[ALSO: D044#agenterror]** | Code | When it happens | Class | Exit |
- **[ONLY HERE]** | `INVALID_ARGUMENT` | Argument validation in test code refused an argument | test | 1 |
- **[ONLY HERE]** | `INVALID_LOCATOR` | Argument validation in test code refused a locator's arguments | test | 1 |
    term `INVALID_LOCATOR` also in 8: D033#map-each-api, D042#errors, D042#shared-semantics, D050#locator-actions, D050#queries, D050#refinement, D050#screen-actions, D053#the-browser-fixture
- **[ONLY HERE]** | `ERROR` | A value thrown from test code that no other code classifies | test | 1 |

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D004#session-rules: Both say SESSION_CONTRACT is raised when a setup test saves a session twice, saves an undeclared name, or misses a declared one.
- D015#watch-it-happen: Both say UNSUPPORTED_ARTIFACT fails the run when a video mode is set on a target whose engine cannot record.
- D019#start-signed-in: Both involve e2e explore --session naming a session that must be produced by a setup test.
- D033#map-each-api: Both name ONLY_IN_CI as the error for a focused test in a CI run.
- D040#commands: Both name runner codes such as NO_TESTS, INVALID_GLOB, UNKNOWN_TARGET, CONFIG_NOT_FOUND, NO_LAST_RUN, COLLECTION_ERROR and RUN_TIMEOUT.
- D041#top-level: Both describe INVALID_GLOB, RUN_TIMEOUT from maxDuration with time-limit skips, LAUNCH_TIMEOUT and CLEANUP_TIMEOUT.
- D041#output: Both describe NO_LAST_RUN, NO_TESTS and UNSUPPORTED_ARTIFACT stops that leave the previous run's files.
- D041#artifacts: Both say the removed artifacts kinds list, artifacts.trace and artifacts.video forms fail with INVALID_CONFIG naming the trace or video option.
- D041#recording: Both state UNSUPPORTED_ARTIFACT when a target's engine cannot record a requested video mode.
- D004#session-rules: Both state SESSION_CONTRACT when a setup test saves a session twice, an undeclared name, or not a declared one.
- D008#what-ci-changes: Both state .only is rejected in CI with ONLY_IN_CI.
- D008#sharding: Both state a shard with no test fails with NO_TESTS.
- D014#core-concepts: Both state a step started without await fails with STEP_NOT_AWAITED.
- D015#watch-it-happen: Both describe UNSUPPORTED_ARTIFACT for --video on an engine that cannot record.
- D039#open: Both describe APP_URL_REQUIRED and UNSUPPORTED_CAPABILITY for app.open.
- D040#commands: Both describe NO_TESTS, NO_LAST_RUN, INVALID_GLOB, UNKNOWN_TARGET and CONFIG_NOT_FOUND causes for the CLI.
- D040#exit-codes: Both give the exit code per error class and the 130 interrupted code.
- D041#top-level: Both describe INVALID_GLOB, NO_TESTS, RUN_TIMEOUT and INVALID_CONFIG.
- D041#the-app-under-test: Both describe APP_URL_REQUIRED for app.command without url or readyUrl, and INVALID_APP_URL for port 0.
- D041#output: Both describe NO_TESTS, NO_LAST_RUN and UNSUPPORTED_ARTIFACT stops.
- D041#recording: Both state UNSUPPORTED_ARTIFACT for a video mode the engine cannot record, and LAUNCH_TIMEOUT.
- D041#ci: Both state test.only is rejected in CI with ONLY_IN_CI, exit code 2.
- D041#finding-the-config-file: Both state both e2e.config.ts and e2e.config.mts in one directory is CONFIG_AMBIGUOUS.
- D042#capabilities: Both describe UNSUPPORTED_CAPABILITY for a fixture, action or tier the engine does not declare.
- D043#run-mode: Both state a focused test is ONLY_IN_CI.
- D044#exit-codes: Both give the exit code per error class (configuration 2, infrastructure 3, interrupted 130).
- D045#polling-a-value: Both describe STEP_NOT_AWAITED for an expect.poll still running when the phase returned, and HOOK_FAILED in suite hooks.
- D046#flags: Both state several targets and no name is TARGET_REQUIRED.
- D046#the-catalog: Both state UNKNOWN_TOOL for a name not in the session's catalog.
- D046#sessions: Both describe NO_SESSION for a call before open_session or after the session ended.
- D046#several-sessions: Both define the MCP codes SESSION_REQUIRED, NO_SESSION, SESSION_OPEN, CONFIG_IN_USE and ENGINE_IN_USE.
- D049#functions: Both describe RUNNER_BUSY when another suite is running or a host is open, and NO_TESTS and exit codes.
- D049#host: Both describe WORKER_PROTOCOL for overlapping hosted attempts or a closed host.
- D051#tool-calls: Both state a defineTool without execute is rejected at config load.
- D052#members: Both describe ONLY_IN_CI and SESSION_CONTRACT for sessions not saved or saved twice.
- D052#hooks: Both describe HOOK_FAILED when a beforeAll/afterAll hook throws, skipping the suite's tests.
- D052#options: Both describe COLLECTION_ERROR for an unknown test option key naming the nearest key, and UNSUPPORTED_ARTIFACT.
- D053#the-browser-fixture: Both describe APP_URL_REQUIRED for a relative URL without app.url, and EVALUATE_FAILED when evaluate throws.
- D056#what-is-sent: Both mention CONFIG_NOT_FOUND and INVALID_CONFIG as runner codes that stop a command.
- D046#exit-codes: Both state that config and engine failures carry the same runner codes and exit codes as the CLI.
- D049#functions: Both define RUNNER_BUSY, UNKNOWN_TARGET, TARGET_REQUIRED and NO_TESTS conditions for run, list and openHost.
- D049#host: Both describe WORKER_PROTOCOL for overlapping hosted attempts or use of a closed host.
- D049#session: Both define TEST_TIMEOUT as the outcome when the attempt deadline passes.
- D051#sessions: Both say a stored session past its expiry or mismatched is refused (SESSION_EXPIRED).
- D052#hooks: Both describe HOOK_FAILED for beforeAll/afterAll and the worker being killed for a blocked event loop after cleanupTimeout.
- D052#options: Both describe UNSUPPORTED_ARTIFACT for a video mode and COLLECTION_ERROR for forbidden serial options.
- D052#fixtures: Both cover COLLECTION_ERROR for an invalid fixture definition and timeouts of abandoned bodies.
- D052#testoptions: Both describe COLLECTION_ERROR for malformed options and nested serial groups.
- D053#the-browser-fixture: Both define EVALUATE_FAILED and APP_URL_REQUIRED.

## S40 · single · D053#browser-interface  (Browser › Types › `Browser` interface; page title: Browser)

Regel: genau ein Abschnitt, dessen Hauptinhalt die Antwort ist; jeder Teil der Antwort muss nur hier stehen.

**Typ-Eignung:** Schwacher Slot. Fast alles steht auch in D053#the-browser-fixture: aktiver Tab gegen ganzer Browser, nicht gefolgte Tabs, die Methodenliste mit Rückgabetypen und `keyboard`/`mouse` mit den Namen `{ press, down, up, type }` und `{ move, wheel, down, up }`. Dazu kommen D005 (Rezepte zu `route`, `onDialog`, `waitForDownload`, `addInitScript`, `emulateMedia`, `setCookies`) und D053#options; „from the next navigation on“ bei `addInitScript` steht auch in D053#options. Nur hier stehen die Beschreibungen der `keyboard`- und `mouse`-Methoden, z. B. „Holds one key until up; repeated down calls send a repeat event.“ (`find "repeat event"`: nur hier). D053#the-browser-fixture verweist dafür ausdrücklich auf dieses Interface („[`Browser`](#browser-interface) describes each method“). Ziel `procedural`: eine Taste halten und wieder loslassen. Die Antwort muss auf den Beschreibungen beruhen, nicht nur auf den Methodennamen, denn die stehen auch in D053#the-browser-fixture. Prüfe, ob `single` (Hauptinhalt) hier trägt; ein Sprunggrund passt nicht sauber, weil einzelne Inhalte nur hier stehen.

*(Nur Codeblock: der mechanische Teil prüft keine Codeblöcke. Die Kommentare im Code sind mit `catalogue.py find` und durch Lesen gegen den Korpus geprüft; das Ergebnis steht in der Typ-Eignung.)*

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D005#run-a-script-before-the-page: Both describe browser.addInitScript adding a script that runs before the page's own scripts.
- D033#map-each-api: Both list browser methods such as locator, frameLocator, evaluate, waitForResponse, waitForDownload, onDialog and addInitScript.
- D045#expectcall-softexpectcall-and-expect: Both show the browser fixture as Expectable, so expect(browser) returns matchers.
- D053#the-browser-fixture: Both describe the Browser methods, active tab scope, keyboard and mouse input and evaluate.
- D005#mock-an-api: Both describe browser.route handlers, waitForResponse and unroute for mocking network requests.
- D005#handle-a-dialog: Both describe browser.onDialog registering an accept, dismiss or function handler with an unsubscribe function.
- D005#download-a-file: Both describe browser.waitForDownload returning path, absolutePath and suggestedFilename.
- D005#reach-into-an-iframe: Both describe frameLocator creating a query scope inside one iframe.
- D005#read-from-the-page: Both say browser.evaluate runs a serialized function in the page and takes data through an argument.
- D005#run-a-script-before-the-page: Both describe browser.addInitScript running before the page's own scripts.
- D005#emulate-dark-mode-and-reduced-motion: Both describe emulateMedia for colorScheme and reducedMotion.
- D005#cookies: Both describe browser.setCookies validating cookie URLs.
- D033#map-each-api: Both map Playwright page/context calls to browser.route, onDialog, waitForDownload, keyboard, mouse, evaluate and setViewport.
- D033#port-page-objects: Both describe browser.keyboard press and type, plain text only, never a Secret.
- D053#options: Both describe emulateMedia, addInitScript and the init script forms, and setViewport for the attempt.
- D053#the-browser-fixture: Both describe browser methods (goto, reload, evaluate, route, cookies, setViewport, emulateMedia, onDialog, waitForDownload, keyboard, mouse) and active-tab versus whole-browser scope.
- D059#resize-inside-a-test: Both describe browser.setViewport for the rest of the attempt.

## Reserve für S37 (Project, Zug 13) · single · D051#outbound-connections  (Security rules › Reference › Outbound connections; page title: Security rules)

Regel: genau ein Abschnitt, dessen Hauptinhalt die Antwort ist; jeder Teil der Antwort muss nur hier stehen.

**Typ-Eignung:** Nur relevant, wenn S37 übersprungen wird. Hauptinhalt: die Ziele, die e2e kontaktiert, je mit Bedingung. Vorsicht: D054#what-leaves-your-computer fasst Modellanbieter, App, Telemetrie (`eu.i.posthog.com`), `registry.npmjs.org` nur bei `e2e feedback` und „no crash reporting“ zusammen. Weitere Teile stehen in D056 und D043#telemetry (Telemetrie), D027#set-up-the-provider (smol), D022#authenticate (`EXPO_TOKEN`), D043#engines (Limrun-Host), D053#installing-browsers (Browser-Download), D041#the-app-under-test und D059 (`readyUrl`), D020#when-nothing-is-posted (GitHub-API). Nur hier (mit `find` geprüft): die Sign-in- und Model-List-Endpunkte bei `e2e login` und `e2e models`, die Kernel-API nur über `kernel()`, „Your test code, plugins, and app can make more connections“. Eignung: `limitation` (was die Liste nicht abdeckt) oder `factual` (nur noch ein Platz frei); `conceptual` trägt die Tabelle kaum, weil sie Bedingungen nennt, keine Gründe.

- **[ONLY HERE]** ### Outbound connections **Note** There is no crash reporting, and no update check outside `e2e feedback`.
    term `e2e feedback` also in 4: D040#commands, D040#exit-codes, D054#what-leaves-your-computer, D056#feedback
- **[ONLY HERE]** `--ai-trace` writes a local file and doesn't upload it.
    term `--ai-trace` also in 6: D013#how-an-agent-reads-a-failure, D015#agent-steps, D040#commands, D041#output, D043#diagnostics, D051#artifacts
- **[ONLY HERE]** Your test code, plugins, and app can make more connections.
- **[ALSO: D054#what-leaves-your-computer]** | `eu.i.posthog.com` | One telemetry request per CLI invocation or per `run()` from `e2e/runner` that returns a report, plus at most one per session `e2e mcp` serves, unless you opt out ([Telemetry](/telemetry)). One request per `e2e feedback` report sent: none under `--dry-run` or `E2E_TELEMETRY_DE
    term `--dry-run` also in 2: D040#commands, D056#feedback
    term `--repro` also in 2: D040#commands, D056#feedback
    term `DO_NOT_TRACK` also in 4: D040#commands, D043#telemetry, D056#feedback, D056#opt-out
    term `E2E_TELEMETRY_DEBUG` also in 3: D040#commands, D043#telemetry, D056#see-what-would-be-sent
    term `E2E_TELEMETRY_DISABLED` also in 8: D008#what-ci-changes, D040#commands, D043#reference-environment, D043#telemetry, D056#feedback, D056#in-a-fleet, D056#in-ci, D056#opt-out
    term `e2e feedback` also in 4: D040#commands, D040#exit-codes, D054#what-leaves-your-computer, D056#feedback
    term `e2e/runner` also in 8: D040#commands, D044#runner-codes, D049#functions, D049#playwright-test-fixtures, D049#reference-runner, D049#types, D056#the-notice, D056#what-is-sent
    term `eu.i.posthog.com` also in 2: D054#what-leaves-your-computer, D056#where-it-goes
    term `run()` also in 4: D026#configure-a-target, D043#engines, D056#the-notice, D056#what-is-sent
- **[ONLY HERE]** | Your model provider | Agent steps that call a model. Deterministic tests and fully replayed steps make no model call. |
- **[ONLY HERE]** | A subscription provider's sign-in and model-list endpoints | `e2e login` and `e2e models` ([Subscriptions](/subscriptions)). |
    term `e2e models` also in 5: D040#commands, D043#model, D044#exit-codes, D044#reference-errors, D055#pick-a-model
- **[ONLY HERE]** | The app's `readyUrl` | Readiness probes for an app the runner starts. |
    term `readyUrl` also in 7: D035#expo-development-builds, D041#the-app-under-test, D042#app, D044#agenterror, D044#runner-codes, D046#several-sessions, D059#let-the-runner-start-it
- **[ONLY HERE]** | Playwright's browser download | One time, when the browser is missing. |
- **[ONLY HERE]** | The DevTools endpoint in `web({ connect })` | Every run of that target. |
    term `web({ connect })` also in 3: D033#browser-timeouts-and-artifacts, D034#port-the-config, D044#runner-codes
- **[ONLY HERE]** | The GitHub API | Only from the `@e2e-dev/github` reporter. |
    term `@e2e-dev/github` also in 9: D012#pull-request-comments, D020#github, D020#setup, D040#commands, D043#reporters, D048#built-in-reporters, D048#custom-reporters, D048#reference-reporters, D048#related
- **[ONLY HERE]** | `registry.npmjs.org` | One request per `e2e feedback` you run, to check for a newer e2e release. Skipped with `--allow-outdated` and under `E2E_TELEMETRY_DISABLED` or `DO_NOT_TRACK`. |
    term `--allow-outdated` also in 1: D040#commands
    term `DO_NOT_TRACK` also in 4: D040#commands, D043#telemetry, D056#feedback, D056#opt-out
    term `E2E_TELEMETRY_DISABLED` also in 8: D008#what-ci-changes, D040#commands, D043#reference-environment, D043#telemetry, D056#feedback, D056#in-a-fleet, D056#in-ci, D056#opt-out
    term `e2e feedback` also in 4: D040#commands, D040#exit-codes, D054#what-leaves-your-computer, D056#feedback
    term `registry.npmjs.org` also in 1: D054#what-leaves-your-computer
- **[ONLY HERE]** | `api.limrun.com` (or `LIMRUN_BASE_URL`) and its devices | Only from [`limrun()`](/integrations/limrun). It signs in with `LIMRUN_API_KEY`. |
    term `LIMRUN_API_KEY` also in 2: D026#install-and-authenticate, D043#engines
    term `LIMRUN_BASE_URL` also in 1: D043#engines
    term `api.limrun.com` also in 1: D043#engines
    term `limrun()` also in 2: D026#configure-a-target, D043#engines
- **[ONLY HERE]** | The Kernel API and its hosted browsers | Only from [`kernel()`](/integrations/kernel). |
    term `kernel()` also in 4: D005#hosted-browsers, D024#integrations-kernel, D024#setup, D043#engines
- **[ONLY HERE]** | The Expo API and the simulators' agent-device daemons | Only from [`easSimulators()`](/integrations/eas). It signs in with `EXPO_TOKEN`, else with the eas-cli login in `~/.expo/state.json`. On a CI runner, set `EXPO_TOKEN` or keep that login out of the runner's home. |
    term `EXPO_TOKEN` also in 3: D022#authenticate, D022#when-a-session-fails-to-start, D043#engines
    term `easSimulators()` also in 5: D022#install-the-app, D022#integrations-eas, D022#setup, D035#hosted-devices, D043#engines
    term `~/.expo/state.json` also in 1: D022#authenticate
- **[ONLY HERE]** | `mcr.microsoft.com` | Only from [`smol()`](/integrations/smol), to pull the Playwright image. The machines then have unrestricted network access, and reach every port on your computer's loopback through `host.smolvm.internal`, not only `hostPorts` ([Set up the provider](/integrations/smol#set-up-t
    term `host.smolvm.internal` also in 1: D027#set-up-the-provider
    term `hostPorts` also in 4: D027#options, D027#run-the-app-in-the-machine, D027#set-up-the-provider, D027#start-every-test-signed-in
    term `smol()` also in 3: D005#hosted-browsers, D027#integrations-smol, D027#set-up-the-provider
- **[ONLY HERE]** | The package registry | When `e2e init` installs dependencies. |
- **[ONLY HERE]** | The app under test | Every run, plus whatever the app itself loads. |

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D027#set-up-the-provider: Both say smol machines pull the Playwright image, have unrestricted outbound network access, and reach any loopback port via host.smolvm.internal.
- D040#commands: Both describe e2e feedback, e2e models and --ai-trace network use.
- D001#what-a-step-costs: Both say replayed agent steps make no model call.
- D007#how-a-replay-works: Both say a replayed step finishes without a model call.
- D014#locators: Both say locators and deterministic tests make no model call.
- D015#agent-steps: Both say a replayed step makes no model call, and --ai-trace is the opt-in trace.
- D022#authenticate: Both say EAS simulators sign in with EXPO_TOKEN or the eas-cli login in ~/.expo/state.json.
- D027#set-up-the-provider: Both warn the smol machines have unrestricted network access and reach host loopback ports, not only hostPorts.
- D040#commands: Both describe e2e feedback --dry-run, --allow-outdated and the npm registry check for a newer release.
- D041#the-app-under-test: Both describe the readyUrl readiness probe of an app the runner starts.
- D043#telemetry: Both describe E2E_TELEMETRY_DEBUG and E2E_TELEMETRY_DISABLED/DO_NOT_TRACK controlling telemetry sending.
- D043#engines: Both give LIMRUN_BASE_URL as the Limrun API host defaulting to api.limrun.com.
- D051#artifacts: Both say --ai-trace is opt-in, writes a local file and is not uploaded.
- D053#installing-browsers: Both say a missing Playwright browser is downloaded once.
- D054#what-leaves-your-computer: Both list the destinations a run contacts: model provider, app under test, PostHog telemetry, and npm registry only for e2e feedback.
- D056#opt-out: Both say telemetry is skipped under E2E_TELEMETRY_DISABLED or DO_NOT_TRACK.
- D056#see-what-would-be-sent: Both mention E2E_TELEMETRY_DEBUG preventing telemetry from being sent.
- D056#what-is-sent: Both state telemetry is one request per CLI invocation or run() that returns a report, plus MCP sessions.
- D056#where-it-goes: Both name eu.i.posthog.com as the telemetry destination.
- D056#feedback: Both describe e2e feedback sending one event to PostHog, with dry-run and opt-out exceptions.
- D059#let-the-runner-start-it: Both describe readyUrl as the health endpoint the runner probes for a started app.
- D056#what-is-sent: Both state when telemetry requests are sent: per CLI invocation, per run() and per MCP session.
