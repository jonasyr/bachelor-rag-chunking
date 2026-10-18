import pytest

from mdx import (
    parse_frontmatter,
    parse_js_literal,
    parse_provider_snippet,
    render_provider,
    slug,
    to_markdown,
)

SNIPPET = """export const ModelProvider = ({ show }) => {
  const providers = [
    {
      id: 'gateway',
      name: 'Vercel AI Gateway',
      group: 'AI SDK',
      packages: [],
      code: "import { gateway } from 'ai';",
      model: "gateway('openai/x')",
      env: ['AI_GATEWAY_API_KEY'],
      note: 'You can use a token instead.',
      docs: 'https://ai-sdk.dev/gateway',
    },
    {
      id: 'vertex',
      name: 'Google Vertex AI',
      group: 'AI SDK',
      packages: ['@ai-sdk/google-vertex'],
      code: `import { createVertex } from '@ai-sdk/google-vertex';

const vertex = createVertex({ project: 'p|q' });`,
      model: "vertex('gemini')",
      env: ['GOOGLE_VERTEX_PROJECT', 'GOOGLE_VERTEX_LOCATION'],
      docs: 'https://ai-sdk.dev/vertex',
      readsAtLoad: true,
    },
  ];
  const managers = [
    ['npm', 'npm install -D'],
    ['pnpm', 'pnpm add -D'],
  ];
  const config = `import type { E2EConfig } from 'e2e';
${provider.code}

export default { agents: { default: { model: ${provider.model} } } } satisfies E2EConfig;`;
  const model = `${provider.code}

const agent = { model: ${provider.model} };`;
  const note = provider.readsAtLoad
    ? 'This provider reads the variables when the config loads.'
    : null;
};
"""


def test_parse_frontmatter_reads_quoted_and_plain_values():
    meta, body = parse_frontmatter(
        '\ufeff---\ntitle: "e2e/runner"\ndescription: Run a suite.\n'
        '"og:image": "x.png"\n---\n\nBody\n'
    )
    assert meta == {"title": "e2e/runner", "description": "Run a suite.", "og:image": "x.png"}
    assert body == "\nBody\n"


@pytest.mark.parametrize(
    ("text", "message"),
    [("# No frontmatter\n", "no frontmatter"), ("---\ntitle: >\n  folded\n---\n", "unsupported")],
)
def test_parse_frontmatter_rejects(text, message):
    with pytest.raises(ValueError, match=message):
        parse_frontmatter(text)


@pytest.mark.parametrize(
    ("heading", "anchor"),
    [  # observed on the live site, 18.10.2026
        ("`.env` files", "env-files"),
        ("agent.act", "agent-act"),
        ("For scripts: report.json", "for-scripts-report-json"),
        ("What `--reporter` does to reporter objects", "what-reporter-does-to-reporter-objects"),
        ("`ExpectCall`, `SoftExpectCall`, and `Expect`", "expectcall-softexpectcall-and-expect"),
        ("One flow, several personas", "one-flow-several-personas"),
        ("See [the guide](/guide) first", "see-the-guide-first"),
    ],
)
def test_slug_matches_the_site(heading, anchor):
    assert slug(heading) == anchor


def test_parse_js_literal_reads_nested_values_and_escapes():
    src = "[{a: 'x\\'y', \"b\": [1, 2.5, true, null], c: `l1\nl2`,}, ] rest"
    value, end = parse_js_literal(src)
    assert value == [{"a": "x'y", "b": [1, 2.5, True, None], "c": "l1\nl2"}]
    assert src[end:] == " rest"


@pytest.mark.parametrize("src", ["[a]", "{a 1}", "`${x}`", "[1 2]"])
def test_parse_js_literal_rejects_non_literals(src):
    with pytest.raises(ValueError):
        parse_js_literal(src)


def test_parse_provider_snippet():
    snippet = parse_provider_snippet(SNIPPET)
    assert [p["id"] for p in snippet.providers] == ["gateway", "vertex"]
    assert snippet.install == "npm install -D"
    assert snippet.reads_at_load == "This provider reads the variables when the config loads."
    assert "${provider.code}" in snippet.config


def test_parse_provider_snippet_rejects_unknown_keys():
    with pytest.raises(ValueError, match="provider keys"):
        parse_provider_snippet(SNIPPET.replace("readsAtLoad: true", "extra: true"))


