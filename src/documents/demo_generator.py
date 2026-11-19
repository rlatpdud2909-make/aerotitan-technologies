import csv, json, random
from pathlib import Path
from src.quality.demo_spec import load_spec, ROOT
from src.quality.rule_validation import evaluate
from src.documents.pdf_utils import make_pdf

SUPPLIERS=['Northstar Alloy Supply (Fictional)','Meridian Metalworks (Fictional)','Aster Materials Group (Fictional)']
BASE={'Al':('6.00','wt%'),'V':('4.00','wt%'),'Fe':('0.18','wt%'),'O':('0.12','wt%'),'C':('0.03','wt%'),'N':('0.02','wt%'),'H':('0.005','wt%'),'Yield Strength':('900','MPa'),'Ultimate Tensile Strength':('970','MPa'),'Elongation':('14','%')}

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def generate():
    rng=random.Random(20261112); spec=load_spec(); categories=['normal']*12+['chemical']*6+['mechanical']*5+['identity']*4+['missing']*3
    # Stratification with shuffled IDs avoids grouping outcomes by case number.
    dev=['normal']*8+['chemical']*4+['mechanical']*3+['identity']*3+['missing']*2
    final=['normal']*4+['chemical']*2+['mechanical']*2+['identity']+['missing']
    rng.shuffle(dev); rng.shuffle(final); categories=dev+final
    rows=[]
    for index,category in enumerate(categories,1):
        case=f'case_{index:03}'; split='development' if index<=20 else 'final_test'; supplier=SUPPLIERS[(index-1)%3]; layout='ABC'[(index-1)%3]
        po=f'AT-PO-2026-{index:03}'; cert=f'MTR-{7000+index}'; heat=f'HT-{3000+index}'; lot=f'LT-{5000+index}'
        values={k:{'value':v,'unit':u} for k,(v,u) in BASE.items()}
        if category=='normal' and index%2==0:
            values['Yield Strength']={'value':'130.5','unit':'ksi'}; values['Ultimate Tensile Strength']={'value':'140.7','unit':'ksi'}
        if category=='chemical':
            field=['Al','V','Fe','O','C','N'][index%6]; values[field]['value']={'Al':'6.60','V':'4.60','Fe':'0.32','O':'0.21','C':'0.09','N':'0.06'}[field]
        if category=='mechanical':
            field=['Yield Strength','Ultimate Tensile Strength','Elongation'][index%3]; values[field]['value']={'Yield Strength':'820','Ultimate Tensile Strength':'890','Elongation':'9'}[field]
            if field=='Ultimate Tensile Strength': values['Yield Strength']['value']='820' # preserve physical ordering, two documented violations
        ids={'Heat Number':heat,'Lot Number':lot,'Specification Revision':'V1'}; expected=ids.copy()
        if category=='identity': ids['Heat Number']=f'HT-{8000+index}'
        if category=='missing': values.pop(['H','Elongation','Fe'][index%3])
        verdict, findings=evaluate(spec,values,ids,expected)
        target={'normal':'CONFORMING','chemical':'NONCONFORMING','mechanical':'NONCONFORMING','identity':'NONCONFORMING','missing':'REVIEW_REQUIRED'}[category]
        assert verdict==target
        case_dir=ROOT/'data/demo_documents'/split/case; case_dir.mkdir(parents=True,exist_ok=True)
        po_path=case_dir/'purchase_order.pdf'; mtr_path=case_dir/'material_report.pdf'
        rule_rows=[['Requirement','Minimum','Maximum','Unit']]+[[r['field'],str(r.get('min','-')),str(r.get('max','-')),r['unit']] for r in spec['rules']]
        po_info=[['Field','Purchase requirement'],['PO Number',po],['Supplier',supplier],['Order Date','2026-01-15'],['Material Grade','Ti-6Al-4V'],['Product Form','Round Bar'],['Material Condition','Annealed'],['Required Specification','DEMO_SPEC_TI64_V1'],['Specification Revision','V1'],['Quantity','10 bars'],['Material Dimensions','Diameter 50 mm x 1000 mm'],['Required Delivery Date','2026-02-15'],['Required Heat Number',heat],['Required Lot Number',lot],['Required Certificate Information','MTR, certificate number, supplier, test date and all listed results']]
        make_pdf(po_path,'PURCHASE ORDER','AeroTitan Technologies | Fictional educational order', [('Order and material',po_info),('Synthetic quality requirements (inclusive)',rule_rows)])
        identity=[['Field','Reported value'],['Supplier',supplier],['Manufacturer',supplier],['Certificate Number',cert],['Purchase Order Reference',po],['Material Grade','Ti-6Al-4V'],['Product Form','Round Bar'],['Material Condition','Annealed'],['Heat Number',ids['Heat Number']],['Lot Number',ids['Lot Number']],['Applicable Specification','DEMO_SPEC_TI64_V1'],['Specification Revision',ids['Specification Revision']],['Test Date','2026-02-01']]
        chemical=['Al','V','Fe','O','C','N','H']; mech=['Yield Strength','Ultimate Tensile Strength','Elongation']
        if index%2==0: chemical=list(reversed(chemical))
        def measurements(keys): return [['Test','Result','Unit']]+[[k,values[k]['value'],values[k]['unit']] for k in keys if k in values]
        if layout=='A': blocks=[('Material identification',identity),('Chemical composition',measurements(chemical)),('Mechanical properties',measurements(mech))]
        elif layout=='B': blocks=[('Mechanical test results',measurements(mech)),('Certificate details',identity),('Composition by element',measurements(chemical))]
        else: blocks=[('Composition analysis',measurements(chemical)),('Mechanical test data',measurements(mech)),('Technical report identification',identity)]
        make_pdf(mtr_path,'MATERIAL TEST REPORT',f'{supplier} | Layout {layout} | Fictional technical document',blocks)
        gt=[]
        for n,(field,kind,actual,unit) in enumerate(findings,1):
            rule=next((r for r in spec['rules'] if r['field']==field),None)
            gt.append({'finding_id':f'F{n:02}','field_name':field,'expected_value_or_rule':rule if rule else expected.get(field),'actual_value':actual,'unit':unit,'finding_type':kind,'severity':'nonconformance' if kind in ('OUT_OF_RANGE','MISMATCH') else 'review','source_document':str(mtr_path.relative_to(ROOT)).replace('\\','/'),'source_page':1,'expected_reason':{'OUT_OF_RANGE':'Reported value violates the synthetic PO limit.','MISMATCH':'Reported identifier differs from the PO requirement.','MISSING':'Required item is absent from the MTR.','UNCLEAR_UNIT':'Unit cannot be verified.'}[kind]})
        paths={'purchase_order':str(po_path.relative_to(ROOT)).replace('\\','/'),'material_test_report':str(mtr_path.relative_to(ROOT)).replace('\\','/')}
        truth={'case_id':case,'purchase_order_id':po,'certificate_id':cert,'supplier_id':f'SUP-{(index-1)%3+1:02}','document_layout':layout,'material_grade':'Ti-6Al-4V','product_form':'Round Bar','material_condition':'Annealed','expected_verdict':verdict,'expected_findings':gt,'document_paths':paths,'requirement_set_id':spec['id'],'source_type':'SYNTHETIC_DEMO'}
        dump(ROOT/'data/ground_truth'/split/(case+'.json'),truth)
        dump(ROOT/'data/structured_cases'/split/(case+'.json'),{'category':category,'values':values,'identifiers':ids,'expected_identifiers':expected,'purchase_order_id':po,'certificate_id':cert})
        rows.append({'case_id':case,'split':split,'supplier':supplier,'material':'Ti-6Al-4V','purchase_order_id':po,'certificate_id':cert,'document_layout':layout,**paths})
    meta=ROOT/'data/metadata/cases.csv'; meta.parent.mkdir(parents=True,exist_ok=True)
    with meta.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print('Generated 30 PO PDFs, 30 MTR PDFs and 30 ground truth files.')
