"""Optional, human-reviewed follow-up guidance; never changes a verdict."""
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
    system=('당신은 교육용 소재 입고검사 후속 대응 방향을 제안합니다. 제공된 JSON만 검사 사실의 근거로 사용하세요. '
        '확인되지 않은 수치, 원인, 승인, 시험 결과의 정정 여부, 날짜, 문서 번호를 만들지 마세요. '
        '제공된 확인 사실이 없으면 원문 확인이 필요하다고 명시하세요. 결과는 사전 검토 결과이며 '
        '불합격 처리했다, 불합격 판정을 내린다, 최종 판정이나 처분이 확정됐다 같은 표현은 금지합니다. '
        'PO는 요구조건을 기재한 구매발주서이고 MTR은 측정값을 기재한 시험성적서입니다. 요구조건과 측정값이 동일해야 한다고 표현하지 마세요. '
        'PO는 공급자나 시험기관이 제출·발행한 문서라고 단정하지 마세요. MTR은 제출된 시험성적서이며 내부에서 직접 시험했다고 쓰지 마세요. '
        '제공되지 않은 문서 약어나 다른 문서를 만들지 마세요. '
        'unconfirmed_items는 미확인 항목이며 원문에 값이 존재하지 않는다는 뜻이 아닙니다. '
        '원인은 확인되지 않았으며 최종 결정은 담당자가 합니다. '
        '검사 사실과 확인되지 않은 사항을 구분하고 후속 대응을 실행한 것처럼 쓰지 마세요. 제공된 정보만으로 기타 미확인 사항이나 문제가 없다고 단정하지 마세요. '
        '검사 사실과 공통 확인표는 화면에 이미 표시됩니다. 같은 내용을 반복하지 마세요. '
        '이 사례에 필요한 서로 다른 세 가지 가상 확인 결과를 제시하고 각 결과에 따른 다음 검토 행동과 이유를 작성하세요. '
        '문서나 소재 식별정보가 불명확한 경우, 이 검사에서 확인한 부적합이나 불일치가 원문에서 재확인되는 경우, '
        '원인 또는 실제 소재 상태가 여전히 확인되지 않은 경우를 각각 조건으로 다루세요. '
        '두 번째 조건은 "부적합이 재확인되는 경우" 같은 일반 표현 대신, 제공된 실제 문제 항목명을 포함하세요. '
        '관련 확인값이 제공되었으면 기준과 측정값을 구분해 정확한 단위와 함께 행동 또는 이유에 언급하세요. '
        '각 조건은 아직 발생하지 않은 가정이며, condition은 "~한 경우"로 쓰고 action은 실행 가능한 검토 행동, why는 한 문장 이유로 쓰세요. '
        '검증 가능한 근거가 부족하면 먼저 원문 확인을 권고하고 가정한 원인이나 해결책을 확정하지 마세요. '
        '재시험, 문서 정정, 공급업체 문의는 필요성과 승인 여부를 담당자가 검토할 선택지로만 제시하세요. '
        '이메일을 작성하지 마세요. 번호 목록 숫자는 쓰지 마세요. '
        '한국어 JSON 객체만 반환하세요. 형식은 {"branches":[{"condition":"...","action":"...","why":"..."}]}이며 branches에는 서로 다른 세 항목이 필요합니다.')
    response=client.chat.completions.create(model=model,messages=[{'role':'system','content':system},{'role':'user','content':json.dumps(facts,ensure_ascii=False)}])
    if not response.choices or getattr(response.choices[0],'finish_reason',None)=='length': raise ValueError('AI 초안 응답이 비어 있거나 잘렸습니다.')
    raw=(response.choices[0].message.content or '').strip()
    if raw.startswith('```') and '\n' in raw: raw=raw.split('\n',1)[1].rsplit('```',1)[0].strip()
    try: draft=json.loads(raw)
    except (ValueError,TypeError) as exc: raise ValueError('AI 초안 형식을 확인할 수 없습니다.') from exc
    if not isinstance(draft,dict) or not isinstance(draft.get('branches'),list) or len(draft['branches'])!=3:
        raise ValueError('AI 제안에 필요한 세 가지 조건이 빠졌습니다.')
    keys=('condition','action','why')
    if any(not isinstance(branch,dict) or any(not isinstance(branch.get(k),str) or not branch[k].strip() for k in keys) for branch in draft['branches']):
        raise ValueError('AI 제안에 조건, 검토 행동 또는 이유가 빠졌습니다.')
    if len({b['condition'].strip() for b in draft['branches']})!=3:
        raise ValueError('AI 제안에 중복된 조건이 있습니다.')
    if re.search(r'(불합격|부적합)\s*(처리|확정|통보)|판정을\s*내리|최종\s*(승인|판정).{0,12}(완료|확정|처리)|내부\s*(시험|측정)|기타\s*미확인\s*사항.{0,10}없',json.dumps(draft,ensure_ascii=False)):
        raise ValueError('AI 초안에 확인되지 않은 처분 또는 시험 출처가 포함되어 표시하지 않았습니다.')
    numbers=lambda x:set(re.findall(r'(?<![\d.])\d+(?:\.\d+)?',x))
    if numbers(json.dumps(draft,ensure_ascii=False))-numbers(json.dumps(facts,ensure_ascii=False)):
        raise ValueError('AI 초안에 확인되지 않은 숫자가 포함되어 표시하지 않았습니다.')
    acronyms=lambda s:set(re.findall(r'(?<![A-Za-z])[A-Z]{2,}(?![A-Za-z])',s))
    permitted=acronyms(json.dumps(facts,ensure_ascii=False)) | {'PO','MTR','AI'}
    if acronyms(json.dumps(draft,ensure_ascii=False))-permitted:
        raise ValueError('AI 제안에 확인되지 않은 약어가 포함되어 표시하지 않았습니다.')
    return {'draft':{'branches':[{k:branch[k] for k in keys} for branch in draft['branches']]},'facts':facts,'usage':str(getattr(response,'usage',None))}
