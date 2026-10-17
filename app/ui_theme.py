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
/* Two columns (640 px and up): the starting section fills the height of the form beside it
   and scrolls inside; a found section scrolls within most of the window. */
@media (min-width: 640px) {
  .formatted, .source {max-height: 75vh; overflow-y: auto;
    scrollbar-width: thin; scrollbar-color: var(--line) transparent;}
  [data-testid="stColumn"]:has(.st-key-reader) {display: flex; flex-direction: column;}
  [data-testid="stColumn"]:has(.st-key-reader) > [data-testid="stVerticalBlock"],
  [data-testid="stLayoutWrapper"]:has(> .st-key-reader),
  .st-key-reader, .st-key-reader [data-testid="stElementContainer"]:has(.formatted, .source),
  .st-key-reader .stHtml:has(.formatted, .source) {
    flex: 1 1 0; min-height: 0; display: flex; flex-direction: column;}
  .st-key-reader [data-testid="stElementContainer"]:has(.formatted, .source) {min-height: 20rem;}
  .st-key-reader .formatted, .st-key-reader .source {flex: 1 1 0; min-height: 0; max-height: none;}
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
.formatted th, .formatted td {border: 1px solid var(--line); padding: 0.3rem 0.6rem;}
.formatted a {color: var(--accent);}
.source .code {font-family: "Source Code Pro", ui-monospace, monospace; font-size: 0.88rem;
  line-height: 1.55;}
mark.hl {background: var(--marker); color: inherit; padding: 0 0.12em; border-radius: 2px;}
.checks {list-style: none; padding-left: 0; margin: 0.25rem 0 0.75rem;}
.checks li {margin: 0.15rem 0;}
.checks .ok {color: var(--ok);} .checks .problem {color: var(--problem);}
::selection {background: var(--select);}
.formatted.reference {background: transparent; color: var(--muted); max-height: none;}
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
