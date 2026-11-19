from datetime import datetime, timezone
from html import escape

def render_report(r):
    def e(x): return escape(str(x if x is not None else ''))
    ai=r.get('mode')=='AI Agent Mode'
    if ai:
        cols=[('field','항목'),('llm_raw','LLM 원본'),('llm_raw_unit','LLM 단위'),('llm_normalized','LLM 정규화'),('python_value','Python 추출'),('comparison_value','검사값'),('comparison_source','검사값 출처'),('document','문서'),('page','페이지'),('evidence_status','MTR 근거 상태'),('cross_check_status','교차 확인'),('po_evidence_status','PO 근거 상태'),('po_llm_bounds','PO LLM 조건'),('po_evidence','PO 원문 근거'),('evidence','MTR 원문 근거'),('review_reasons','추가 검토 사유'),('requirement','요구조건'),('result','규격 비교')]
    else:
        cols=[('field','항목'),('requirement','요구조건'),('actual','측정값'),('unit','단위'),('result','결과'),('source','근거')]
    rows=''.join('<tr>'+''.join(f"<td>{e('FAIL' if k=='result' and row.get(k) in ('OUT_OF_RANGE','MISMATCH') else row.get(k))}</td>" for k,_ in cols)+'</tr>' for row in r['rows'])
    headers=''.join(f'<th>{e(label)}</th>' for _,label in cols)
    findings=''.join(f'<li>{e(f)}</li>' for f in r['findings']) or '<li>발견 사항 없음</li>'
    identity=''
    if ai:
        keys=[('document','문서'),('field','항목'),('llm_raw','LLM 값'),('python_value','Python 값'),('comparison_value','검사값'),('comparison_source','출처'),('evidence_status','근거 상태'),('evidence','원문 근거')]
        identity='<h3>식별정보 교차 확인</h3><table><tr>'+''.join(f'<th>{e(label)}</th>' for _,label in keys)+'</tr>'+''.join('<tr>'+''.join(f'<td>{e(row.get(k))}</td>' for k,_ in keys)+'</tr>' for row in r.get('identity_records',[]))+'</table>'
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>Receiving Material Quality Review</title><style>body{{font-family:Arial,sans-serif;max-width:1500px;margin:40px auto;line-height:1.5;color:#10243a}}table{{border-collapse:collapse;width:100%;font-size:12px}}td,th{{border:1px solid #b8c2cc;padding:7px;text-align:left;overflow-wrap:anywhere}}th{{background:#e7eef1}}.notice{{padding:15px;background:#f2f4f5}}</style></head><body><h1>AeroTitan Technologies</h1><h2>Receiving Material Quality Review</h2><p>{e(datetime.now(timezone.utc).isoformat())} / {e(r['mode'])}</p><p>PO: {e(r['po'].get('PO Number'))} | Certificate: {e(r['mtr'].get('Certificate Number'))}</p><p>Material: {e(r['mtr'].get('Material Grade'))} | Supplier: {e(r['mtr'].get('Supplier'))}</p><p>Heat: {e(r['mtr'].get('Heat Number'))} | Lot: {e(r['mtr'].get('Lot Number'))}</p><h3>화학 조성 및 기계적 물성</h3><p>규격 비교와 원문 근거 확인은 별도 상태입니다. 검사값이 없으면 비교하지 않습니다.</p><table><tr>{headers}</tr>{rows}</table>{identity}<h3>추적성 및 검토 사항</h3><ul>{findings}</ul><h2>문서 기반 사전 검토: {e(r['verdict'])}</h2><p>담당자 최종 확인: ____________________　일시: ____________________</p><p class="notice">본 결과는 교육용 모의 데이터 기반의 자동 검토 결과이며 실제 항공우주 소재의 최종 품질 승인 또는 인증을 의미하지 않습니다.</p></body></html>'''
