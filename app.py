import streamlit as st
from pathlib import Path
from components.site import header, footer
from content import site_pages

st.set_page_config(page_title="AeroTitan Technologies", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")
css = Path(__file__).parent / "assets" / "styles" / "main.css"
st.markdown(f"<style>{css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
header()
pages = {
    "HOME": site_pages.home,
    "COMPANY": site_pages.company,
    "PRODUCTS": site_pages.products,
    "TECHNOLOGY": site_pages.technology,
    "QUALITY": site_pages.quality,
    "AI SOLUTION": site_pages.ai_solution,
}
selected = st.query_params.get("page", "HOME").upper()
if selected not in pages:
    selected = "HOME"
pages[selected]()
footer()
