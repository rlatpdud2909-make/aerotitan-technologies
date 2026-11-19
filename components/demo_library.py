from pathlib import Path
import csv
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

def demo_library():
    st.markdown('### 입고검사 문서 자료실')
    st.info('아래 문서는 교육용 모의 문서이며 실제 소재 승인에 사용할 수 없습니다.')
    path = ROOT / 'data/metadata/cases.csv'
    if not path.exists():
        st.warning('표시할 예시 문서가 없습니다.')
        return
    with path.open(encoding='utf-8', newline='') as f:
        cases = [r for r in csv.DictReader(f) if r['split'] == 'development']
    if not cases:
        st.warning('표시할 예시 문서가 없습니다.')
        return
    chosen = st.selectbox('문서 선택', cases, format_func=lambda r: f"{r['case_id']} · {r['supplier'].replace(' (Fictional)', '')}")
    st.write(f"소재: {chosen['material']} | 발주번호: {chosen['purchase_order_id']} | 성적서 번호: {chosen['certificate_id']}")
    kind = st.radio('문서 유형', ['구매발주서', '소재 시험성적서'], horizontal=True)
    field = 'purchase_order' if kind == '구매발주서' else 'material_test_report'
    for label, key in [('구매발주서 PDF 다운로드', 'purchase_order'), ('시험성적서 PDF 다운로드', 'material_test_report')]:
        document = ROOT / chosen[key]
        if document.is_file():
            st.download_button(label, document.read_bytes(), file_name=f"{chosen['case_id']}_{key}.pdf", mime='application/pdf', key=f'download_{key}')
    selected = ROOT / chosen[field]
    if selected.is_file():
        st.pdf(selected.read_bytes(), height=650, alt=f'{kind} 미리보기')
    else:
        st.warning('선택한 문서를 찾을 수 없습니다.')
