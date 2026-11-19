"""Optional, human-reviewed follow-up draft; never changes an inspection verdict."""
import json
import re
from openai import OpenAI

def verified_facts(result):
    if result.get('verdict') not in ('NONCONFORMING', 'REVIEW_REQUIRED'):
        raise ValueError('부적합 또는 추가 검토 결과에서 사용할 수 있습니다.')
    facts={'verdict':result['verdict'],'verified_measurements':[], 'verified_identity':[], 'unconfirmed_items':[],
           'unverified_notice':'확인되지 않은 값과 원인은 추정하지 말고 원문 확인을 요청하세요.'}
    for row in result.get('rows',[]):
        if row.get('result')=='NOT_CHECKED':
            facts['unconfirmed_items'].append({'field':row['field'],'status':'검사에 필요한 근거 미확인'})
        if row.get('result') not in ('OUT_OF_RANGE','MISMATCH'): continue
        value=row.get('comparison_value')
        if not (value and row.get('evidence_status')=='VERIFIED' and row.get('po_evidence_status')=='VERIFIED' and row.get('cross_check_status')=='MATCH'):
            facts['unconfirmed_items'].append({'field':row['field'],'status':'검사 근거 추가 확인 필요'}); continue
        facts['verified_measurements'].append({'field':row['field'],'requirement':row['requirement'],
            'measurement':value,'po_evidence':row.get('po_evidence',[]),
            'mtr_evidence':{'page':row.get('page'),'quote':row.get('evidence')}})
    findings={(f.get('field'),f.get('type')) for f in result.get('findings',[])}
    for field in ('Heat Number','Lot Number'):
        if (field,'MISMATCH') not in findings: continue
        recs=[r for r in result.get('identity_records',[]) if (r.get('document'),r.get('field')) in (('PO','Required '+field),('MTR',field))]
        if len(recs)==2 and {r.get('document') for r in recs}=={'PO','MTR'} and all(r.get('evidence_status')=='VERIFIED' and r.get('comparison_value') and r.get('page') and r.get('evidence') for r in recs):
            facts['verified_identity'].append({'field':field,'records':[{'document':r['document'],'value':r['comparison_value'],'page':r.get('page'),'quote':r.get('evidence')} for r in recs]})
        else: facts['unconfirmed_items'].append({'field':field,'status':'식별정보 원문 확인 필요'})
    return facts

def create_draft(result, api_key, base_url, model, client=None):
    facts=verified_facts(result)
    if not all((api_key,base_url,model)) and client is None:
        raise ValueError('AI 서비스 설정을 확인하세요.')
    client=client or OpenAI(api_key=api_key,base_url=base_url,timeout=45,max_retries=0)
    system=('당신은 교육용 소재 입고검사 후속 검토 초안을 작성합니다. 제공된 JSON만 근거로 사용하세요. '
        '확인되지 않은 수치, 원인, 승인, 시험 결과의 정정 여부, 날짜, 문서 번호를 만들지 마세요. '
        '제공된 확인 사실이 없으면 원문 확인이 필요하다고 명시하세요. 결과는 사전 검토 결과이며 '
        '불합격 처리했다, 불합격 판정을 내린다, 최종 판정이나 처분이 확정됐다 같은 표현은 금지합니다. '
        'MTR은 제출된 시험성적서이며 내부에서 직접 시험했다고 쓰지 마세요. '
        'unconfirmed_items는 미확인 항목이며 원문에 값이 존재하지 않는다는 뜻이 아닙니다. '
        '원인은 확인되지 않았으며 최종 결정과 대외 발송은 담당자가 합니다. '
        '한국어 JSON 객체만 반환하세요. 필수 키는 review, supplier_request, email_subject, email_body이며 값은 문자열입니다. '
        '이메일은 발송하지 않는 초안이고 확인된 사실만 사용합니다.')
    response=client.chat.completions.create(model=model,messages=[{'role':'system','content':system},{'role':'user','content':json.dumps(facts,ensure_ascii=False)}])
    if not response.choices or getattr(response.choices[0],'finish_reason',None)=='length': raise ValueError('AI 초안 응답이 비어 있거나 잘렸습니다.')
    raw=(response.choices[0].message.content or '').strip()
    if raw.startswith('```') and '\n' in raw: raw=raw.split('\n',1)[1].rsplit('```',1)[0].strip()
    try: draft=json.loads(raw)
    except (ValueError,TypeError) as exc: raise ValueError('AI 초안 형식을 확인할 수 없습니다.') from exc
    keys=('review','supplier_request','email_subject','email_body')
    if not isinstance(draft,dict) or any(not isinstance(draft.get(k),str) or not draft[k].strip() for k in keys):
        raise ValueError('AI 초안에 필수 내용이 빠졌습니다.')
    if re.search(r'(불합격|부적합)\s*(처리|확정|통보)|판정을\s*내리|최종\s*(승인|판정|확정)|내부\s*(시험|측정)',json.dumps(draft,ensure_ascii=False)):
        raise ValueError('AI 초안에 확인되지 않은 처분 또는 시험 출처가 포함되어 표시하지 않았습니다.')
    numbers=lambda x:set(re.findall(r'(?<![\d.])\d+(?:\.\d+)?',x))
    if numbers(json.dumps(draft,ensure_ascii=False))-numbers(json.dumps(facts,ensure_ascii=False)):
        raise ValueError('AI 초안에 확인되지 않은 숫자가 포함되어 표시하지 않았습니다.')
    return {'draft':{k:draft[k] for k in keys},'facts':facts,'usage':str(getattr(response,'usage',None))}
