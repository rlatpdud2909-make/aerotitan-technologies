import json
import re
from decimal import Decimal, InvalidOperation
from openai import OpenAI
from src.agent.schemas import Extraction, ToolArguments
from src.agent.field_names import canonical_identity, canonical_measurement
from src.agent.prompts import EXTRACT_INSTRUCTIONS, AGENT_INSTRUCTIONS
from src.agent.tool_registry import NAMES, run_tool, tool_inputs

TOOLS=[{'type':'function','name':name,'description':('Prepare report data; HTML is generated separately by Python.' if name=='build_quality_report' else f'Execute {name} using validated server-side document data.'),'parameters':{'type':'object','properties':{},'required':[],'additionalProperties':False},'strict':True} for name in NAMES]

class ExtractionTruncated(ValueError):
    pass

class ExtractionFormatError(ValueError):
    pass

def extract(client,model,context,provider="openai",include_verified=False):
    text='\n'.join(f'{kind} PAGE {i}:\n{p}' for kind,key in [('PO','po_pages'),('MTR','mtr_pages')] for i,p in enumerate(context[key],1))
    if provider == 'school':
        prompt = EXTRACT_INSTRUCTIONS + "\nReturn only JSON in this format: {\"fields\":[{\"document\":\"PO or MTR\",\"field\":\"...\",\"value\":\"...\",\"unit\":\"...\",\"page\":1,\"quote\":\"...\"}]}. No markdown."
        response = client.chat.completions.create(model=model, messages=[{'role':'system','content':prompt},{'role':'user','content':text}])
        if response.choices and getattr(response.choices[0], 'finish_reason', None) == 'length':
            raise ExtractionTruncated('Extraction response reached a length limit; no retry attempted.')
        if not response.choices or not response.choices[0].message.content: raise ValueError('학교 API의 추출 응답이 비어 있습니다.')
        raw=response.choices[0].message.content.strip()
        if raw.startswith('```'):
            raw=raw.split('\n',1)[1].rsplit('```',1)[0].strip()
        try:
            extraction=Extraction.model_validate_json(raw)
        except ValueError as exc:
            raise ExtractionFormatError('Invalid extraction JSON or schema; no retry attempted.') from exc
    else:
        response=client.responses.parse(model=model,store=False,input=[{'role':'system','content':EXTRACT_INSTRUCTIONS},{'role':'user','content':text}],text_format=Extraction)
        if response.output_parsed is None: raise ValueError('AI의 구조화된 추출 응답이 비어 있습니다.')
        extraction=response.output_parsed
    verified=[]; issues=[]
    def element_name(label):
        # Only element symbols used by this demo, optionally preceded by Element.
        match=re.fullmatch(r'(?:element\s+)?(al|v|fe|o|c|n|h)',label.strip(),re.IGNORECASE)
        return {'al':'Al','v':'V','fe':'Fe','o':'O','c':'C','n':'N','h':'H'}.get(match.group(1).lower()) if match else None
    def decimal_equal(left,right):
        try: return Decimal(str(left)) == Decimal(str(right))
        except (InvalidOperation, ValueError): return False
    for item in extraction.fields:
        pages=context['po_pages' if item.document=='PO' else 'mtr_pages']
        if item.document == 'PO' and item.field.startswith('Material Dimensions '):
            continue
        name=(canonical_measurement(item.field) if canonical_measurement(item.field) != item.field else canonical_identity(item.document,item.field)) if item.document == 'MTR' else element_name(item.field) or canonical_identity(item.document,item.field)
        quote=' '.join(item.quote.split())
        label_ok = name.lower() in quote.lower()
        value_ok = item.value in item.quote
        if item.document == 'MTR' and name in {r['field'] for r in context['spec']['rules']}:
            label_ok = quote == f'{name} {item.value} {item.unit}'
        if name != item.field and canonical_identity(item.document,item.field) == name:
            label_ok = quote == f'{name} {item.value}' and not item.unit
        if item.document == 'PO':
            # A requirement is accepted only when the exact four-cell row is
            # present in the PO, the program confirmed it, and units match.
            suffix=re.fullmatch(r'(.+?)\s+(minimum|maximum)',item.field,re.IGNORECASE)
            base=(element_name(suffix.group(1)) or suffix.group(1)) if suffix else name
            rule=next((r for r in context['spec']['rules'] if r['field']==base),None)
            if rule:
                row=f"{base} {rule.get('min','-')} {rule.get('max','-')} {rule['unit']}"
                row_ok=(base in context['valid_rules'] and quote == row and item.unit == rule['unit'])
                if suffix:
                    bound='min' if suffix.group(2).lower()=='minimum' else 'max'
                    label_ok=value_ok=(row_ok and bound in rule and decimal_equal(item.value,rule[bound]))
                elif base in ('Al','V','Fe','O','C','N','H'):
                    text_value=' '.join(item.value.lower().split())
                    range_match=re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)\s*(?:to|[-–])\s*([0-9]+(?:\.[0-9]+)?)',text_value)
                    max_match=re.fullmatch(r'(?:up to|<=|≤)\s*([0-9]+(?:\.[0-9]+)?)',text_value)
                    if range_match and 'min' in rule and 'max' in rule:
                        value_ok=decimal_equal(range_match.group(1),rule['min']) and decimal_equal(range_match.group(2),rule['max'])
                    elif max_match and 'max' in rule and 'min' not in rule:
                        value_ok=decimal_equal(max_match.group(1),rule['max'])
                    label_ok=row_ok
        if item.page<1 or item.page>len(pages) or not quote or quote not in ' '.join(pages[item.page-1].split()) or not value_ok or (item.unit and item.unit not in item.quote) or not label_ok:
            issues.append(f'AI 추출 근거 확인 실패: {item.document} {item.field}'); continue
        verified.append((item,name))
    if not any(item.document == 'MTR' for item in extraction.fields):
        issues.append('MTR extraction returned no fields.')
    for rule in context['spec']['rules']:
        if not any(item.document == 'MTR' and canonical_measurement(item.field) == rule['field'] for item in extraction.fields):
            issues.append('MTR measurement not extracted: ' + rule['field'])
    for field, item in context['values'].items():
        if not any(f.document=='MTR' and name==field and f.value==item['value'] and f.unit==item['unit'] for f,name in verified):
            issues.append(f'AI 추출값과 원본 대조 필요: {field}')
    result=(extraction, issues, getattr(response,'usage',None))
    return (*result, verified) if include_verified else result

