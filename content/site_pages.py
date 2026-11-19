import streamlit as st
from components.site import intro, section, card, process
from components.demo_library import demo_library
from components.agent_ui import agent_ui

PRODUCTS = [
    ("01", "Structural Bracket", "구조용 브래킷", "항공우주 구조물의 연결 및 하중 전달을 위한 형상 예시", "절단 → CNC 밀링 → 표면 처리 → 치수 검사", "주요 치수, 표면 상태, 소재 이력"),
    ("02", "Precision Mount", "정밀 마운트", "장비 및 구조물의 고정에 활용되는 부품 예시", "소재 준비 → CNC 가공 → 홀 가공 → 최종 검사", "홀 위치, 공차, 외관 및 추적성"),
    ("03", "Machined Structure", "정밀 가공 구조 부품", "복잡한 형상의 경량 구조 부품 예시", "소재 절단 → 황삭·정삭 → 후처리 → 검사", "형상 및 치수, 표면 상태, 검사 기록"),
]

def home():
    st.markdown('''<div class="hero"><div class="hero-art"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><div class="hero-word">Ti<span>64</span></div></div><div class="hero-copy"><span class="eyebrow light">AEROSPACE · MATERIALS · PRECISION</span><h1>Precision in Titanium.<br><em>Confidence in Aerospace.</em></h1><p>항공우주 산업을 위한 정밀 티타늄 제조 솔루션</p><div class="hero-actions"><a href="?page=PRODUCTS" target="_self">제품 살펴보기 <b>↗</b></a><a class="outline" href="?page=TECHNOLOGY" target="_self">제조 기술 <b>↗</b></a></div></div><div class="hero-bottom"><span>ENGINEERED FOR WHAT'S NEXT</span><span>Ti-6Al-4V / PRECISION MANUFACTURING</span></div></div>''', unsafe_allow_html=True)
    st.markdown('<div class="intro-line"><span>01 / ABOUT AEROTITAN</span><h2>소재의 가능성을<br>정밀한 결과로.</h2><p>AeroTitan Technologies는 Ti-6Al-4V 티타늄 합금을 중심으로 항공우주용 정밀 부품을 제조하는 가상 B2B 기업입니다. 소재 조달부터 가공, 검사와 납품까지 연결되는 제조 체계를 설계합니다.</p></div>', unsafe_allow_html=True)
    section("02 / CORE BUSINESS", "Precision at every stage.", "소재와 공정, 품질을 하나의 흐름으로 연결합니다.")
    cols=st.columns(3)
    for col, item in zip(cols, [("01 / COMPONENTS","Titanium Precision Components","항공우주 구조 부품을 위한 티타늄 정밀 가공 제품을 소개합니다."),("02 / MANUFACTURING","Advanced Manufacturing","CNC 가공과 후처리를 연결하는 제조 공정을 설계합니다."),("03 / QUALITY","Quality Assurance","입고 검사부터 최종 검증까지 소재와 공정의 이력을 관리합니다.")]):
        with col: card(*item)
    section("03 / PRODUCT PORTFOLIO", "Designed around precision.", "항공우주 산업의 요구를 고려한 가상 제품 포트폴리오입니다.")
    cols=st.columns(3)
    for col, item in zip(cols, PRODUCTS):
        with col:
            st.markdown(f'<div class="product-card"><div class="product-art"><span>Ti</span><i></i></div><small>{item[0]} / CONCEPT PRODUCT</small><h3>{item[1]}</h3><p>{item[2]}</p></div>', unsafe_allow_html=True)
    st.markdown('<a class="text-link" href="?page=PRODUCTS" target="_self">전체 제품 보기 ↗</a>', unsafe_allow_html=True)
    section("04 / MANUFACTURING", "From material to delivery.", "소재의 입고부터 완제품 납품까지 이어지는 제조 흐름")
    process()
    st.markdown('<div class="quality-band"><span class="eyebrow light">05 / QUALITY ASSURANCE</span><h2>신뢰는 소재의<br>첫 검사에서 시작됩니다.</h2><p>시험성적서와 구매 요구조건을 비교하고 판정 이력을 관리하는 품질 프로세스를 구상합니다.</p><a href="?page=QUALITY" target="_self">품질 관리 살펴보기 ↗</a></div>', unsafe_allow_html=True)

