# Vorbereitungsblatt Block 2 (S09–S16)

KI-Hilfe (Claude) vor dem Schreiben, offengelegt nach ADR 0031/0049, wie das Blatt zu Block 1. Rein mechanisch: je Satz
des Ausgangsabschnitts (ohne Codeblöcke), ob eine Folge von 5 Wörtern auch im eigenen Text eines anderen Abschnitts
steht (außer umschließenden und enthaltenen Abschnitten), und für Begriffe in Backticks, in welchen anderen
Abschnitten sie vorkommen (nur bei höchstens 10 Treffern gelistet, dann vollständig). Dazu die Zeilen aus
`catalogue_overlap.csv`. Es enthält keine Frage, keine Antwort, keinen Typ und kein Relevanzurteil. „ONLY HERE“ heißt
nur: kein wörtlicher Treffer; anders formulierte Stellen mit gleichem Inhalt findet es nicht (dafür „Also covered
elsewhere“ im Editor). Erstellt am 09.11.2026.

## S09 · detail · D011#workflow  (EAS Workflows › Workflow; page title: EAS Workflows)

Regel: genau ein Abschnitt, ein einzelnes Faktum, Referenzantwort höchstens 30 Wörter; das Faktum muss nur hier stehen.

- **[ONLY HERE]** ## Workflow The Android job needs a `nested-virtualization` Linux runner, the only EAS machine that can run the emulator.
- **[ONLY HERE]** Use custom jobs, as below.
- **[ONLY HERE]** The built-in `maestro` job type runs Maestro flows, not e2e.
    term `maestro` also in 3: D013#migrate-an-existing-suite, D032#migrate-maestro, D032#port-the-config
