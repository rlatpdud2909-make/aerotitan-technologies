from src.documents.pdf_parser import extract_pdf
from src.documents.field_extractor import parse_demo, lines
from src.agent.tool_registry import NAMES,run_tool,summarize,tool_inputs

def review(po_bytes,mtr_bytes,mode='rule',api_key=None,model=None,client=None,provider='openai',base_url=None):
    context=parse_demo(extract_pdf(po_bytes),extract_pdf(mtr_bytes))
    if mode=='rule':
        results={}; log=[]
        for name in NAMES:
            try:
                results[name]=run_tool(name,context); log.append({'origin':'python_rule_mode','call_id':None,'tool':name,'arguments':{},'status':'success','result':results[name]})
            except Exception as exc: log.append({'origin':'python_rule_mode','call_id':None,'tool':name,'arguments':{},'status':'failed','result':str(exc)})
        return summarize(context,results,'Rule-Based Mode',log,'규칙 기반 문서 검토. AI 호출 없음.')
    if mode!='ai': raise ValueError('지원하지 않는 분석 모드입니다.')
    if not model: raise ValueError(('SCHOOL_MODEL' if provider=='school' else 'OPENAI_MODEL')+'을 설정하세요. 계정에서 사용 가능한 모델을 지정해야 합니다.')
    if provider=='school' and not api_key and client is None: raise ValueError('SCHOOL_API_KEY를 설정하세요.')
    from src.agent.llm_client import get_client,extract,call_tools,call_school_tools,ToolsUnsupported
    if provider not in ('openai','school'): raise ValueError('지원하지 않는 API 공급자입니다.')
    if provider=='school' and not base_url: raise ValueError('SCHOOL_API_BASE_URL을 설정하세요.')
    client=client or get_client(api_key,base_url if provider=='school' else None)
    extraction, issues, extraction_usage, verified=extract(client,model,context,provider,include_verified=True)
    from src.agent.reconciliation import reconcile
    python_context=context
    context=reconcile(python_context,extraction,verified)
    # Preserve model evidence warnings for audit; only resolve a PO warning when
    # the complete source row was independently checked without conflicts.
    context['extraction_issues']=list(issues)
    resolved=set()
    from src.agent.field_names import canonical_measurement
    import re
    for record in context['records']:
        if record.get('po_comparison_source')!='Python 원문 독립 확인': continue
        for field in extraction.fields:
            suffix=re.fullmatch(r'(.+?)\s+(minimum|maximum)',field.field,re.I)
            base=canonical_measurement(suffix.group(1) if suffix else field.field)
            if field.document=='PO' and base==record['field']:
                resolved.add(f'AI 추출 근거 확인 실패: PO {field.field}')
    context['issues'].extend(x for x in issues if x not in resolved)
    try:
        results,log,summary,usage=(call_school_tools(client,model,context) if provider=='school' else call_tools(client,model,context))
    except ToolsUnsupported:
        results={}; log=[]; summary='학교 API가 도구 호출을 지원하지 않아 Python이 검증을 실행했습니다.'; usage=[]
        for name in NAMES:
            try:
                results[name]=run_tool(name,context)
                log.append({'origin':'python_fallback','call_id':None,'tool':name,'comparison_inputs':tool_inputs(name,context),'status':'success','result':results[name]})
            except Exception:
                log.append({'origin':'python_fallback','call_id':None,'tool':name,'status':'failed','result':'Tool failed'})
    # Do not allow a model to call missing-fields before extraction issues are considered or suppress mandatory findings.
    if 'detect_missing_fields' in results:
        results['detect_missing_fields']=run_tool('detect_missing_fields',context)
        log.append({'origin':'python_safety_recheck','call_id':None,'tool':'detect_missing_fields','arguments':{},'status':'success','result':results['detect_missing_fields']})
    # Keep independently observed Python violations without using Python values as LLM inputs.
    independent=[]
    for name in ('validate_material_identity','validate_chemical_composition','validate_mechanical_properties','validate_traceability'):
        for item in run_tool(name,python_context):
            if item.get('type') not in ('OUT_OF_RANGE','MISMATCH'): continue
            if item['type']=='MISMATCH':
                from src.agent.reconciliation import IDENTITY
                mapping={'PO Number':'Purchase Order Reference'}
                field=item['field']; pair=next(((p,m) for p,m in IDENTITY if p==field or mapping.get(field)==m),None)
                if not pair: continue
                pf,mf=pair; pv=python_context['po'].get(pf); mv=python_context['mtr'].get(mf)
                labels={x for pair in IDENTITY for x in pair}|{'Certificate Number','Test Date','Manufacturer','Applicable Specification'}
                def anchored(pages,label,value):
                    tokens=lines(pages)
                    return bool(value and value not in labels and tokens.count(label)==1 and tokens.index(label)+1<len(tokens) and tokens[tokens.index(label)+1]==value)
                if not (anchored(python_context['po_pages'],pf,pv) and anchored(python_context['mtr_pages'],mf,mv)): continue
            independent.append(dict(item,source='Python independent original-document check'))
    if independent:
        results['python_independent']=independent
        log.append({'origin':'python_independent','call_id':None,'tool':'independent_original_document_checks','status':'success','result':independent})
    report=summarize(context,results,'AI Agent Mode',log,summary)
    for row in report['rows']:
        record=next((r for r in context['records'] if r['field']==row['field']),None)
        if record:
            row.update(record)
            if record['comparison_value'] is None:
                row['result']='NOT_CHECKED'
    report['extraction']=extraction.model_dump(); report['extraction_issues']=context['extraction_issues']; report['usage']={'extraction':str(extraction_usage),'tool_calls':usage}
    return report
