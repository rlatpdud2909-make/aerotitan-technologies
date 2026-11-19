"""Reconcile model evidence with the separate synthetic-document parser."""
import copy
import re
from decimal import Decimal, InvalidOperation
from src.quality.rule_validation import convert
from src.agent.field_names import canonical_identity, canonical_measurement

CHEM={'Al','V','Fe','O','C','N','H'}
IDENTITY=[('Material Grade','Material Grade'),('Product Form','Product Form'),('Material Condition','Material Condition'),('Supplier','Supplier'),('PO Number','Purchase Order Reference'),('Specification Revision','Specification Revision'),('Required Specification','Applicable Specification'),('Required Heat Number','Heat Number'),('Required Lot Number','Lot Number')]

def norm_symbol(name):
    return canonical_measurement(name)

def equal_number(a,b):
    try: return Decimal(str(a)).is_finite() and Decimal(str(a))==Decimal(str(b))
    except (InvalidOperation,ValueError,TypeError): return False

def independent_po_rule(rule, context, fields):
    """Verify one unambiguous educational PO row without concealing conflicts."""
    pages=context.get('po_pages', [])
    if len(pages)!=1 or rule['field'] not in context['valid_rules']:
        return None
    tokens=[line.strip() for line in pages[0].splitlines() if line.strip()]
    header=['Requirement','Minimum','Maximum','Unit']
    starts=[i for i in range(len(tokens)-3) if tokens[i:i+4]==header]
    indexes=[i for i,x in enumerate(tokens) if x==rule['field']]
    row=[rule['field'],str(rule.get('min','-')),str(rule.get('max','-')),rule['unit']]
    if len(starts)!=1 or len(indexes)!=1 or indexes[0]<=starts[0]+3 or tokens[indexes[0]:indexes[0]+4]!=row:
        return None
    bounds={k:str(rule[k]) for k in ('min','max') if k in rule}; seen=set()
    for f in fields:
        suffix=re.fullmatch(r'(.+?)\s+(minimum|maximum)',f.field,re.I)
        base=norm_symbol(suffix.group(1)) if suffix else norm_symbol(f.field)
        if f.document!='PO' or base!=rule['field']: continue
        matches=[k for k,v in bounds.items() if equal_number(f.value,v)]
        declared=('min' if suffix.group(2).lower()=='minimum' else 'max') if suffix else None
        # The model's quote can be incomplete or incorrect. The PO criterion is
        # taken solely from the independently verified row, never that quote.
        # Any conflicting value, bound, unit, duplicate or page still blocks it.
        if (len(matches)!=1 or f.unit!=rule['unit'] or (declared and declared!=matches[0])
            or matches[0] in seen or f.page!=1): return None
        seen.add(matches[0])
    return {'page':1,'quote':' '.join(row),'bounds':bounds}