def company():
    intro("01 / COMPANY", "Built for precision.", "정밀 제조와 데이터 기반 품질관리를 지향하는 항공우주 소재 기업")
    section("WHO WE ARE", "티타늄 소재에서 시작하는 신뢰", "AeroTitan Technologies는 대학 프로젝트를 위해 설립한 가상 기업입니다. 항공우주 산업의 소재 요구와 제조 현장의 품질 과제를 현실적으로 탐구하기 위해 기획했습니다.")
    cols=st.columns(3)
    for c, x in zip(cols, [("VISION","비전","티타늄 정밀 부품의 신뢰성과 생산 효율을 높이고 데이터 기반 품질관리 체계를 갖춘 제조기업을 지향합니다."),("VALUES","핵심 가치","정밀성, 추적성, 책임 있는 판단과 지속적인 개선을 중시합니다."),("CUSTOMERS","주요 고객군","항공우주 구조 부품 제조업체, 항공기 부품 공급업체 및 정밀기계 제조기업을 대상으로 합니다.")]):
        with c: card(*x)
    section("BUSINESS MODEL", "소재 조달부터 납품까지", "티타늄 소재 구매, 입고 검사, 정밀 가공, 후처리 관리, 품질 검증과 납품으로 이어지는 B2B 제조 구조입니다.")
    process()
    section("OPERATING MODEL", "의뢰부터 납품까지", "다음은 가상 기업의 운영 시나리오입니다. 어닐링 상태의 Ti-6Al-4V 원형 봉재를 조달하여 CNC 가공으로 브래킷과 마운팅 부품을 제작합니다.")
    operations = ["고객 의뢰", "도면·요구사항 검토", "구매 요청", "발주서 발행", "공급업체 공급", "소재·MTR 입고", "품질 적합성 검토", "승인 또는 보류", "생산 투입", "CNC 가공", "필요 시 후처리", "제품 검사", "출하 검토·납품"]
    st.markdown('<div class="process operation-flow">' + ''.join(f'<div><small>{i:02}</small><strong>{step}</strong></div>' for i, step in enumerate(operations, 1)) + '</div>', unsafe_allow_html=True)
    st.caption("각 단계의 담당 부서, 문서, 진행 조건은 docs/company_operations.md에 정리되어 있습니다.")
    section("OUR ORGANIZATION", "협업으로 이어지는 제조", "가상 기업의 부서 구성과 역할")
    roles=[("경영관리","사업 운영 및 자원 관리"),("기술영업","고객 요구사항 검토 및 기술 협의"),("구매·자재관리","소재 조달과 입출고 이력 관리"),("생산기술","가공 방법 및 공정 계획 수립"),("제조","정밀 가공과 생산 수행"),("품질보증","입고·공정·최종 검사 및 기록 관리"),("연구개발","소재·공정 개선과 기술 검토")]
    for name, desc in roles: st.markdown(f'<div class="role"><strong>{name}</strong><span>{desc}</span></div>', unsafe_allow_html=True)

def products():
    intro("02 / PRODUCTS", "Made to perform.", "티타늄의 가능성을 정밀한 부품 형상으로")
    st.info("아래 제품은 실제 생산 제품이 아닌 가상 기업의 교육용 포트폴리오 예시입니다. 이미지는 개념도입니다.")
    for n, en, ko, use, manufacturing, quality in PRODUCTS:
        col1,col2=st.columns([1,1.25], gap="large")
        with col1: st.markdown(f'<div class="product-art large"><span>Ti</span><i></i><small>CONCEPT / {n}</small></div>',unsafe_allow_html=True)
        with col2:
            st.markdown(f'<span class="eyebrow">PRODUCT / {n}</span><h2>{en}</h2><h3>{ko}</h3><p>{use}</p>', unsafe_allow_html=True)
            st.markdown(f'**사용 소재**　Ti-6Al-4V 티타늄 합금  \n**적용 분야**　항공우주 구조 및 정밀 기계  \n**주요 공정**　{manufacturing}  \n**품질 관리**　{quality}')
        st.markdown('<hr>',unsafe_allow_html=True)

