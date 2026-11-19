from src.quality.rule_validation import evaluate
from src.documents.field_extractor import CHEM

NAMES=['validate_material_identity','validate_chemical_composition','validate_mechanical_properties','validate_traceability','detect_missing_fields','build_quality_report']
def tool_inputs(name, context):
    if context.get('mode_source') != 'LLM': return {'source':'Python'}
    if name in ('validate_chemical_composition','validate_mechanical_properties'):
        return {'source':'LLM','values':{k:v for k,v in context['values'].items() if (k in CHEM)==(name=='validate_chemical_composition')}, 'verified_rule_fields':list(context['valid_rules']), 'rules':context['spec']['rules']}
    if name in ('validate_material_identity','validate_traceability'):
        return {'source':'LLM','po':{r['field']:r['comparison_value'] for r in context.get('identity_records',[]) if r['document']=='PO'}, 'mtr':{r['field']:r['comparison_value'] for r in context.get('identity_records',[]) if r['document']=='MTR'}}
    return {'source':'LLM','description':'Validated evidence and issue list' if name=='detect_missing_fields' else 'Report data aggregation; HTML generated separately'}

def run_tool(name, context):
    po,mtr=context['po'],context['mtr']
    if name=='validate_material_identity':
        pairs=[(k,po.get(k),mtr.get(k)) for k in ('Material Grade','Product Form','Material Condition')]
        pairs += [('Supplier',po.get('Supplier'),mtr.get('Supplier')),('PO Number',po.get('PO Number'),mtr.get('Purchase Order Reference')),('Applicable Specification',po.get('Required Specification'),mtr.get('Applicable Specification')),('Specification Revision',po.get('Specification Revision'),mtr.get('Specification Revision'))]
        return [{'field':k,'type':'MISMATCH','expected':a,'actual':b} for k,a,b in pairs if a and b and a!=b]
    if name in ('validate_chemical_composition','validate_mechanical_properties'):
        rules=[r for r in context['spec']['rules'] if r['field'] in context['valid_rules'] and (r['field'] in CHEM)==(name=='validate_chemical_composition')]
        _,found=evaluate({'rules':rules},context['values'],{}, {})
        return [{'field':f,'type':kind,'actual':v,'unit':u} for f,kind,v,u in found]
    if name=='validate_traceability':
        result=[]
        for k in ('Heat Number','Lot Number'):
            a,b=po.get('Required '+k),mtr.get(k)
            if a and b and a!=b: result.append({'field':k,'type':'MISMATCH','expected':a,'actual':b})
        return result
    if name=='detect_missing_fields': return [{'field':'document','type':'REVIEW','detail':x} for x in context['issues']]
    if name=='build_quality_report': return [{'field':'report','type':'INFO','detail':'Results assembled by Python after mandatory checks.'}]
    raise ValueError('Tool not allowed')

def summarize(context, results, mode, log, summary=''):
    findings=[item for name,items in results.items() if name!='build_quality_report' for item in items]
    incomplete=[name for name in NAMES if name not in results]
    if incomplete: findings.append({'field':'tools','type':'REVIEW','detail':'Missing or failed tools: '+', '.join(incomplete)})
    if any(x['type'] in ('OUT_OF_RANGE','MISMATCH') for x in findings): verdict='NONCONFORMING'
    elif findings: verdict='REVIEW_REQUIRED'
    else: verdict='CONFORMING'
    rows=[dict(row, result=next((f['type'] for f in findings if f.get('field')==row['field']), 'NOT_CHECKED' if any(n not in results for n in ('validate_chemical_composition','validate_mechanical_properties')) or row['field'] not in context['valid_rules'] else 'PASS')) for row in context['rows']]
    return {'mode':mode,'verdict':verdict,'findings':findings,'rows':rows,'po':context['po'],'mtr':context['mtr'],'tool_log':log,'summary':summary,'results':results, 'field_records':context.get('records',[]),'identity_records':context.get('identity_records',[])}
