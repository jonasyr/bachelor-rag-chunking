"""Shared look of the app's pages (spec 2026-10-14-catalogue-authoring, "Visual design"):
CSS classes and the light/dark palette as CSS variables."""

import streamlit as st

CSS = """
<style>
.source {font-family: "Source Serif", "Source Serif 4", Georgia, serif; font-size: 1.02rem;
  line-height: 1.7; max-width: 72ch; white-space: pre-wrap; overflow-wrap: anywhere;
  padding: 1.25rem 1.5rem; border: 1px solid var(--line); border-radius: 6px;
  background: var(--surface); color: var(--ink);}
.heading-path {color: var(--muted); font-size: 0.92rem; margin-bottom: 0.4rem;
  font-family: "Source Sans", "Source Sans 3", sans-serif;}
[data-testid="stMainBlockContainer"] {padding-top: 2rem; max-width: 1480px;}
[data-testid="stSidebar"] table {width: 100%;}
[data-testid="stSidebar"] td:last-child {font-variant-numeric: tabular-nums;}
.slot-title {font-family: "Source Sans", "Source Sans 3", sans-serif; font-size: 1.5rem;
  font-weight: 600; line-height: 1.25; margin: 0; color: var(--ink);}
.slot-title span {color: var(--muted); font-weight: 400;}
/* Two columns (640 px and up): every section view scrolls inside its own box; the starting
   section keeps most of the window so "Also covered elsewhere" starts right below it. */
@media (min-width: 640px) {
  .formatted, .source {max-height: 75vh; overflow-y: auto;
    scrollbar-width: thin; scrollbar-color: var(--line) transparent;}
  [data-testid="stMainBlockContainer"] {padding-left: 2.5rem; padding-right: 2.5rem;}
  .st-key-reader .formatted, .st-key-reader .source {max-height: 80vh; min-height: 24rem;}
  .st-key-also .formatted, .st-key-also .source {max-height: 50vh;}
}
.formatted {font-family: "Source Serif", "Source Serif 4", Georgia, serif;
  font-size: 1.02rem; line-height: 1.7; color: var(--ink); background: var(--surface);
  border: 1px solid var(--line); border-radius: 6px; padding: 0.5rem 1.5rem;
  overflow-wrap: anywhere;}
.formatted > * {max-width: min(72ch, 100%);}
.formatted h1, .formatted h2, .formatted h3, .formatted h4 {
  font-family: "Source Sans", "Source Sans 3", sans-serif; line-height: 1.3;
  margin: 1rem 0 0.5rem;}
.formatted h1, .formatted h2 {font-size: 1.35rem;}
.formatted h3, .formatted h4 {font-size: 1.15rem;}
.formatted p, .formatted ul, .formatted ol, .formatted pre, .formatted table {margin: 0 0 0.9rem;}
.formatted ul, .formatted ol {padding-left: 1.4rem;}
.formatted li > p {margin-bottom: 0.4rem;}
.formatted code {font-family: "Source Code Pro", ui-monospace, monospace; font-size: 0.86em;
  background: var(--code-bg); padding: 0.1em 0.3em; border-radius: 3px;}
.formatted pre {background: var(--code-bg); padding: 0.75rem 1rem;
  border-radius: 6px; overflow-x: auto; line-height: 1.5;}
.formatted pre code {background: none; padding: 0; font-size: 0.86rem; overflow-wrap: normal;}
.formatted table {border-collapse: collapse; display: block; overflow-x: auto;}
.formatted th, .formatted td {border: 1px solid var(--line); padding: 0.3rem 0.6rem;
  vertical-align: top; overflow-wrap: normal; word-break: normal; min-width: 6rem;
  max-width: 26rem;}
/* wide tables keep whole words and scroll sideways inside the section box */
.formatted > table, .formatted > pre, .formatted > *:has(table, pre) {max-width: 100%;}
.formatted td code, .formatted th code {white-space: normal; overflow-wrap: normal;}
.formatted a {color: var(--accent);}
.source .code {font-family: "Source Code Pro", ui-monospace, monospace; font-size: 0.88rem;
  line-height: 1.55;}
mark.hl {background: var(--marker); color: inherit; padding: 0 0.12em; border-radius: 2px;}
.checks {list-style: none; padding-left: 0; margin: 0.25rem 0 0.75rem;}
.checks li {margin: 0.15rem 0;}
.checks .ok {color: var(--ok);} .checks .problem {color: var(--problem);}
.cb-reference {color: var(--muted); border-left: 1px solid var(--line); padding-left: 0.85rem;
  white-space: pre-wrap; overflow-wrap: anywhere; margin-bottom: 0.5rem;}
.cb-answer {font-family: "Source Serif", "Source Serif 4", Georgia, serif; font-size: 1.02rem;
  line-height: 1.6; color: var(--ink); background: var(--surface); border: 1px solid var(--line);
  border-radius: 6px; padding: 0.75rem 1.25rem; white-space: pre-wrap; overflow-wrap: anywhere;}
::selection {background: var(--select);}
/* Writing aids (ADR 0049): class guide, "Also covered elsewhere" */
.guide-rule {margin: 0 0 0.35rem; color: var(--ink); font-weight: 600;}
.guide-prompts {margin: 0; padding-left: 1.2rem; color: var(--muted);}
.guide-prompts li {margin: 0.1rem 0;}
.dup-head {display: flex; gap: 0.6rem; align-items: baseline; justify-content: space-between;
  flex-wrap: wrap;}
.dup-path {font-weight: 600; color: var(--ink); overflow-wrap: anywhere;}
.dup-badge {font-size: 0.78rem; color: var(--muted); border: 1px solid var(--line);
  border-radius: 999px; padding: 0.05rem 0.55rem; white-space: nowrap;}
.dup-badge.is-added {color: var(--ok); border-color: var(--ok);}
.dup-id {font-family: "Source Code Pro", ui-monospace, monospace; font-size: 0.8rem;
  color: var(--muted);}
.dup-excerpt {color: var(--muted); font-size: 0.92rem; border-left: 1px solid var(--line);
  padding-left: 0.7rem; overflow-wrap: anywhere;}
.st-key-also {margin-top: 1rem;}
.rel-path {color: var(--ink); line-height: 1.35; overflow-wrap: anywhere;}
/* captions: the theme's own text colour, slightly lighter (Streamlit's grey fails 4.5:1) */
[data-testid="stCaptionContainer"] {color: color-mix(in srgb, currentColor 76%, transparent);}
[data-testid="stCaptionContainer"] p {color: inherit;}
[data-testid="stMainBlockContainer"] p, .guide-prompts li {text-wrap: pretty;}
.st-key-search {margin-top: 1.25rem;}
.st-key-use_type button, .st-key-use_type button p {color: var(--accent); font-weight: 600;}
/* "Read section" and "Add" stay side by side on a phone */
.st-key-also [data-testid="stHorizontalBlock"] {flex-wrap: nowrap;}
.st-key-also [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {min-width: 0;}
@media (max-width: 639px) {
  .slot-title span {display: block; font-size: 1rem; margin-top: 0.2rem;}
  .formatted, .source {max-height: 60vh; overflow-y: auto;}
  [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"] {
    min-height: 2.75rem;}
}
</style>
"""
# Scoring page only (injected by app/scoring_page.py): the page has no tabs above its first row,
# so it clears Streamlit's header itself; question and reference read as context, quieter than
# the answer under review; links in excerpts stay visible but inert (relative doc links would
# navigate away from the page and drop unsaved scores).
SCORING_CSS = """
<style>
[data-testid="stMainBlockContainer"] {padding-top: 4.5rem;}
.context {font-family: "Source Sans", "Source Sans 3", sans-serif; font-size: 0.98rem;
  line-height: 1.55; color: var(--ink); overflow-wrap: anywhere; margin-bottom: 0.25rem;}
.context.reference {color: var(--muted); border-left: 1px solid var(--line); padding-left: 0.85rem;}
.context p {margin: 0 0 0.5rem;}
.context code {font-family: "Source Code Pro", ui-monospace, monospace; font-size: 0.86em;
  background: var(--code-bg); padding: 0.1em 0.3em; border-radius: 3px;}
.inert a {pointer-events: none; color: inherit; text-decoration: underline dotted var(--muted);}
[data-testid="stButtonGroup"] button {min-width: 2.75rem; min-height: 2.75rem;}
@media (max-width: 639px) {
  [data-testid="stMainBlockContainer"] {padding-top: 3.75rem;}
  .slot-title span {display: block; font-size: 1rem; margin-top: 0.2rem;}
}
</style>
"""
LIGHT = {
    "line": "#D9DEE4",
    "surface": "#FFFFFF",
    "ink": "#1F2933",
    "muted": "#616E7C",
    "marker": "#FFE58A",
    "select": "rgba(36, 87, 166, 0.22)",
    "ok": "#2F7D4F",
    "problem": "#B3261E",
    "code-bg": "#F3F5F7",
    "accent": "#2457A6",
}
DARK = {
    "line": "#2E3640",
    "surface": "#1D232A",
    "ink": "#E4E8EC",
    "muted": "#9AA5B1",
    "marker": "rgba(255, 214, 90, 0.35)",
    "select": "rgba(122, 165, 232, 0.32)",
    "ok": "#6CC48F",
    "problem": "#F2877F",
    "code-bg": "#161B21",
    "accent": "#7AA5E8",
}


def palette_css() -> str:
    dark = getattr(getattr(st.context, "theme", None), "type", "light") == "dark"
    tokens = DARK if dark else LIGHT
    return "<style>:root {" + "".join(f"--{k}: {v};" for k, v in tokens.items()) + "}</style>"