def po_rule_verified(rule, verified, all_fields=None):
    """Require the model to extract every applicable bound from the PO."""
    needed={bound for bound in ('min','max') if bound in rule}; seen=set(); used=[]; values={}
    # An unqualified numeric value is a bound only if the whole original row
    # and unit were independently verified, and it matches exactly one bound.
    raw_numeric=[]
    for f in all_fields or []:
        suffix=re.fullmatch(r'(.+?)\s+(minimum|maximum)',f.field,re.I)
        base=norm_symbol(suffix.group(1)) if suffix else norm_symbol(f.field)
        if f.document=='PO' and base==rule['field']:
            try:
                value=Decimal(f.value)
                if value.is_finite(): raw_numeric.append(f)
            except (InvalidOperation,ValueError,TypeError):
                pass
    if raw_numeric:
        seen_bounds=[]
        row=f"{rule['field']} {rule.get('min','-')} {rule.get('max','-')} {rule['unit']}"
        for f in raw_numeric:
            matching=[bound for bound in needed if equal_number(f.value,rule[bound])]
            suffix=re.fullmatch(r'(.+?)\s+(minimum|maximum)',f.field,re.I)
            declared=('min' if suffix.group(2).lower()=='minimum' else 'max') if suffix else None
            if (len(matching)!=1 or f.unit!=rule['unit'] or
                ' '.join(f.quote.split())!=row or
                (declared is not None and declared!=matching[0]) or
                not any(f is candidate for candidate,_ in verified)):
                return False, [], {}
            seen_bounds.append(matching[0])
        if len(seen_bounds)!=len(set(seen_bounds)):
            return False, [], {}
    for f,name in verified:
        if f.document!='PO': continue
        suffix=re.fullmatch(r'(.+?)\s+(minimum|maximum)',f.field,re.I)
        base=norm_symbol(suffix.group(1)) if suffix else norm_symbol(f.field)
        if base!=rule['field'] or f.unit!=rule['unit']: continue
        if suffix:
            bound='min' if suffix.group(2).lower()=='minimum' else 'max'
            if bound in needed and equal_number(f.value,rule[bound]): seen.add(bound);values[bound]=f.value;used.append(f)
        else:
            value=' '.join(f.value.lower().split())
            matching=[bound for bound in needed if equal_number(f.value,rule[bound])]
            row=f"{rule['field']} {rule.get('min','-')} {rule.get('max','-')} {rule['unit']}"
            if len(matching)==1 and ' '.join(f.quote.split())==row:
                bound=matching[0];seen.add(bound);values[bound]=f.value;used.append(f)
                continue
            m=re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)\s*(?:to|[-–])\s*([0-9]+(?:\.[0-9]+)?)',value)
            u=re.fullmatch(r'(?:up to|<=|≤)\s*([0-9]+(?:\.[0-9]+)?)',value)
            if m and needed=={'min','max'} and equal_number(m.group(1),rule['min']) and equal_number(m.group(2),rule['max']): seen.update(needed);values.update(min=m.group(1),max=m.group(2));used.append(f)
            elif u and needed=={'max'} and equal_number(u.group(1),rule['max']): seen.add('max');values['max']=u.group(1);used.append(f)
    return needed.issubset(seen), used, values