def call_tools(client,model,context):
    messages=[{'role':'system','content':AGENT_INSTRUCTIONS},{'role':'user','content':'Run all six available quality review tools for the supplied, already validated documents.'}]
    results={}; log=[]; usage=[]; final=''
    for _ in range(8):
        response=client.responses.create(model=model,store=False,input=messages,tools=TOOLS,parallel_tool_calls=False)
        usage.append(str(getattr(response,'usage',None))); messages.extend(response.output)
        calls=[item for item in response.output if item.type=='function_call']
        if not calls:
            final=response.output_text or ''; break
        for call in calls:
            try:
                if call.name not in NAMES: raise ValueError('Tool not allowed')
                args=ToolArguments.model_validate_json(call.arguments)
                result=run_tool(call.name,context); results[call.name]=result
                log.append({'origin':'model_function_call','call_id':call.call_id,'tool':call.name,'arguments':args.model_dump(),'comparison_inputs':tool_inputs(call.name,context),'status':'success','result':result})
                payload={'ok':True,'result':result}
            except Exception as exc:
                results.pop(call.name,None)
                log.append({'origin':'model_function_call','call_id':call.call_id,'tool':call.name,'arguments':call.arguments,'status':'failed','result':str(exc)})
                payload={'ok':False,'error':'Invalid or failed tool call'}
            messages.append({'type':'function_call_output','call_id':call.call_id,'output':json.dumps(payload,ensure_ascii=False)})
    return results,log,final,usage

def get_client(api_key, base_url=None):
    if not api_key: raise ValueError('OPENAI_API_KEY가 설정되지 않았습니다.')
    return OpenAI(api_key=api_key,base_url=base_url,timeout=45,max_retries=0)


class ToolsUnsupported(Exception):
    pass

def call_school_tools(client, model, context):
    from openai import BadRequestError
    tools=[{'type':'function','function':{'name':t['name'],'description':t['description'],'parameters':t['parameters']}} for t in TOOLS]
    messages=[{'role':'system','content':AGENT_INSTRUCTIONS},{'role':'user','content':'Run all six available quality review tools for the supplied, already validated documents.'}]
    results={}; log=[]; usage=[]; final=''
    for _ in range(8):
        try:
            response=client.chat.completions.create(model=model,messages=messages,tools=tools,tool_choice='auto')
        except BadRequestError as exc:
            detail=str(exc).lower()
            if 'tool' in detail and any(x in detail for x in ('not support','unsupported','not allowed','not implemented')):
                raise ToolsUnsupported('The provider explicitly rejected tool calling.') from exc
            raise
        usage.append(str(getattr(response,'usage',None)))
        if not response.choices: raise ValueError('학교 API가 빈 응답을 반환했습니다.')
        message=response.choices[0].message
        calls=message.tool_calls or []
        messages.append(message.model_dump(exclude_none=True))
        if not calls:
            final=message.content or ''; break
        for call in calls:
            if call.type != 'function': raise ValueError('지원하지 않는 도구 호출 유형입니다.')
            name=call.function.name
            try:
                if name not in NAMES: raise ValueError('Tool not allowed')
                args=ToolArguments.model_validate_json(call.function.arguments)
                result=run_tool(name,context); results[name]=result
                log.append({'origin':'model_function_call','call_id':call.id,'tool':name,'arguments':args.model_dump(),'comparison_inputs':tool_inputs(name,context),'status':'success','result':result})
                payload={'ok':True,'result':result}
            except Exception:
                results.pop(name,None)
                log.append({'origin':'model_function_call','call_id':call.id,'tool':name,'status':'failed','result':'Invalid or failed tool call'})
                payload={'ok':False,'error':'Invalid or failed tool call'}
            messages.append({'role':'tool','tool_call_id':call.id,'content':json.dumps(payload,ensure_ascii=False)})
    return results,log,final,usage
