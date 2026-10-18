import pytest

from mdx import parse_frontmatter, parse_js_literal, parse_provider_snippet, render_provider, slug

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
