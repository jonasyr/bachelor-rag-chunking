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

from scoring_store import app_pages, rater_mode  # noqa: E402

st.set_page_config(layout="wide")
st.markdown(CSS + palette_css(), unsafe_allow_html=True)
# second rater (ADR 0046): in R2 mode the scoring page only
st.navigation(
    [
        st.Page(file, title=title, default=n == 0)
        for n, (file, title) in enumerate(app_pages(rater_mode()))
    ]
).run()