def test_render_provider_select_is_a_table_of_all_providers():
    rows = render_provider("select", parse_provider_snippet(SNIPPET))
    assert rows[0] == "| Provider | Group | Packages | Variables | Import | Model | Note |"
    assert rows[2] == (
        "| [Vercel AI Gateway](https://ai-sdk.dev/gateway) | AI SDK |  | `AI_GATEWAY_API_KEY` | "
        "`import { gateway } from 'ai';` | `gateway('openai/x')` | You can use a token instead. |"
    )
    assert "createVertex({ project: 'p\\|q' });`" in rows[3]
    assert rows[3].endswith("| This provider reads the variables when the config loads. |")
    assert len(rows) == 4


def test_render_provider_parts_show_the_default_selection():
    snippet = parse_provider_snippet(SNIPPET)
    assert render_provider("install", snippet) == [
        "**Install · Vercel AI Gateway**",
        "",
        "```bash",
        "npm install -D ai",
        "```",
    ]
    assert render_provider("env", snippet) == [
        "**Environment · Vercel AI Gateway**",
        "",
        "```bash",
        "export AI_GATEWAY_API_KEY=...",
        "```",
        "",
        "You can use a token instead.",
    ]
    config = render_provider("config", snippet)
    assert config[:3] == ["**e2e.config.ts · Vercel AI Gateway**", "", "```ts"]
    assert "import { gateway } from 'ai';" in config
    assert (
        "export default { agents: { default: { model: gateway('openai/x') } } } "
        "satisfies E2EConfig;" in config
    )
    assert render_provider("model", snippet)[0] == "**Model setup · Vercel AI Gateway**"


def test_render_provider_rejects_unknown_show():
    with pytest.raises(ValueError, match="show='other'"):
        render_provider("other", parse_provider_snippet(SNIPPET))


def page(body, title="Guide", description="About it."):
    return f'---\ntitle: {title}\ndescription: {description}\nicon: "x"\n---\n\n{body}'


def md(body, **kw):
    return to_markdown(page(body, **kw), "ci/guide")


def test_frontmatter_becomes_anchored_h1_and_first_paragraph():
    assert md("Text.\n") == "# Guide {#ci-guide}\n\nAbout it.\n\nText.\n"


def test_headings_get_the_site_slug_and_h4_stays_plain():
    out = md("## For scripts: report.json\n\n### `agent.act`\n\n#### Deep\n")
    assert "## For scripts: report.json {#for-scripts-report-json}" in out
    assert "### `agent.act` {#agent-act}" in out
    assert "#### Deep\n" in out


def test_body_h1_raises():
    with pytest.raises(ValueError, match="H1 in the page body"):
        md("# Second title\n")


def test_imports_dropped_and_prompt_export_rendered_in_setup_prompt():
    body = (
        "import { SetupPrompt } from '../snippets/setup-prompt-card.jsx';\n\n"
        "export const setupPrompt = `Read \\`ci.md\\`.\n\n1. Add the workflow.`;\n\n"
        "Intro.\n\n<SetupPrompt>\n\n"
        "<Prompt description={setupPrompt} children={setupPrompt} "
        '  actions={["copy", "cursor"]} />\n\n'
        "</SetupPrompt>\n"
    )
    out = md(body)
    assert "import" not in out and "export" not in out
    expected = "Intro.\n\n**Agent prompt**\n\n```text\nRead `ci.md`.\n\n1. Add the workflow.\n```\n"
    assert expected in out


def test_admonitions_accordions_tabs_become_labels():
    body = (
        "<Note>\nKeep it.\n</Note>\n\n<Warning>Inline warning.</Warning>\n\n"
        '<AccordionGroup>\n<Accordion title="Why">\nBecause.\n</Accordion>\n</AccordionGroup>\n\n'
        '<Tabs>\n<Tab title="tests/a.e2e.ts">\nTab text.\n</Tab>\n</Tabs>\n'
    )
    out = md(body)
    for expected in (
        "**Note**\nKeep it.",
        "**Warning**\nInline warning.",
        "**Why**\nBecause.",
        "**tests/a.e2e.ts**\nTab text.",
    ):
        assert expected in out