- **[ONLY HERE]** **.eas/workflows/e2e.yml** `CI: '1'` turns on the [CI defaults](/ci#what-ci-changes) on a runner that doesn't set `CI`.
    term `CI: '1'` also in 1: D049#functions
- **[ONLY HERE]** `eas/start_android_emulator` is an EAS build function, documented under [custom builds](https://docs.expo.dev/custom-builds/schema/), not on the Workflows syntax page.
- **[ONLY HERE]** It downloads the system image you name with `sdkmanager`.

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D008#upload-the-reports: Both upload the .e2e output as a CI artifact even when the run fails.
- D008#mobile-jobs: Both say the Android emulator needs a Linux runner with nested virtualization and iOS needs a macOS runner with a booted simulator.
- D009#workflow: Both give a CI workflow building iOS and Android apps, installing them on a simulator or emulator and running npx e2e run --target with junit.
- D010#workflow: Both create an iPhone 17 simulator via xcrun simctl, install the app and run npx e2e run --target ios and android with junit.
- D011#build-profile: Both rely on an e2e build profile producing a simulator iOS build and an Android apk without credentials.
- D012#ios-and-android: Both give a CI workflow with one job per platform that boots a simulator or emulator, installs the build and runs npx e2e run --target.

## S10 · paraphrase · D010#workflow  (Codemagic › Workflow; page title: Codemagic)

Regel: genau ein Abschnitt; die Frage teilt kein Inhaltswort mit der Abschnittsüberschrift oder dem Seitentitel (auch keine Wortformen).

- **[ONLY HERE]** ## Workflow The Ubuntu image has AVDs named `emulator` (API 34), `emulator-35`, and `emulator-36`.
- **[ONLY HERE]** Linux instances need billing enabled.
- **[ONLY HERE]** `test_report` sends `junit.xml` to the Tests tab of the build.

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D008#upload-the-reports: Both upload .e2e/report.json, junit.xml and results as CI artifacts and point the CI test report at junit.xml.
- D008#mobile-jobs: Both describe mobile CI jobs: macOS simulator and Linux emulator, install the build, then run npx e2e run --target ios or android.
- D009#workflow: Both give a CI workflow for iOS and Android that boots a simulator or emulator, installs the app and runs npx e2e run per target with junit.
- D009#artifacts-and-test-reports: Both send junit.xml to the CI service's test report tab and keep the .e2e output as build artifacts.
- D011#workflow: Both give a CI workflow building iOS and Android apps, installing them on a simulator or emulator and running npx e2e run --target with junit.
- D012#ios-and-android: Both create an iPhone 17 simulator on a named iOS runtime via xcrun simctl and run npx e2e run --target ios and android with junit.

## S11 · single · D026#choose-device-options  (Test mobile apps on Limrun › Choose device options; page title: Test mobile apps on Limrun)

Regel: genau ein Abschnitt, dessen Hauptinhalt die Antwort ist; kein anderer Abschnitt enthält sie.

- **[ONLY HERE]** ## Choose device options | Option | Default | Purpose | | --- | --- | --- | | `region` | Limrun selects | Region preference, such as `eu` or `us-east1`.
    term `region` also in 6: D036#ai-sdk-providers, D037#use-a-subscription-or-api-key, D038#vision, D050#locator-actions, D050#queries, D050#types
- **[ONLY HERE]** Capacity may cause overflow to another region.
- **[ONLY HERE]** | | `hardTimeout` | `1h` | Maximum device lifetime, including abandoned runs.
- **[ONLY HERE]** Use a Go duration such as `30m` or `2h`.
- **[ONLY HERE]** | | `ios.model` | Limrun selects | `iphone` or `ipad`.
    term `iphone` also in 9: D010#workflow, D012#ios-and-android, D035#agent-tools, D035#hosted-devices, D035#several-devices, D047#agent-tools, D047#engine, D047#reference-mobile, D057#device-toolkits
- **[ONLY HERE]** | | `android.model` | Limrun selects | `phone` or `tablet`.
    term `tablet` also in 1: D059#one-size-per-target
- **[ONLY HERE]** | | `android.osVersion` | `15` | Android major version requested as a scheduling clue.
- **[ONLY HERE]** | Each worker gets an isolated agent-device daemon on the test runner and one Limrun instance.
- **[ONLY HERE]** The daemon uses agent-device's Limrun driver for app control and recording.
- **[ONLY HERE]** The integration pins the same agent-device version as the mobile engine and checks that before allocation.
- **[ONLY HERE]** A device must become ready and finish installation within five minutes.
- **[ONLY HERE]** The provider cleans up after failed setup and the engine releases all acquired devices when the run finishes or is interrupted.
- **[ONLY HERE]** The provider renews idle driver leases while other targets run.
- **[ONLY HERE]** The daemon keeps an active device alive between commands; the hard timeout remains the upper bound if the runner disappears.
- **[ONLY HERE]** Choose a timeout longer than the run.
- **[ONLY HERE]** Instance IDs appear in progress output.
- **[ONLY HERE]** Find a run's instances by the `source=e2e` and `run=<run id>` labels in Limrun.
- **[ONLY HERE]** Recordings use the normal mobile artifact path, `video/video.mp4` inside each attempt directory.
    term `video/video.mp4` also in 3: D022#recordings, D041#recording, D047#engine

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D005#pick-a-lease-scope: Both say leases are released on every exit path, including failure and interrupt.
- D022#options: Both give a maximum session lifetime option for hosted simulator sessions and device selection options.
- D022#recordings: Both say recordings are written as video/video.mp4 inside each attempt's artifact directory.
- D028#limits: Both say a hosted device ends on a timeout if the runner disappears before releasing it.
- D035#hosted-devices: Both say the hosted device provider releases acquired devices when the run finishes or is interrupted, with Limrun cleaning up devices.

## S12 · detail · D022#sessions  (EAS Simulators › Sessions; page title: EAS Simulators)

Regel: genau ein Abschnitt, ein einzelnes Faktum, Referenzantwort höchstens 30 Wörter; das Faktum muss nur hier stehen.

- **[ONLY HERE]** ## Sessions Each target starts up to `workers` sessions, fewer when it has fewer test files.
- [ALSO: D047#engine, D053#installing-browsers] They start in parallel before the run's clock starts, and take about three minutes each (queue, boot, build install).
- **[ONLY HERE]** Tests start when all are ready.
- **[ONLY HERE]** A run must fit in one session, because EAS stops a session `maxDurationMinutes` after it is ready.
    term `maxDurationMinutes` also in 1: D022#options
- **[ONLY HERE]** Split a longer suite across more workers or CI jobs.
- **[ONLY HERE]** EAS queues sessions beyond the account's concurrency limit.
- [ALSO: D028#limits] No session ends before the run does, so keep `workers` times the number of EAS targets within that limit:
- **[ONLY HERE]** - A session still queued after two minutes logs `still queued at EAS after two minutes`.
- **[ONLY HERE]** - Targets prepare one after another, so one target's ready sessions idle while the next target's queue and boot.
- **[ONLY HERE]** - A session still queued when another has been ready for `maxIdleTimeMinutes` fails the lease, because EAS may be stopping the idle one.
    term `maxIdleTimeMinutes` also in 1: D022#options
- **[ONLY HERE]** The run then stops every session.

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D005#pick-a-lease-scope: Both say hosted sessions cost money while they run, so keep workers at what the suite can fill.
- D022#options: Both describe maxDurationMinutes and maxIdleTimeMinutes, how long EAS lets a session run or sit idle.
- D022#when-a-session-fails-to-start: Both say a session that stays queued too long fails and the run's other sessions are stopped.
- D028#limits: Both say to keep workers times the number of targets within the service's parallel session limit.
- D035#hosted-devices: Both say each worker leases its own hosted session and to keep workers at what the suite can fill.

## S13 · detail · D057#declare-what-a-tool-does  (Project tools › Declare what a tool does; page title: Project tools)

Regel: genau ein Abschnitt, ein einzelnes Faktum, Referenzantwort höchstens 30 Wörter; das Faktum muss nur hier stehen.

- **[ONLY HERE]** ## Declare what a tool does `defineTool` takes the AI SDK tool and these annotations:
    term `defineTool` also in 9: D041#agentconfig, D041#agents, D042#actions, D044#runner-codes, D046#the-catalog, D051#tool-calls, D057#add-a-tool, D057#observe-from-a-tool, D060#ship-a-tool-pack
- **[ONLY HERE]** | Annotation | Meaning | | --- | --- | | `mutates: true` | Changes state.
    term `mutates: true` also in 3: D018#driving-the-page-yourself, D057#add-a-tool, D057#observe-from-a-tool
- **[ONLY HERE]** The call takes a slot of the step's action budget before it runs, failed or not, and runs in order with the other actions.
- **[ONLY HERE]** The [replay cache](/cache) can't replay it, so the agent runs that part of the step live.
- **[ONLY HERE]** Runs without an action slot and may observe the screen.
- **[ONLY HERE]** | | `platforms: ['ios', 'android']` | Offers the tool only on those platforms.
- **[ONLY HERE]** Omit it to offer the tool on every target.

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D018#keep-the-loop-change-the-vocabulary: Both say a mutating tool takes an action slot of the step's budget and cannot be replayed from the cache.
- D041#agentconfig: Both define tool annotations mutates and platforms.
- D057#add-a-tool: Both show defineTool with the mutates annotation true for a state-changing tool.
- D057#observe-from-a-tool: Both say a mutates: false tool is read-only and observation is not allowed in a mutates: true tool.
- D060#ship-a-tool-pack: Both say project tools use platforms to offer a tool only on matching platforms.

## S14 · detail · D056#what-is-sent  (Telemetry › What is sent; page title: Telemetry)

Regel: genau ein Abschnitt, ein einzelnes Faktum, Referenzantwort höchstens 30 Wörter; das Faktum muss nur hier stehen.

- **[ONLY HERE]** ## What is sent Each command sends one `e2e_cli_session` event.
- **[ONLY HERE]** `run` and `explore` also send `e2e_run_completed`, `init` sends `e2e_init_completed`, and `mcp` sends one `e2e_mcp_session` per MCP session.
    term `e2e_run_completed` also in 1: D049#functions
- **[ONLY HERE]** `--help` and `--version` send nothing, on any command.
    term `--help` also in 2: D040#help-and-version, D040#reference-cli
    term `--version` also in 1: D040#help-and-version
- **[ONLY HERE]** `run()` from `e2e/runner` sends no session event, only one `e2e_run_completed` per run that returns a report.
    term `e2e/runner` also in 8: D040#commands, D044#runner-codes, D049#functions, D049#playwright-test-fixtures, D049#reference-runner, D049#types, D051#outbound-connections, D056#the-notice
    term `e2e_run_completed` also in 1: D049#functions
    term `run()` also in 4: D026#configure-a-target, D043#engines, D051#outbound-connections, D056#the-notice
- **[ONLY HERE]** The events go in one request when the command or `run()` ends, with a two-second deadline.
    term `run()` also in 4: D026#configure-a-target, D043#engines, D051#outbound-connections, D056#the-notice
- **[ONLY HERE]** `e2e mcp` sends each session event in its own request, and `e2e run --watch` sends each run's event when that run ends.
    term `e2e run --watch` also in 1: D040#commands
- **[ONLY HERE]** Events hold only the properties below.
- [ALSO: D043#telemetry] An error code that isn't an upper-case token is sent as `OTHER`.
- **[ONLY HERE]** An engine, platform, model, fleet, or MCP client name, or an MCP client version, that isn't a plain token of letters, digits, dots, dashes, and underscores is sent as `other`.
- **[ONLY HERE]** An engine version that isn't semver is sent as `unversioned`.
- **[ONLY HERE]** In action and tool call counts, a project's own tools count together as `tool`, and any other name as `other`.
- **[ONLY HERE]** **Every event** | Property | Value | | --- | --- | | `distinct_id` | A random id stored in the preferences file.
- **[ONLY HERE]** CI uses `ci:<vendor>` instead, and a fleet uses `fleet:<name>` (see [In a fleet](#in-a-fleet)) | | `project_id` | A hash of the repository's root commit, shared across full clones.
    term `fleet:<name>` also in 2: D043#telemetry, D056#in-a-fleet
- **[ONLY HERE]** `null` outside git and in a shallow clone | | `session_id` | A random id for this one invocation | | `first_run`, `days_since_first_run` | Whether this command created the preferences file, and whole days since then.
- **[ONLY HERE]** `null` in CI, in a fleet, and for a preferences file from before the time was recorded | | `os`, `os_release`, `arch`, `cpu_count`, `memory_gb`, `docker`, `wsl`, `tty` | The machine class | | `sandbox` | The microVM the kernel announces itself as (`firecracker`), else `null` | | `ci`, `ci_name` | Wh
    term `E2E_TELEMETRY_FLEET` also in 2: D043#telemetry, D056#in-a-fleet
    term `ci_name` also in 1: D043#telemetry
    term `circleci` also in 1: D043#telemetry
    term `claude-code` also in 1: D043#telemetry
    term `codex` also in 4: D013#install-the-skill, D029#set-it-up, D043#telemetry, D046#setup
    term `coding_agent` also in 1: D043#telemetry
    term `cursor` also in 5: D013#generate-a-verification-skill-for-your-app, D029#set-it-up, D040#commands, D043#telemetry, D046#setup
    term `docker` also in 1: D025#attach-to-a-running-server
    term `fleet` also in 3: D040#commands, D043#telemetry, D056#in-a-fleet
    term `gitlab` also in 1: D043#telemetry
    term `package_manager` also in 1: D043#telemetry
    term `sandbox` also in 1: D054#what-runs-with-your-permissions
    term `wsl` also in 2: D019#read-the-results, D043#telemetry
- **[ONLY HERE]** `node_version` is Node's own version, or the Node compatibility version under Bun or Deno | | `$lib`, `$lib_version`, `$process_person_profile`, `$geoip_disable` | `e2e`, its version, `false`, and `true`:
- [ALSO: D056#where-it-goes] PostHog keeps no person profile and derives no location | **e2e_cli_session, once per command** | Property | Value | | --- | --- | | `command` | `init`, `run`, `list`, `cache ls`, `guide`, `telemetry`, ...
    term `cache ls` also in 3: D007#inspect-the-cache, D007#next, D040#commands
- **[ONLY HERE]** | | `flags` | The names of the flags given, such as `--headed` or `--tag`.
    term `--tag` also in 7: D022#watch-a-run, D032#port-the-config, D033#map-each-api, D040#commands, D049#functions, D052#options, D052#testoptions
- [ALSO: D040#commands] Never their values | | `exit_code`, `duration_ms` | How the command ended and how long it took | | `error_code` | The runner code of the failure that stopped the command before it could run (`CONFIG_NOT_FOUND`, `INVALID_CONFIG`, ...), `CLI_USAGE` for a flag or argument the CLI rejected, else `null`
    term `--yes` also in 7: D030#migrate-cypress, D031#migrate-detox, D032#migrate-maestro, D033#migrate-playwright, D034#migrate-selenium, D037#set-up-with-your-coding-agent, D040#commands
    term `CONFIG_NOT_FOUND` also in 2: D040#commands, D044#runner-codes
    term `chatgpt` also in 2: D040#commands, D055#set-up
    term `copilot` also in 6: D037#use-a-subscription-or-api-key, D040#commands, D043#telemetry, D055#pick-a-model, D055#set-up, D055#subscriptions
    term `grok` also in 5: D036#ai-sdk-providers, D037#use-a-subscription-or-api-key, D040#commands, D055#set-up, D059#protected-previews
    term `openai-compatible` also in 6: D036#ai-sdk-providers, D036#pick-a-gateway-or-a-provider, D037#use-a-subscription-or-api-key, D040#commands, D041#agents, D055#set-up
    term `opencode-console` also in 7: D037#use-a-subscription-or-api-key, D040#commands, D043#model, D055#pick-a-model, D055#set-up, D055#sign-in-help, D055#subscriptions
    term `openrouter` also in 8: D016#install-and-configure, D016#vision, D036#ai-sdk-providers, D036#pick-a-gateway-or-a-provider, D037#use-a-subscription-or-api-key, D040#commands, D041#agents, D043#model
    term `scaffolded` also in 3: D033#defaults-that-differ, D041#resolution-order, D043#what-app-processes-inherit
- **[ONLY HERE]** Never the endpoint typed for an OpenAI-compatible gateway | | `skill`, `mcp`, `install` | Whether the agent skill, the MCP registration, and the dependency install were chosen | **e2e_run_completed, once per e2e run, e2e explore, or completed run()** | Property | Value | | --- | --- | | `command` |
    term `e2e/runner` also in 8: D040#commands, D044#runner-codes, D049#functions, D049#playwright-test-fixtures, D049#reference-runner, D049#types, D051#outbound-connections, D056#the-notice
    term `run()` also in 4: D026#configure-a-target, D043#engines, D051#outbound-connections, D056#the-notice
- **[ONLY HERE]** `web`, `ios`, `web@0.6.1`, or your own engine's name and version | | `steps_total`, `steps_agent`, `steps_locator`, `steps_assertion`, `steps_screen`, `steps_app`, `steps_session`, `steps_resource` | Step counts by kind | | `steps_agent_act`, `steps_agent_assert`, `steps_agent_extract`, `steps_agent
- **[ONLY HERE]** `{"no-entry": 3, "retry": 1}` | | `tests_code_only`, `tests_replayed`, `tests_assisted`, `tests_live` | The executed tests by how the cache carried them: no agent step, every agent step replayed from the cache, the agent ran but the cache carried part of a step, the agent ran every agent step | | `a
- **[ONLY HERE]** `{"tap": 12, "typeText": 3, "scroll": 2}` | | `model_gateway`, `model_provider`, `model_id`, `model_calls`, `model_tokens`, `model_cached_tokens`, `estimated_cost_usd` | For the first model-backed step: the AI SDK provider that served it (`gateway` for the Vercel AI Gateway, `openrouter.chat`, `open
- **[ONLY HERE]** Then the run's totals | | `model_calls_act`, `model_calls_assert`, `model_calls_extract`, `model_calls_waitfor` | The model calls by agent entry point | | `cost_source` | `provider` when the provider priced the calls, `none` when nobody priced them, `null` for a run without model calls | | `artifact
    term `APP_UNREACHABLE` also in 7: D008#upload-the-reports, D015#common-errors, D035#troubleshooting, D038#agent-act, D039#open, D041#the-app-under-test, D044#agenterror
- **[ONLY HERE]** `null` for a clean run | | `error_kinds` | For `ENGINE_FAILURE`, `MODEL_PROVIDER_FAILED`, and `ERROR`: the code and a kind read off the message against a closed list (`auth`, `rate-limit`, `overloaded`, `timeout`, `network`, `server`, `bad-request`, `device`, `daemon`, `browser`, `permission`, `not-
    term `MODEL_PROVIDER_FAILED` also in 6: D007#when-a-recording-is-written, D015#common-errors, D036#what-fails-and-where, D038#agent-act, D044#agenterror, D055#sign-in-help
    term `daemon` also in 9: D022#install-the-app, D022#integrations-eas, D022#options, D026#choose-device-options, D035#hosted-devices, D035#physical-devices, D035#troubleshooting, D047#engine, D051#outbound-connections
    term `not-found` also in 4: D007#fail-on-a-stale-recording, D007#why-a-step-was-not-replayed, D038#types, D044#agenterror
- **[ONLY HERE]** Only the kind's name leaves the machine, never the message | Config features, absent when the config didn't load.
- **[ONLY HERE]** Each is a count, a boolean, or one of the runner's own option values, never text you wrote:
- [ALSO: D041#recording] | Property | Value | | --- | --- | | `config_workers`, `config_retries` | The worker count and retries the run resolved | | `config_agents`, `config_custom_executor`, `config_separate_judge`, `config_project_tools` | How many agents are configured, whether any has a custom executor or a judge model
    term `on-all-retries` also in 5: D033#browser-timeouts-and-artifacts, D040#commands, D041#artifacts, D041#recording, D052#options
    term `on-first-retry` also in 6: D015#watch-it-happen, D033#browser-timeouts-and-artifacts, D033#defaults-that-differ, D040#commands, D041#recording, D052#options
    term `production` also in 6: D006#what-the-agent-does, D011#model-key, D022#authenticate, D040#commands, D041#the-app-under-test, D059#let-the-runner-pick-the-port
    term `retain-on-failure` also in 9: D015#watch-it-happen, D033#browser-timeouts-and-artifacts, D033#defaults-that-differ, D040#commands, D041#artifacts, D041#e2econfig, D041#recording, D041#top-level, D052#options
    term `staging` also in 7: D005#write-a-provider, D024#setup, D041#the-app-under-test, D051#secrets-in-engine-options, D052#options, D053#options, D059#protected-previews
- **[ONLY HERE]** | Property | Value | | --- | --- | | `explore_ended` | Why it stopped:
- [ALSO: D040#commands] `finished`, `step-limit`, `time`, `stuck`, or `aborted` | | `explore_max_steps`, `explore_timeout_ms` | The budgets it ran with | | `explore_steps`, `explore_steps_passed`, `explore_steps_failed`, `explore_steps_blocked`, `explore_steps_exhausted` | Exploration steps, by how each ended | | `explore_
    term `aborted` also in 6: D040#commands, D042#lifecycle, D044#agenterror, D044#runner-codes, D049#host, D053#the-browser-fixture
    term `step-limit` also in 1: D040#commands
    term `stuck` also in 1: D040#commands
- **[ONLY HERE]** `{"1": 0, "2": 1, "3": 0, "4": 0, "5": 1}` | **e2e_mcp_session, once per MCP session** An `e2e mcp` server sends one for each `open_session` it receives, when the session closes or the open fails.
    term `open_session` also in 8: D040#commands, D044#agenterror, D044#runner-codes, D046#flags, D046#sessions, D046#setup, D046#several-sessions, D046#tools
- **[ONLY HERE]** A session that is still open when the client kills the server isn't sent.
- **[ONLY HERE]** | Property | Value | | --- | --- | | `client`, `client_version` | The name and version the MCP client gives itself (`claude-code`, `cursor-vscode`, ...).
    term `claude-code` also in 1: D043#telemetry
- **[ONLY HERE]** `null` before the client introduced itself | | `outcome`, `error_code` | `closed` for a session that opened, `open-failed` with the runner code of the failure (`APP_UNREACHABLE`, `ENGINE_FAILURE`, ...) | | `ended_by` | `agent` for `close_session`, `idle`, `step` for the session's time limit, `server
    term `APP_UNREACHABLE` also in 7: D008#upload-the-reports, D015#common-errors, D035#troubleshooting, D038#agent-act, D039#open, D041#the-app-under-test, D044#agenterror
    term `close_session` also in 5: D044#runner-codes, D046#sessions, D046#several-sessions, D046#the-catalog, D046#tools
    term `idle` also in 9: D022#sessions, D024#watch-and-clean-up-browsers, D026#choose-device-options, D028#limits, D046#sessions, D046#the-catalog, D051#mcp-and-explore, D053#browser-interface, D053#the-browser-fixture
- **[ONLY HERE]** `null` for a failed open | | `platform`, `engine`, `headed` | The target's platform and engine with its version, as for a run, and whether the UI was shown | | `duration_ms`, `sessions_open` | How long the session lived, and how many other sessions were open when it opened | | `calls_total`, `calls_
- **[ONLY HERE]** `{"observe": 4, "tap": 9, "locate": 2, "screenshot": 1}` | | `error_codes` | How often each runner code failed a call:
- **[ONLY HERE]** `{"LOCATOR_NOT_FOUND": 2}`, at most 20 codes |

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D040#commands: Both mention the e2e feedback command sending an event with anonymous machine facts, and the flag names recorded.
- D043#telemetry: Both describe E2E_TELEMETRY_FLEET, the preferences file, and package_manager and coding agent properties.
- D051#outbound-connections: Both state when telemetry requests are sent: per CLI invocation, per run() and per MCP session.
- D054#what-leaves-your-computer: Both say a run sends telemetry to eu.i.posthog.com unless you opt out.
- D056#in-ci: Both say CI runs count as the CI vendor (ci:<vendor>), with no preferences file.
- D056#in-a-fleet: Both say a fleet's events count as fleet:<name> via E2E_TELEMETRY_FLEET.
- D056#where-it-goes: Both say events go to PostHog which keeps no person profile and skips GeoIP.
- D056#feedback: Both describe the e2e_feedback event sent to the same PostHog project with the machine facts.
- D056#the-notice: Both say the first run() from e2e/runner prints the telemetry notice on stderr.

## S15 · single · D054#what-can-still-leak  (Security › What can still leak; page title: Security)

Regel: genau ein Abschnitt, dessen Hauptinhalt die Antwort ist; kein anderer Abschnitt enthält sie.

- **[ONLY HERE]** ## What can still leak Redaction matches strings, and only a secret fill turns screenshots off:
- **[ONLY HERE]** - **Video and other downloads.** Neither is masked.
- **[ONLY HERE]** If the test typed a password, check them before you share them.
- [ALSO: D051#artifacts, D059#let-the-runner-start-it] - **`command.log`.** It holds your app's stdout and stderr verbatim.
    term `command.log` also in 4: D015#common-errors, D051#artifacts, D051#reference, D051#where-redaction-stops
- **[ONLY HERE]** Keep secrets out of your app's output.
- [ALSO: D004#the-password-is-a-handle] - **Transformed values.** The last four characters of a key, or its base64, pass through.
- [ALSO: D051#policy-denials] Assert the outcome, not the secret.
- [ALSO: D051#redaction] - **Values not filled as a secret.** A secret passed as a plain string, or a sign-in that sets a cookie, leaves screenshots on.
- [ALSO: D018#what-the-context-holds] Only a configured secret's value is redacted.
- **[ONLY HERE]** - **Request credentials.** `basicAuth` answers a `401` from any origin.
    term `401` also in 4: D051#site-check, D053#options, D053#weboptions, D059#protected-previews
- [ALSO: D059#protected-previews] `headers` reach every host under a shared domain such as `vercel.app`.
    term `vercel.app` also in 2: D051#site-check, D059#protected-previews
- **[ONLY HERE]** - **Committed recordings.** Cache entries store typed values verbatim, except secret fills.
- [ALSO: D004#the-password-is-a-handle, D015#artifacts] They aren't signed and replay with your permissions, so review them as you would test code. [Where redaction stops](/reference/security#where-redaction-stops) lists every case.

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D004#the-password-is-a-handle: Both say redaction matches strings so a transformed value such as the last four characters passes through.
- D007#cache: Both say the replay cache stores typed values as typed except secret fills, so recordings should be reviewed before sharing.
- D015#artifacts: Both say videos mask nothing and point to where redaction stops.
- D051#site-check: Both mention a shared hosting domain such as vercel.app being treated as one site.
- D051#secrets-in-engine-options: Both say basicAuth secret protection is text only and withholds no pixels.
- D051#redaction: Both say a secret passed as a plain string is not a secret fill, so screenshots stay on.
- D051#where-redaction-stops: Both list what passes through redaction: transformed values, video that masks nothing, and command.log written verbatim.
- D051#artifacts: Both say video is not masked (incomplete) and command.log holds the app's stdout and stderr verbatim.
- D053#options: Both say basicAuth answers a 401 from any origin and its secret protection is text only.
- D059#protected-previews: Both say headers reach every host under a shared suffix such as vercel.app.

## S16 · paraphrase · D015#watch-it-happen  (Debugging a run › Watch it happen; page title: Debugging a run)

Regel: genau ein Abschnitt; die Frage teilt kein Inhaltswort mit der Abschnittsüberschrift oder dem Seitentitel (auch keine Wortformen).

- **[ONLY HERE]** ## Watch it happen **npm** **pnpm** **bun** `--video` takes an optional mode.
- **[ONLY HERE]** Put test files before it, or write `--video=<mode>`.
    term `--video=<mode>` also in 1: D040#commands
- **[ONLY HERE]** Each recording goes into its attempt's directory:
- **[ONLY HERE]** WebM per page on web, MP4 on a device.
- **[ONLY HERE]** The failure recap prints the path, or the URL when a hosted browser keeps the recording.
- **[ONLY HERE]** Subtract the recording's `startedAt` from a step's `startedAt` to find that step in the video.
    term `startedAt` also in 4: D005#recording-on-the-provider, D041#artifactsconfig, D041#recording, D042#artifacts
- **[ONLY HERE]** In CI, set `video: 'on-first-retry'` in the config.
    term `video: 'on-first-retry'` also in 1: D041#recording
- **[ONLY HERE]** A test that passes the first time records nothing, and a flaky test leaves a recording of its retry.
- [ALSO: D040#commands] A target's `video` wins over the config's, and `--video` wins over both.
- **[ONLY HERE]** A test's own option, such as `test('checkout', { video: 'on' }, ...)`, wins over all of them.
    term `test('checkout', { video: 'on' }, ...)` also in 1: D041#recording
- [ALSO: D040#commands, D041#recording] The config's `video` and `--video` apply only to targets whose engine can record, and one notice names the others.
- **[ONLY HERE]** When a target or a test asks for a recording its engine can't make, the run fails with `UNSUPPORTED_ARTIFACT` before any test starts. [Recording](/reference/config#recording) has every mode and file.
    term `UNSUPPORTED_ARTIFACT` also in 5: D040#commands, D041#output, D041#recording, D044#runner-codes, D052#options

Inhaltliche Überschneidungen (`catalogue_overlap.csv`):
- D008#upload-the-reports: Both say --video adds a video for each target whose engine can record to the .e2e output.
- D019#explore: Both mention --headed to watch the agent drive the app.
- D026#record-a-run: Both show npx e2e run --video recording every attempt on mobile.
- D030#map-each-command: Both say npx e2e run --headed shows the browser while the test runs.
- D032#port-the-config: Both say npx e2e run --video records one MP4 of the device per attempt.
- D033#browser-timeouts-and-artifacts: Both cover the video modes (--video [mode]) and --headed for watching a run.
- D033#map-each-api: Both say --headed shows a visible browser to watch the run.
- D035#what-differs-from-the-web: Both say --video writes WebM on web and an MP4 of the device screen on mobile.
- D037#add-an-agent-step: Both say --headed lets you watch a web test run.
- D040#commands: Both say --video [mode] chooses which attempts record a video, WebM on a browser engine and MP4 on a device engine.
- D041#recording: Both explain the video recording modes, their precedence (config, target, --video, test option), UNSUPPORTED_ARTIFACT, and using startedAt offsets.
- D044#runner-codes: Both say UNSUPPORTED_ARTIFACT fails the run when a video mode is set on a target whose engine cannot record.
- D051#artifacts: Both say video is opt-in through video or --video and stored as webm or mp4 under results.
- D052#options: Both say a test's own video option wins over --video, target and config, and UNSUPPORTED_ARTIFACT is raised before any test starts.
