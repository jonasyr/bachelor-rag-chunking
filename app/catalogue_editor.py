"""The app (ADR 0031, 0034): the question catalogue and the blind scoring as two pages.

Run: uv run streamlit run app/catalogue_editor.py --server.address localhost
"""

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR.parent / "src"))
sys.path.insert(0, str(APP_DIR))

import streamlit as st  # noqa: E402
from ui_theme import CSS, palette_css  # noqa: E402

st.set_page_config(layout="wide")
st.markdown(CSS + palette_css(), unsafe_allow_html=True)
st.navigation(
    [
        st.Page("catalogue_page.py", title="Catalogue", default=True),
        st.Page("scoring_page.py", title="Scoring"),
    ]
).run()
