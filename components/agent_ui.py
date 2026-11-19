import csv, os, hashlib
from pathlib import Path
import streamlit as st
from src.agent.orchestrator import review
from src.reporting.quality_report import render_report

ROOT=Path(__file__).resolve().parents[1]
def setting(name):
    try: return st.secrets.get(name) or os.getenv(name)
    except Exception: return os.getenv(name)

def reset_followup_checks():
    for key in list(st.session_state):
        if key.startswith('followup_check_'):
            del st.session_state[key]

def agent_ui():
    st.markdown('### AeroTitan Quality Agent')
    st.warning('교육용 모의 데이터 전용입니다. 실제 기업 기밀자료를 업로드하지 마세요. 검토 결과는 최종 입고 승인이 아닙니다.')
    mode=st.radio('검토 방식',['Rule-Based Mode','AI Agent Mode'],horizontal=True,key='agent_mode',format_func=lambda x: '규칙 기반 검토' if x=='Rule-Based Mode' else 'AI 문서 검토')
    st.caption('규칙 기반 모드는 정해진 교육용 PDF 형식만 지원합니다. AI 모드는 선택한 API 설정이 필요합니다.')
    provider=st.radio('AI 서비스',['기본 AI','OpenAI'],horizontal=True,key='agent_provider') if mode=='AI Agent Mode' else 'OpenAI'
    source=st.radio('문서 선택',['문서','직접 업로드'],horizontal=True,key='agent_source')
    po=mtr=None
    if source=='문서':
        with (ROOT/'data/metadata/cases.csv').open(encoding='utf-8',newline='') as f: cases=[r for r in csv.DictReader(f) if r['split']=='development']
        item=st.selectbox('검토할 문서 선택',cases,format_func=lambda r:f"{r['case_id']} · {r['supplier'].replace(' (Fictional)', '')}",key='agent_case')
        po=(ROOT/item['purchase_order']).read_bytes();mtr=(ROOT/item['material_test_report']).read_bytes()
    else:
        p=st.file_uploader('구매발주서 PDF',type='pdf',key='po_upload'); m=st.file_uploader('시험성적서 PDF',type='pdf',key='mtr_upload')
        po=p.getvalue() if p else None; mtr=m.getvalue() if m else None
    signature=hashlib.sha256((po or b'')+b'\0'+(mtr or b'')+mode.encode()+provider.encode()).hexdigest()
    if st.session_state.get('quality_signature') != signature:
        st.session_state.pop('quality_review',None)
        st.session_state.pop('followup_draft',None)
        st.session_state.pop('followup_email',None)
        st.session_state.pop('followup_subject',None)
        reset_followup_checks()
    if mode=='AI Agent Mode':
        st.caption('AI 문서 분석에는 시간이 걸릴 수 있습니다. 완료되면 아래에 검토 결과가 표시됩니다.')
    if st.button('AI 품질검사 실행' if mode=='AI Agent Mode' else '품질검사 실행',type='primary'):
        st.session_state.pop('quality_review',None)
        st.session_state.pop('followup_draft',None)
        st.session_state.pop('followup_email',None)
        st.session_state.pop('followup_subject',None)
        reset_followup_checks()
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
        label={'CONFORMING':'적합','NONCONFORMING':'부적합','REVIEW_REQUIRED':'추가 검토 필요'}.get(result['verdict'],result['verdict'])
        st.subheader(f"문서 기반 사전 검토: {label} ({result['verdict']})")
        st.write('실행 모드:',result['mode'])
        if result['mode']=='AI Agent Mode':
            from src.agent.tool_registry import NAMES
            called={x.get('tool') for x in result.get('tool_log',[]) if x.get('origin')=='model_function_call' and x.get('status')=='success' and x.get('tool') in NAMES}
            st.caption(f'AI가 호출해 성공한 검증 도구: {len(called)} / {len(NAMES)}개. 상세 실행 기록에서 호출 주체와 실패 여부를 확인할 수 있습니다.')
            if any(x.get('origin')=='python_report_fallback' and x.get('status')=='success' for x in result.get('tool_log',[])):
                st.info('AI가 보고서 데이터 구성 도구를 완료하지 않아 Python이 별도로 실행했습니다. HTML 보고서는 별도 함수가 생성합니다.')
        st.write('소재:',result['mtr'].get('Material Grade'),'| 공급업체:',result['mtr'].get('Supplier'),'| Certificate:',result['mtr'].get('Certificate Number'))
        st.write('Heat:',result['mtr'].get('Heat Number'),'| Lot:',result['mtr'].get('Lot Number'))
        st.markdown('**요구조건과 검사 결과**')
        if result['mode']=='AI Agent Mode':
            summary_rows=[]
            for row in result['rows']:
                checked=row.get('comparison_value') or {}
                status=row.get('result','NOT_CHECKED')
                summary_rows.append({'항목':row['field'],'PO 요구조건':row.get('requirement','') if row.get('po_evidence_status')=='VERIFIED' else '원문 확인 필요',
                    'MTR 검사값':(' '.join(str(checked.get(k,'')) for k in ('value','unit')).strip() if checked else '확인 불가'),
                    '비교 결과':{'PASS':'적합','OUT_OF_RANGE':'부적합','MISMATCH':'불일치','NOT_CHECKED':'확인 필요'}.get(status,status),
                    '측정값 출처':row.get('comparison_source') or '없음',
                    'PO 기준 출처':row.get('po_comparison_source') or '미확인',
                    '원문 근거':('확인' if row.get('evidence_status')=='VERIFIED' and row.get('po_evidence_status')=='VERIFIED' else '확인 필요')})
            st.dataframe(summary_rows,hide_index=True,width='stretch')
            st.caption('비교 결과는 교육용 기준에 대한 사전 검사입니다. 원문 근거가 부족하면 확인 필요로 표시합니다.')
            display=[]
            for row in result['rows']:
                display.append({'항목':row['field'], 'LLM 원본':row.get('llm_raw'), 'LLM 단위':row.get('llm_raw_unit'), 'LLM 정규화':str(row.get('llm_normalized') or ''), 'Python 추출':str(row.get('python_value') or ''), '검사값':str(row.get('comparison_value') or ''), '검사값 출처':row.get('comparison_source') or '없음', '원문 근거':row.get('evidence') or '', '문서':row.get('document'), '페이지':row.get('page'), '근거 상태':row.get('evidence_status'), '교차 확인':row.get('cross_check_status'), 'PO 근거 상태':row.get('po_evidence_status'), 'PO LLM 조건':str(row.get('po_llm_bounds') or ''), 'PO 근거':str(row.get('po_evidence') or ''), '규격 비교':('FAIL' if row['result'] in ('OUT_OF_RANGE','MISMATCH') else row['result']), '추가 검토 사유':'; '.join(row.get('review_reasons',[]))})
            with st.expander('항목별 추출값 및 원문 근거 상세'): st.dataframe(display,hide_index=True,width='stretch')
            with st.expander('식별정보 LLM·Python 교차 확인'): st.dataframe(result.get('identity_records',[]),hide_index=True,width='stretch')
            with st.expander('AI 원문 인용 확인 기록'):
                st.write(result.get('extraction_issues') or '확인되지 않은 AI 인용 없음')
        else: st.dataframe(result['rows'],hide_index=True,width='stretch')
        st.markdown('**부적합 및 확인 필요 사항**')
        if result['findings']:
            st.dataframe([{'항목':f.get('field',''), '유형':f.get('type',''),
                '내용':f.get('detail') or ('기준: '+str(f.get('expected',''))+' / 측정: '+str(f.get('actual',''))+' '+str(f.get('unit',''))),
                '출처':f.get('source','검증 도구')} for f in result['findings']],hide_index=True,width='stretch')
        else: st.write('발견 사항 없음')
        if result['verdict'] in ('NONCONFORMING','REVIEW_REQUIRED'):
            st.markdown('### AI 후속 대응 방향')
            st.caption('선택 기능: 확인된 검사 근거를 바탕으로 우선 확인 사항과 대응 선택지를 제안합니다. AI 요청이 추가됩니다.')
            st.warning('제안은 담당자의 검토를 위한 참고 사항입니다. 확인되지 않은 원인은 추정하지 않으며 최종 조치와 승인은 담당자가 결정합니다.')
            from src.agent.followup_draft import verified_facts
            facts=verified_facts(result)
            st.markdown('**검사로 확인된 사실과 원문 근거**')
            shown=[]
            for fact in facts['verified_measurements']:
                shown.append({'항목':fact['field'],'PO 요구조건':fact['requirement'],
                    'MTR 검사값':f"{fact['measurement']['value']} {fact['measurement']['unit']}",
                    'PO 근거':'; '.join(f"{e.get('page','?')}쪽: {' '.join(e.get('quote','').split())}" for e in fact['po_evidence']),
                    'MTR 근거':f"{fact['mtr_evidence']['page']}쪽: {' '.join((fact['mtr_evidence']['quote'] or '').split())}"})
            for fact in facts['verified_identity']:
                shown.append({'항목':fact['field'],'PO 요구조건':next((r['value'] for r in fact['records'] if r['document']=='PO'),''),
                    'MTR 검사값':next((r['value'] for r in fact['records'] if r['document']=='MTR'),''),
                    'PO 근거':next((f"{r['page']}쪽: {r['quote']}" for r in fact['records'] if r['document']=='PO'),''),
                    'MTR 근거':next((f"{r['page']}쪽: {r['quote']}" for r in fact['records'] if r['document']=='MTR'),'')})
            if shown: st.dataframe(shown,hide_index=True,width='stretch')
            else: st.info('원문이 확인된 부적합 항목이 없습니다. 대응 방향은 원문 확인부터 시작해야 합니다.')
            if facts['unconfirmed_items']:
                st.caption('미확인 항목은 원문에 값이 없다는 뜻이 아닙니다. 원문에서 다시 확인해야 합니다.')
                st.dataframe(facts['unconfirmed_items'],hide_index=True,width='stretch')
            st.markdown('**담당자 확인표**')
            st.caption('담당자가 직접 확인한 항목만 표시하세요. 체크 상태는 현재 화면에서만 유지되며, 실제 소재 보류나 공식 검사 기록을 뜻하지 않습니다.')
            checks=[
                ('소재 식별정보 확인', 'PO·MTR과 입고 소재의 Heat·Lot을 대조해 같은 소재의 문서인지 확인합니다.'),
                ('시험성적서 원문 확인', '문제 항목의 수치와 단위를 원본 MTR에서 확인합니다.'),
                ('발주 요구조건 원문 확인', '구매발주서에서 요구조건과 상한·하한, 단위를 확인합니다.'),
                ('소재의 현재 상태 확인', '담당자가 보류 여부와 생산 투입 상태를 확인합니다. 이 화면은 실제 상태를 조회하지 않습니다.'),
                ('추가 자료와 조치 필요성 확인', '확인 결과에 따라 시험 기록, 재시험, 공급업체 확인 등이 필요한지 내부 절차에 따라 검토합니다.'),
            ]
            for index,(title,reason) in enumerate(checks):
                st.checkbox(title,key=f'followup_check_{index}')
                st.caption(reason)
            if st.button('AI 대응 방향 확인'):
                st.session_state.pop('followup_draft',None)
                st.session_state.pop('followup_email',None)
                st.session_state.pop('followup_subject',None)
                try:
                    from src.agent.followup_draft import create_draft
                    with st.spinner('후속 대응 방향을 정리하고 있습니다...'):
                        draft=create_draft(result,setting('SCHOOL_API_KEY'),setting('SCHOOL_API_BASE_URL'),setting('SCHOOL_MODEL'))
                    st.session_state['followup_draft']=draft
                except ValueError as exc: st.error(f'대응 방향을 정리하지 못했습니다: {str(exc)[:200]}')
                except Exception as exc: st.error(f'대응 방향을 정리하지 못했습니다: {type(exc).__name__}. AI 서비스 연결 상태를 확인하세요.')
            draft=st.session_state.get('followup_draft')
            if draft:
                labels=[('immediate','이번 사례의 우선 확인'),('options','확인 결과에 따른 대응 선택지')]
                for key,title in labels:
                    st.markdown(f'**{title} · AI 제안**');st.write(draft['draft'][key])
                st.caption('AI 제안은 실행된 조치가 아닙니다. 내용과 근거를 확인한 뒤 담당자가 결정합니다.')
                text='AI 후속 대응 제안 — 담당자 확인 필요\n\n'+'\n\n'.join(f"{title}\n{draft['draft'][key]}" for key,title in labels)
                st.download_button('대응 방향 TXT 다운로드',text,file_name='quality_followup_guidance.txt',mime='text/plain')
                with st.expander('AI에 전달된 검사 근거'): st.json(draft['facts'])
        if result['mode']=='AI Agent Mode':
            st.caption('다음 설명은 AI 생성 문장으로 별도 검증이 필요합니다. 판정은 프로그램 결과입니다.')
            st.write(result['summary'])
            extracted=result.get('extraction',{}).get('fields',[])
            st.markdown('**AI가 추출한 값과 원문 근거**')
            st.dataframe(extracted,hide_index=True,width='stretch')
        with st.expander('도구 실행 기록 및 근거'): st.json(result['tool_log'])
        st.download_button('검토 보고서 HTML 다운로드',render_report(result),file_name='quality_review.html',mime='text/html')
        st.info('담당자는 원본과 실물을 확인하고 최종 승인 또는 보류를 결정해야 합니다.')
