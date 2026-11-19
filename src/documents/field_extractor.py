from decimal import Decimal, InvalidOperation
from src.quality.demo_spec import load_spec

CHEM={'Al','V','Fe','O','C','N','H'}
def lines(pages): return [line.strip() for page in pages for line in page.splitlines() if line.strip()]
def value_after(ls, label):
    indices=[i for i,x in enumerate(ls) if x==label]
    return ls[indices[0]+1] if len(indices)==1 and indices[0]+1<len(ls) else None

def parse_demo(po_pages,mtr_pages):
    po=lines(po_pages); mtr=lines(mtr_pages); spec=load_spec(); issues=[]
    if not po_pages or not mtr_pages or 'PURCHASE ORDER' not in po or 'MATERIAL TEST REPORT' not in mtr:
        raise ValueError('문서 종류가 올바르지 않거나 지원하지 않는 형식입니다.')
    if len(po_pages)!=1 or len(mtr_pages)!=1: issues.append('현재 규칙 기반 검토는 한 페이지 모의 문서만 지원합니다.')
    if 'SYNTHETIC TEST DATA — EDUCATIONAL USE ONLY' not in po or 'SYNTHETIC TEST DATA — EDUCATIONAL USE ONLY' not in mtr:
        issues.append('교육용 모의 문서 표시를 확인하지 못했습니다.')
    values={}; rows=[]; valid_rules=[]
    for rule in spec['rules']:
        name=rule['field']; candidates=[i for i,x in enumerate(po) if x==name]
        expected=[name,str(rule.get('min','-')),str(rule.get('max','-')),rule['unit']]
        if len(candidates)!=1 or po[candidates[0]:candidates[0]+4]!=expected:
            issues.append(f'{name}: 발주서 조건을 기준 JSON과 정확히 확인하지 못했습니다.')
        else: valid_rules.append(name)
        indexes=[i for i,x in enumerate(mtr) if x==name]
        val=None; unit=None
        if len(indexes)==1 and indexes[0]+2<len(mtr):
            val,unit=mtr[indexes[0]+1:indexes[0]+3]
            try:
                if not Decimal(val).is_finite(): raise InvalidOperation
                values[name]={'value':val,'unit':unit}
            except InvalidOperation: val=None; unit=None
        elif len(indexes)>1: issues.append(f'{name}: 중복된 시험 항목')
        rows.append({'field':name,'requirement':f"{rule.get('min','-')} ~ {rule.get('max','-')} {rule['unit']}",'actual':val,'unit':unit,'source':'MTR page 1'})
    po_fields={x:value_after(po,x) for x in ['PO Number','Supplier','Material Grade','Product Form','Material Condition','Required Specification','Specification Revision','Required Heat Number','Required Lot Number']}
    mtr_fields={x:value_after(mtr,x) for x in ['Purchase Order Reference','Supplier','Certificate Number','Material Grade','Product Form','Material Condition','Applicable Specification','Specification Revision','Heat Number','Lot Number','Test Date']}
    if po_fields['Required Specification']!=spec['id'] or mtr_fields['Applicable Specification']!=spec['id']: issues.append('모의 기준 ID가 없거나 일치하지 않습니다.')
    required_po=['PO Number','Supplier','Material Grade','Product Form','Material Condition','Required Specification','Specification Revision','Required Heat Number','Required Lot Number']
    required_mtr=['Purchase Order Reference','Supplier','Certificate Number','Material Grade','Product Form','Material Condition','Applicable Specification','Specification Revision','Heat Number','Lot Number','Test Date']
    for field in required_po:
        if not po_fields[field]: issues.append(f'PO 필수 항목 누락: {field}')
    for field in required_mtr:
        if not mtr_fields[field]: issues.append(f'MTR 필수 항목 누락: {field}')
    return {'spec':spec,'valid_rules':valid_rules,'values':values,'rows':rows,'po':po_fields,'mtr':mtr_fields,'issues':issues,'po_pages':po_pages,'mtr_pages':mtr_pages}