def test_steps_are_numbered():
    body = (
        '<Steps>\n  <Step title="Install">\n  Run it.\n  </Step>\n'
        '  <Step title="Configure">\n  Set it.\n  </Step>\n</Steps>\n'
    )
    out = md(body)
    assert "**1. Install**\n  Run it." in out and "**2. Configure**\n  Set it." in out


def test_cards_become_list_items():
    body = (
        "<CardGroup cols={2}>\n"
        '<Card title="Project tools" icon="wrench" href="/tools">\n'
        "  Add tools\n  per project.\n</Card>\n"
        '<Card title="Plain">\nNo link.\n</Card>\n'
        "</CardGroup>\n"
    )
    out = md(body)
    assert "- [Project tools](/tools): Add tools per project.\n- **Plain**: No link.\n" in out


def test_videos_keep_captions_and_video_cards_keep_title_and_subtitle():
    body = (
        "<Video>\n"
        '  <video src="/images/x.mp4" aria-label="Clip." muted loop playsInline controls />\n\n'
        "  Each browser is one session.\n</Video>\n\n"
        '<VideoCard\n  id="abc"\n  title="Watch it"\n  subtitle="In two minutes."\n/>\n'
    )
    out = md(body)
    assert "Each browser is one session." in out and "<video" not in out
    assert "- **Watch it**: In two minutes." in out


def test_legacy_anchors_and_show_more_dropped_and_blank_runs_collapse():
    out = md(
        '<a id="flags" />\n\n<ShowMore id="steps">\n\n1. One.\n\n</ShowMore>\n\n<span id="x" />\n'
    )
    assert out == "# Guide {#ci-guide}\n\nAbout it.\n\n1. One.\n"


def test_fence_titles_become_labels_and_code_stays_verbatim():
    body = (
        '```ts title="tests/a.e2e.ts" expandable\nconst a = 1;  \n```\n\n'
        "<CodeGroup>\n```bash npm\nnpm i e2e\n```\n```bash pnpm\npnpm add e2e\n```\n</CodeGroup>\n"
    )
    out = md(body)
    assert "**tests/a.e2e.ts**\n```ts\nconst a = 1;\n```" in out
    assert "**npm**\n```bash\nnpm i e2e\n```\n\n**pnpm**\n```bash\npnpm add e2e\n```" in out


def test_indented_fence_inside_a_component_is_dedented():
    body = (
        '<Steps>\n  <Step title="Run">\n'
        "    ```bash\n    # a comment\n    e2e run\n    ```\n  </Step>\n</Steps>\n"
    )
    out = md(body)
    assert "```bash\n# a comment\ne2e run\n```" in out
    assert "{#a-comment}" not in out


def test_model_provider_uses_the_snippet():
    snippet = parse_provider_snippet(SNIPPET)
    out = to_markdown(page('<ModelProvider show="install" />\n'), "models", snippet)
    assert "**Install · Vercel AI Gateway**\n\n```bash\nnpm install -D ai\n```" in out


def test_model_provider_without_snippet_raises():
    with pytest.raises(ValueError, match="provider snippet"):
        md('<ModelProvider show="select" />\n')


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("<Frame>\nx\n</Frame>\n", "unknown component <Frame>"),
        ("<Note>\nopen\n", "unclosed <Note>"),
        ("<Note>\nx\n</Warning>\n", "</Warning> closes <Note>"),
        ("Text with {expression}.\n", "unhandled markup"),
        ("Text with <b>bold</b>.\n", "unhandled markup"),
        (
            "<SetupPrompt>\n<Prompt children={missing} />\n</SetupPrompt>\n",
            "unknown export 'missing'",
        ),
        ("<Prompt children={x} />\n", "<Prompt> outside <SetupPrompt>"),
        ('<Step title="x">\ny\n</Step>\n', "<Step> outside <Steps>"),
        ("```ts\nopen\n", "unclosed code fence"),
        ("```ts lines={1}\nx\n```\n", "fence info"),
    ],
)
def test_unhandled_input_raises(body, message):
    with pytest.raises(ValueError, match=message):
        md(body)


def test_errors_name_the_line():
    with pytest.raises(ValueError, match="line 4"):
        md("Fine.\n\n<Frame>\n")