def technology():
    intro("03 / TECHNOLOGY", "Material. Process. Precision.", "소재의 특성을 이해하고 각 공정의 조건을 관리합니다.")
    section("MATERIAL", "Ti-6Al-4V", "티타늄에 알루미늄 6%, 바나듐 4%를 nominal 조성으로 함유하는 대표적인 α+β 티타늄 합금입니다. 높은 비강도와 내식성으로 항공우주 분야에 활용되며, 낮은 열전도율 등의 특성을 고려한 가공 조건 관리가 필요합니다.")
    for n,title,desc in [("01","원자재 조달","구매 요구조건에 맞는 소재와 시험성적서를 확인하고 소재 식별 정보를 기록합니다."),("02","CNC 정밀 가공","도면과 공정 계획에 따라 절삭 조건과 형상을 관리합니다."),("03","열처리 및 표면 처리","요구사항에 따라 적절한 후처리를 계획하고 수행 이력을 관리합니다."),("04","치수 검사","도면의 치수와 허용오차를 기준으로 적절한 측정 방법을 적용합니다."),("05","품질 및 이력 관리","소재 식별, 공정, 검사 결과를 연결하여 추적 가능한 기록을 유지합니다.")]:
        st.markdown(f'<div class="role"><strong>{n} &nbsp; {title}</strong><span>{desc}</span></div>',unsafe_allow_html=True)
    st.caption("공정 및 소재 설명은 교육용 개요이며, 실제 적용 시 도면·규격·고객 요구조건의 검토가 필요합니다.")

def quality():
    intro("04 / QUALITY", "Confidence is built in.", "소재의 입고부터 납품까지 이어지는 품질보증")
    section("QUALITY ASSURANCE", "생산 투입 전, 소재를 확인합니다.", "가상 시나리오에서 품질보증팀은 어닐링 Ti-6Al-4V 원형 봉재와 관련 문서를 검토하고, 추적성과 요구조건 충족 여부를 확인합니다. 최종 입고 승인 전 소재는 보류합니다.")
    section("INCOMING INSPECTION", "원자재 입고검사 흐름", "발주 요구조건과 공급업체가 제공한 증빙을 대조합니다.")
    steps = ["발주·요구조건 확인", "소재·MTR 입고", "식별·규격 확인", "조성·물성 대조", "검토 기록", "책임자 승인·보류"]
    st.markdown('<div class="process">' + ''.join(f'<div><small>{i:02}</small><strong>{v}</strong></div>' for i,v in enumerate(steps,1)) + '</div>', unsafe_allow_html=True)
    st.caption("승인된 소재만 생산에 투입합니다. 누락·불일치가 있으면 격리 또는 보류 후 확인합니다.")
    section("DOCUMENTS", "두 문서를 연결하는 검토")
    cols=st.columns(2)
    for c,x in zip(cols, [("PURCHASE ORDER", "구매발주서 (PO)", "구매할 소재의 형상·상태, 적용 규격과 개정번호, 치수 및 해당 발주의 시험·추적성 요구조건을 지정합니다."), ("MATERIAL TEST REPORT", "소재 시험성적서 (MTR)", "공급업체가 소재 식별 정보, 시험 결과 및 단위 등 해당 소재의 증빙을 제공합니다. 실제 포함 항목은 문서마다 다릅니다.")]):
        with c: card(*x)
    section("REVIEW POINTS", "무엇을 확인하나요?")
    for name,desc in [("소재 및 규격", "재질·원형 봉재·어닐링 상태, 발주에서 지정한 규격과 개정번호를 확인합니다."), ("화학 조성 및 물성", "발주에서 요구한 항목의 측정값과 단위를 원본 요구조건에 비교합니다."), ("식별과 추적성", "실물 표시, PO, MTR의 Heat/Lot 등 요구된 식별정보를 연결하고 검토 근거를 기록합니다."), ("수작업의 한계", "서로 다른 문서 형식, 반복 대조, 누락·단위 확인과 기록 작성은 시간과 주의가 필요하며 실수 가능성이 있습니다.")]:
        st.markdown(f'<div class="role"><strong>{name}</strong><span>{desc}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="notice"><strong>EDUCATIONAL AI REVIEW</strong><p>교육용 AI와 Python 규칙 기반 도구로 발주서와 시험성적서의 사전 검토를 지원합니다. 최종 입고 승인과 생산 투입 결정은 권한 있는 담당자가 수행합니다.</p><a href="?page=AI%20SOLUTION" target="_self">AI 품질검토 보기 ↗</a></div>',unsafe_allow_html=True)


