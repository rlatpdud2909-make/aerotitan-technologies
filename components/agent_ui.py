import csv, os, hashlib
from pathlib import Path
import streamlit as st
from src.agent.orchestrator import review
from src.reporting.quality_report import render_report

ROOT=Path(__file__).resolve().parents[1]
def setting(name):
    try: return st.secrets.get(name) or os.getenv(name)
    except Exception: return os.getenv(name)

def agent_ui():
    st.markdown('### AeroTitan Quality Agent')
    st.warning('교육용 모의 데이터 전용입니다. 실제 기업 기밀자료를 업로드하지 마세요. 검토 결과는 최종 입고 승인이 아닙니다.')
    mode=st.radio('분석 모드',['Rule-Based Mode','AI Agent Mode'],horizontal=True,key='agent_mode')
    st.caption('규칙 기반 모드는 정해진 교육용 PDF 형식만 지원합니다. AI 모드는 선택한 API 설정이 필요합니다.')
    provider=st.radio('AI 서비스',['기본 AI','OpenAI'],horizontal=True,key='agent_provider') if mode=='AI Agent Mode' else 'OpenAI'
    source=st.radio('문서 선택',['Demo 문서','직접 업로드'],horizontal=True,key='agent_source')
    po=mtr=None
    if source=='Demo 문서':
        with (ROOT/'data/metadata/cases.csv').open(encoding='utf-8',newline='') as f: cases=[r for r in csv.DictReader(f) if r['split']=='development']
        item=st.selectbox('분석할 개발용 사례',cases,format_func=lambda r:f"{r['case_id']} · {r['supplier']}",key='agent_case')
        po=(ROOT/item['purchase_order']).read_bytes();mtr=(ROOT/item['material_test_report']).read_bytes()
    else:
        p=st.file_uploader('구매발주서 PDF',type='pdf',key='po_upload'); m=st.file_uploader('시험성적서 PDF',type='pdf',key='mtr_upload')
        po=p.getvalue() if p else None; mtr=m.getvalue() if m else None
    signature=hashlib.sha256((po or b'')+b'\0'+(mtr or b'')+mode.encode()+provider.encode()).hexdigest()
    if st.session_state.get('quality_signature') != signature:
        st.session_state.pop('quality_review',None)
    if mode=='AI Agent Mode':
        st.caption('AI 문서 분석에는 시간이 걸릴 수 있습니다. 완료되면 아래에 검토 결과가 표시됩니다.')
    if st.button('AI 품질검사 실행' if mode=='AI Agent Mode' else '품질검사 실행',type='primary'):
        st.session_state.pop('quality_review',None)
        if not po or not mtr: st.error('구매발주서와 시험성적서를 모두 선택하세요.')
        else:
            try:
                with st.spinner('문서를 검토하고 있습니다...'):
                    school=provider=='기본 AI'
                    result=review(po,mtr,'ai' if mode=='AI Agent Mode' else 'rule',setting('SCHOOL_API_KEY' if school else 'OPENAI_API_KEY'),setting('SCHOOL_MODEL' if school else 'OPENAI_MODEL'),provider='school' if school else 'openai',base_url=setting('SCHOOL_API_BASE_URL') if school else None)
                st.session_state['quality_review']=result
                st.session_state['quality_signature']=signature
                st.success('문서 검토가 완료되었습니다. 아래에서 결과와 근거를 확인하세요.')
            except ValueError as exc: st.error(f'분석 설정 또는 문서 오류: {str(exc)[:200]}')
            except Exception as exc: st.error(f'분석을 완료하지 못했습니다. {type(exc).__name__}. API 설정과 연결 상태를 확인하세요.')
    result=st.session_state.get('quality_review')
    if result:
        st.subheader(f"문서 기반 사전 검토: {result['verdict']}")
        st.write('실행 모드:',result['mode'])
        st.write('소재:',result['mtr'].get('Material Grade'),'| 공급업체:',result['mtr'].get('Supplier'),'| Certificate:',result['mtr'].get('Certificate Number'))
        st.write('Heat:',result['mtr'].get('Heat Number'),'| Lot:',result['mtr'].get('Lot Number'))
        st.markdown('**요구조건과 검사 결과**')
        if result['mode']=='AI Agent Mode':
            display=[]
            for row in result['rows']:
                display.append({'항목':row['field'], 'LLM 원본':row.get('llm_raw'), 'LLM 단위':row.get('llm_raw_unit'), 'LLM 정규화':str(row.get('llm_normalized') or ''), 'Python 추출':str(row.get('python_value') or ''), '검사값':str(row.get('comparison_value') or ''), '검사값 출처':row.get('comparison_source') or '없음', '원문 근거':row.get('evidence') or '', '문서':row.get('document'), '페이지':row.get('page'), '근거 상태':row.get('evidence_status'), '교차 확인':row.get('cross_check_status'), 'PO 근거 상태':row.get('po_evidence_status'), 'PO LLM 조건':str(row.get('po_llm_bounds') or ''), 'PO 근거':str(row.get('po_evidence') or ''), '규격 비교':('FAIL' if row['result'] in ('OUT_OF_RANGE','MISMATCH') else row['result']), '추가 검토 사유':'; '.join(row.get('review_reasons',[]))})
            st.dataframe(display,hide_index=True,width='stretch')
            st.caption('규격 비교 PASS는 별도로 표시된 원문 근거 확인 상태와 구분됩니다. 검사값이 없으면 비교하지 않습니다.')
            with st.expander('식별정보 LLM·Python 교차 확인'): st.dataframe(result.get('identity_records',[]),hide_index=True,width='stretch')
        else: st.dataframe(result['rows'],hide_index=True,width='stretch')
        st.write('부적합 및 확인 필요 사항',result['findings'] or '없음')
        if result['mode']=='AI Agent Mode':
            st.caption('다음 설명은 AI 생성 문장으로 별도 검증이 필요합니다. 판정은 프로그램 결과입니다.')
            st.write(result['summary'])
            extracted=result.get('extraction',{}).get('fields',[])
            st.markdown('**AI가 추출한 값과 원문 근거**')
            st.dataframe(extracted,hide_index=True,width='stretch')
        with st.expander('도구 실행 기록 및 근거'): st.json(result['tool_log'])
        st.download_button('검토 보고서 HTML 다운로드',render_report(result),file_name='quality_review.html',mime='text/html')
        st.info('담당자는 원본과 실물을 확인하고 최종 승인 또는 보류를 결정해야 합니다.')
