import streamlit as st

NAV = [("HOME", "HOME"), ("COMPANY", "COMPANY"), ("PRODUCTS", "PRODUCTS"), ("TECHNOLOGY", "TECHNOLOGY"), ("QUALITY", "QUALITY"), ("AI SOLUTION", "AI%20SOLUTION")]

def header():
    links = "".join(f'<a href="?page={url}" target="_self">{label}</a>' for label, url in NAV)
    st.markdown(f'<header class="nav"><a class="brand" href="?page=HOME" target="_self"><span class="brand-mark">A</span><span>AEROTITAN<small>TECHNOLOGIES</small></span></a><nav aria-label="주 메뉴">{links}</nav></header>', unsafe_allow_html=True)

def footer():
    links = "".join(f'<a href="?page={url}" target="_self">{label}</a>' for label, url in NAV)
    st.markdown(f'<footer class="footer"><div><strong>AEROTITAN <span>TECHNOLOGIES</span></strong><p>Precision in Titanium.<br>Confidence in Aerospace.</p></div><div><small>EXPLORE</small><div class="footer-links">{links}</div></div><div class="footer-note">본 웹사이트는 대학 프로젝트를 위한 가상 기업 소개입니다.<br>표시된 제품과 공정은 교육용 예시입니다.</div></footer>', unsafe_allow_html=True)

def intro(kicker, title, description):
    st.markdown(f'<section class="page-intro"><span class="eyebrow">{kicker}</span><h1>{title}</h1><p>{description}</p></section>', unsafe_allow_html=True)

def section(kicker, title, description=""):
    st.markdown(f'<div class="section-heading"><span class="eyebrow">{kicker}</span><h2>{title}</h2><p>{description}</p></div>', unsafe_allow_html=True)

def card(number, title, text):
    st.markdown(f'<div class="info-card"><span>{number}</span><h3>{title}</h3><p>{text}</p></div>', unsafe_allow_html=True)

def process():
    steps = [("01", "소재 조달"), ("02", "입고 검사"), ("03", "CNC 가공"), ("04", "열·표면 처리"), ("05", "최종 검사"), ("06", "출하·납품")]
    st.markdown('<div class="process">' + ''.join(f'<div><small>{n}</small><strong>{name}</strong></div>' for n,name in steps) + '</div>', unsafe_allow_html=True)
