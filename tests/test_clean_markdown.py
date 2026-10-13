import pytest

from preprocess import clean_markdown, fence_marker

DOC = "# Title {#title}\n\n"


def clean(body: str) -> str:
    return clean_markdown(DOC + body).text


def test_bom_and_frontmatter_removed():
    result = clean_markdown("\ufeff---\noutline: deep\n---\n\n# T {#t}\n\nBody\n")
    assert result.text == "# T\n\nBody\n"


def test_options_block_with_nested_div_dropped():
    body = '<div class="options-api">\n\nOpt\n<div>\ninner\n</div>\n</div>\n\nAfter\n'
    assert clean(body) == "# Title\n\nAfter\n"


def test_composition_block_unwrapped():
    assert clean('<div class="composition-api">\n\nComp\n\n</div>\n') == "# Title\n\nComp\n"


def test_options_and_composition_paragraphs():
    body = (
        '<p class="options-api">\nOpt para\n</p>\n\n<p class="composition-api">\nComp para\n</p>\n'
    )
    assert clean(body) == "# Title\n\nComp para\n"


def test_options_markup_inside_code_fence_survives():
    body = '```vue-html\n<div class="options-api">x</div>\n```\n'
    assert clean(body) == '# Title\n\n```vue-html\n<div class="options-api">x</div>\n```\n'


def test_inline_code_divs_do_not_change_depth():
    body = 'Use `<div>` here.\n\n<div class="composition-api">\n\nSee `</div>` too\n\n</div>\n'
    assert clean(body) == "# Title\n\nUse `<div>` here.\n\nSee `</div>` too\n"


def test_inline_api_spans():
    body = (
        'Pick <span class="options-api">Options</span>'
        '<span class="composition-api">Composition</span> API.\n'
    )
    assert clean(body) == "# Title\n\nPick Composition API.\n"


def test_page_script_comments_components_demo_and_containers():
    body = (
        '<script setup>\nimport X from "./X.vue"\n</script>\n\n'
        "<!-- hidden\nmulti -->\nText <!-- inline --> kept\n\n"
        '<VueSchoolLink href="u" title="t"/>\n\n'
        '<div class="demo">\n<button>x</button>\n</div>\n\n'
        "::: tip Note\nBe careful.\n:::\n"
    )
    assert clean(body) == "# Title\n\nText kept\n\nNote\nBe careful.\n"


def test_promo_blocks_details_and_images():
    body = (
        '<ScrimbaLink href="u" title="t">\nWatch\n</ScrimbaLink>\n\n'
        "<details>\n<summary>Usage before 3.5</summary>\n\nOld way\n\n</details>\n\n"
        '<img alt="diagram" src="./x.png">\n\n'
        'See docs <sup class="vt-badge ts" />\n'
    )
    assert clean(body) == "# Title\n\nUsage before 3.5\n\nOld way\n\nSee docs\n"


def test_encoded_playground_state_dropped_from_links():
    body = (
        "[Try it in the Playground](https://play.vuejs.org/#eNp9kE1Lw0AQhv) and "
        "[explorer](https://template-explorer.vuejs.org/#eyJzcmMi) but `https://play.vuejs.org/#keep`.\n"
    )
    expected = (
        "# Title\n\n[Try it in the Playground](https://play.vuejs.org/) and "
        "[explorer](https://template-explorer.vuejs.org/) but `https://play.vuejs.org/#keep`.\n"
    )
    assert clean(body) == expected


def test_inline_code_is_never_cleaned():
    body = '2. `<PascalCase />` is clearer; write `<!-- c -->` or `<span class="options-api">`.\n'
    assert clean(body) == "# Title\n\n" + body


def test_highlighted_shell_block_becomes_fenced_code():
    body = (
        '<div class="language-sh"><pre><code><span style="color:green;">✔</span> '
        "<span>Project name: … &lt;your-project-name&gt;</span>\n"
        "<span>Add TypeScript? … No / Yes</span>\n"
        "<span></span>\n"
        "<span>Done.</span></code></pre></div>\n\nAfter\n"
    )
    expected = (
        "# Title\n\n```sh\n✔ Project name: … <your-project-name>\nAdd TypeScript? … No / Yes\n\n"
        "Done.\n```\n\nAfter\n"
    )
    assert clean(body) == expected


