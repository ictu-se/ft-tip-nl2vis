"""Reconcile earlier supporting-panel counts; never pools distinct panels."""
from pathlib import Path
import json,collections
ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text())
a=read(ROOT/'supporting_panels/prepared_annual_case_scores.json');summary=read(ROOT/'supporting_panels/prepared_annual_summaries.json');groups=collections.defaultdict(list)
for r in a:groups[r['family'],r['condition']].append(r)
for s in summary['summaries']:
 rows=groups[s['family'],s['condition']];assert len(rows)==220
 rr=[r for r in rows if r['reference_executed']];assert len(rr)==199
 for field,expected in s['endpoints'].items():assert sum(r['comparison'].get(field) is True for r in rr)==expected['success'],(s['family'],s['condition'],field)
 assert len({r['sample_id'] for r in rows})==220 and len({r['dataset_id'] for r in rows})==15
b=read(ROOT/'supporting_panels/mark_retention_cases.json');mark=[]
for family,expected in [('gemma4_e4b',(53,45)),('qwen35_4b',(34,34))]:
 rows=[r for r in b if r['family']==family];assert len(rows)==64
 rr=[r for r in rows if r['relations']['gold']['status']=='executed'];assert len(rr)==57
 before=[r['before']['ordered_relation_agreement'] and r['before']['executed_pair'] for r in rr]
 after=[r['after']['ordered_relation_agreement'] and r['after']['executed_pair'] for r in rr]
 assert (sum(before),sum(after))==expected
 mark.append(dict(family=family,n=57,before=sum(before),after=sum(after),gains=sum(not x and y for x,y in zip(before,after)),losses=sum(x and not y for x,y in zip(before,after))))
print(json.dumps({'status':'passed','prepared_saved_case_scores':len(a),'prepared_config_family_groups':len(groups),'mark_base_requests':len(b),'mark_retention':mark,'new_model_calls':0,'scope':'Counts reconciled from saved per-case scores, not fresh inference, new annotation or independent final-method validation.'},indent=2))