def reconcile(context, extraction, verified):
    result=copy.deepcopy(context); result['values']={}; result['valid_rules']=[];result['issues']=list(context['issues']);records=[]; llm_rules=[]
    all_fields=extraction.fields
    for rule in context['spec']['rules']:
        name=rule['field']; py=context['values'].get(name)
        raw=[x for x in all_fields if x.document=='MTR' and norm_symbol(x.field)==name]
        confirmed=[x for x,n in verified if x.document=='MTR' and n==name]
        required_ok,po_evidence,po_values=po_rule_verified(rule,verified,all_fields)
        independent=None if required_ok else independent_po_rule(rule,context,all_fields)
        if independent:
            required_ok=True; po_values=independent['bounds']
        # Missing values and duplicate or contradictory model readings are never substituted.
        selected=confirmed[0] if len(raw)==1 and len(confirmed)==1 else None
        reasons=[]
        if not required_ok or name not in context['valid_rules']: reasons.append('PO 요구조건의 LLM 추출 또는 원문 근거 부족')
        if selected is None: reasons.append('MTR LLM 값 누락, 중복 또는 근거 미확인')
        if py is None: reasons.append('Python 원문 교차검증 값 없음')
        if selected and py:
            try:
                if convert(selected.value,selected.unit,rule['unit'])!=convert(py['value'],py['unit'],rule['unit']): reasons.append('LLM과 Python의 값 또는 단위 불일치')
            except (ValueError,TypeError,InvalidOperation): reasons.append('단위 또는 수치 검증 불가')
        comparison=None
        if not reasons:
            comparison={'value':selected.value,'unit':selected.unit};result['values'][name]=comparison;result['valid_rules'].append(name)
            llm_rule=dict(rule);llm_rule.update(po_values);llm_rules.append(llm_rule)
        else:
            result['issues'].append(f'{name}: '+ '; '.join(reasons))
        records.append({'field':name,'llm_raw':raw[0].value if raw else None,'llm_raw_unit':raw[0].unit if raw else None,'llm_normalized':{'value':selected.value,'unit':selected.unit} if selected else None,'python_value':py,'comparison_value':comparison,'comparison_source':'LLM' if comparison else None,'document':'MTR','page':raw[0].page if raw else None,'evidence':raw[0].quote if raw else None,'evidence_status':'VERIFIED' if selected else 'UNVERIFIED','cross_check_status':'MATCH' if selected and py and not any('不一致' in x or '불일치' in x or '검증 불가' in x for x in reasons) else 'UNVERIFIED','po_llm_bounds':po_values,'po_comparison_source':'LLM' if required_ok else None,'po_evidence':[{'page':x.page,'quote':x.quote,'value':x.value} for x in po_evidence],'po_evidence_status':'VERIFIED' if required_ok and name in context['valid_rules'] else 'UNVERIFIED','review_reasons':reasons})
        if independent:
            records[-1].update(po_llm_bounds={},po_llm_evidence_status='UNVERIFIED',po_comparison_bounds=po_values,
                po_comparison_source='Python 원문 독립 확인',
                po_evidence=[{'page':independent['page'],'quote':independent['quote']}])
    result['spec']=dict(context['spec'],rules=llm_rules)
    po={};mtr={}; identity_records=[]
    for pfield,mfield in IDENTITY:
        for doc,field,dest in [('PO',pfield,po),('MTR',mfield,mtr)]:
            py=context[doc.lower()].get(field)
            raw=[x for x in all_fields if x.document==doc and canonical_identity(doc,x.field)==field]
            valid=[x for x,n in verified if x.document==doc and n==field and ' '.join(x.quote.split())==f'{field} {x.value}' and x.value==py]
            selected=valid[0] if len(raw)==1 and len(valid)==1 else None
            if selected: dest[field]=selected.value
            else: result['issues'].append(f'{doc} {field}: LLM 값 또는 원문·Python 대조 확인 필요')
            identity_records.append({'field':field,'document':doc,'llm_field_name':raw[0].field if raw else None,'llm_raw':raw[0].value if raw else None,'llm_normalized':selected.value if selected else None,'python_value':py,'comparison_value':selected.value if selected else None,'comparison_source':'LLM' if selected else None,'page':raw[0].page if raw else None,'evidence':raw[0].quote if raw else None,'evidence_status':'VERIFIED' if selected else 'UNVERIFIED','review_reasons':[] if selected else ['LLM 값 누락 또는 원문·Python 대조 실패']})
    # Other MTR/PO fields remain visible for backwards-compatible reporting only.
    result['po']=dict(context['po']); result['mtr']=dict(context['mtr'])
    for pfield,mfield in IDENTITY:
        result['po'][pfield]=po.get(pfield);result['mtr'][mfield]=mtr.get(mfield)
    # These required certificate fields do not have corresponding PO values.
    for field in ('Certificate Number','Test Date'):
        py=context['mtr'].get(field)
        raw=[x for x in all_fields if x.document=='MTR' and x.field==field]
        valid=[x for x,n in verified if x.document=='MTR' and x.field==field and ' '.join(x.quote.split())==f'{field} {x.value}' and x.value==py]
        selected=valid[0] if len(raw)==1 and len(valid)==1 else None
        result['mtr'][field]=selected.value if selected else None
        if not selected: result['issues'].append(f'MTR {field}: LLM 값 또는 원문·Python 대조 확인 필요')
        identity_records.append({'field':field,'document':'MTR','llm_raw':raw[0].value if raw else None,'llm_normalized':selected.value if selected else None,'python_value':py,'comparison_value':selected.value if selected else None,'comparison_source':'LLM' if selected else None,'page':raw[0].page if raw else None,'evidence':raw[0].quote if raw else None,'evidence_status':'VERIFIED' if selected else 'UNVERIFIED','review_reasons':[] if selected else ['LLM 값 누락 또는 원문·Python 대조 실패']})
    result['records']=records;result['identity_records']=identity_records;result['mode_source']='LLM'
    return result