def test_inline_html_in_prose_becomes_markdown():
    body = (
        "3. <code>process.env<wbr>.NODE_ENV</code> is replaced.\n"
        "A <code v-pre>{{ }}</code> tag.\n"
        "Here both <span v-pre>`{{ message }}`</span> render.\n"
    )
    expected = (
        "# Title\n\n3. `process.env.NODE_ENV` is replaced.\nA `{{ }}` tag.\n"
        "Here both `{{ message }}` render.\n"
    )
    assert clean(body) == expected


def test_unknown_inline_html_in_prose_raises():
    with pytest.raises(ValueError, match="unhandled inline HTML"):
        clean_markdown(DOC + "Text with <kbd>Ctrl</kbd> keys.\n")


def test_version_badge_kept_as_text_and_typescript_badge_dropped():
    body = 'Since <sup class="vt-badge" data-text="3.5+" /> only. See <sup class="vt-badge ts" />\n'
    assert clean(body) == "# Title\n\nSince (3.5+) only. See\n"


def test_api_style_markers_stripped_from_headings():
    result = clean_markdown(
        DOC + "## `ref()` \\*\\* {#ref}\n\n### Stateful Methods \\* {#stateful}\n"
    )
    assert [h.title for h in result.headings] == ["Title", "`ref()`", "Stateful Methods"]
    assert "\\*" not in result.text


def test_fence_info_strings_reduced_and_indented_fences_tracked():
    listed = "- item\n\n   ```vue-html\n   <div>\n   ```\n"
    body = "```js{2-6}\ncode\n```\n\n```sh [npm]\nnpm i\n```\n\n" + listed
    expected = "# Title\n\n```js\ncode\n```\n\n```sh\nnpm i\n```\n\n" + listed
    assert clean(body) == expected


def test_headings_recorded_with_offsets_and_anchors_removed():
    result = clean_markdown(DOC + "## A {#a}\n\ntext\n\n### B {#b}\n\n#### Deep\n\n## C {#c}\n")
    assert [(h.level, h.anchor, h.title) for h in result.headings] == [
        (1, "title", "Title"),
        (2, "a", "A"),
        (3, "b", "B"),
        (2, "c", "C"),
    ]
    for h in result.headings:
        assert result.text[h.offset :].startswith("#" * h.level + " " + h.title + "\n")
    assert "{#" not in result.text
    assert "#### Deep" in result.text


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("```js\nx\n", "unclosed code fence"),
        ('<div class="options-api">\nx\n', "unclosed HTML block"),
        ('<div class="composition-api">\nx\n', "unclosed composition-api wrapper"),
        ("<!-- open\n", "unclosed HTML comment"),
        ("## Sub\n", "heading without anchor"),
        ("## A {#a}\n\n## B {#a}\n", "duplicate anchor"),
        ("# Second {#second}\n", "exactly one H1"),
        ("<table>\n", "unhandled HTML"),
        ('x <b class="options-api">y</b>\n', "options-api markup"),
    ],
)
def test_anomalies_raise(body, message):
    with pytest.raises(ValueError, match=message):
        clean_markdown(DOC + body)


def test_missing_h1_raises():
    with pytest.raises(ValueError, match="exactly one H1"):
        clean_markdown("## A {#a}\n")


def test_drop_block_inside_composition_wrapper():
    body = (
        '<div class="composition-api">\n\nKeep.\n\n'
        '<div class="demo">\n<button>x</button>\n</div>\n\n'
        "Also keep.\n\n</div>\n"
    )
    assert clean(body) == "# Title\n\nKeep.\n\nAlso keep.\n"


def test_line_leading_autolink_is_prose():
    assert (
        clean("<https://vuejs.org> is the site.\n")
        == "# Title\n\n<https://vuejs.org> is the site.\n"
    )


def test_encoded_url_in_autolink_keeps_closing_bracket():
    body = "See <https://play.vuejs.org/#eNp9abc> now.\n"
    assert clean(body) == "# Title\n\nSee <https://play.vuejs.org/> now.\n"


def test_fence_closes_only_with_same_marker():
    body = "~~~\n```\n\n## Not a heading\n~~~\n\nAfter\n"
    assert clean(body) == "# Title\n\n~~~\n```\n\n## Not a heading\n~~~\n\nAfter\n"


def test_fence_needs_at_most_three_spaces_of_indentation():
    assert fence_marker("   ```js") == "```"
    assert fence_marker("    ```js") is None
    assert fence_marker("```js `x`") is None