def ai_solution():
    intro("05 / AI SOLUTION", "A better way to review.", "품질보증 업무를 지원하는 교육용 AI 사전 검토")
    st.markdown('<div class="status"><span>●</span> EDUCATIONAL MVP &nbsp; / &nbsp; 교육용 시범 기능</div>',unsafe_allow_html=True)
    section("THE CHALLENGE", "입고 적합성 검토의 빈틈을 줄이기 위해", "가상 기업의 품질보증팀은 공급업체마다 다른 시험성적서와 구매발주서를 수작업으로 대조합니다. 누락·단위 차이·Heat 번호 불일치를 놓치면 부적합 소재가 생산에 투입되거나 추적성이 약해질 위험이 있습니다.")
    section("AS-IS / TO-BE", "기존 검토와 AI 보조 검토", "아래는 기존 수작업 시나리오와 교육용 보조 검토 흐름입니다.")
    cols=st.columns(2)
    with cols[0]: card("AS-IS / 수작업", "담당자가 직접 대조", "PO 확인 → MTR 열기 → 식별·규격 확인 → 조성·물성 비교 → 누락 확인 → 기록·보고 → 책임자 판단")
    with cols[1]: card("TO-BE / 교육용 MVP", "AI와 규칙 기반 검증이 보조", "PO·MTR 입력 → AI 정보 추출과 원문 대조 → 프로그램의 필수값·단위·조건 비교 → 결과·보고서 → 담당자 원본 검토 및 최종 판단")
    section("REVIEW ARCHITECTURE", "역할을 나누고 근거를 남깁니다.", "문서 기반 사전 검토 결과는 최종 입고 승인이 아닙니다. AI 모드는 API 설정이 필요합니다.")
    for name,desc in [("01 / AI · API 필요", "선택한 PO와 MTR에서 정보와 원문 근거를 추출하고 검증 도구 호출을 조정합니다."), ("02 / PYTHON · 교육용", "모의 규격의 필수 항목, 단위와 요구조건을 규칙 기반 도구로 검증하고 사전 검토 결과와 HTML 보고서를 생성합니다."), ("03 / 사람 · 최종 책임", "원본과 검토 근거, 예외를 확인하고 최종 입고 승인 또는 보류를 결정합니다. 승인 전 생산에 투입하지 않습니다.")]:
        st.markdown(f'<div class="role"><strong>{name}</strong><span>{desc}</span></div>', unsafe_allow_html=True)
    section("SUPPORTED CAPABILITIES", "현재 지원 기능", "교육용 텍스트 PDF 업로드, 근거와 교차 확인, 규칙 기반 비교 및 HTML 보고서를 제공합니다. 임의 공급업체 양식, 스캔·OCR 및 복잡한 추가 규격은 지원하지 않습니다.")
    st.caption("교육용 MVP: 규칙 기반 검토를 지원하며 AI 모드는 API 설정 후 이용할 수 있습니다. 최종 입고 승인은 담당자가 결정합니다.")
    agent_ui()
    demo_library()
