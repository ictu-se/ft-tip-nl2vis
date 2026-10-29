"""Recompute every archived final-system interval from the exported scores.
Requires NumPy; uses the original 10,000-draw database-cluster design.
"""
from pathlib import Path
import json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence'
if not E.exists():E=ROOT/'verification'
data=json.loads((E/'core_scores.json').read_text())
report=json.loads((E/'evidence_summary.json').read_text())
mapping={'planner':'Initial','nvagent':'nvAgent','nvagent_casefold_artifact':'nvAgent','lida':'LIDA','source_boundary_repair_plus_calendar_domain':'Typed','output_unit_record_selection':'Result type','structural_fallback':'Structural','hybrid_reference_blind_selection':'Selector','hybrid_display_contract_guard':'Replacement'}
checked=[]
for c in report['contrasts']:
 target=mapping.get(c['against'])
 if target is None:
  # Match the retained guard identifier without changing any scores.
  if 'guard' in c['against']:target='Replacement'
  else:raise ValueError(c['against'])
 a={r['sample_id']:r for r in data if r['family']==c['family'] and r['configuration']=='Permutation' and (c['subset']=='all' or not r['flagged'])}
 b={r['sample_id']:r for r in data if r['family']==c['family'] and r['configuration']==target}
 dbs=sorted({r['db_id'] for r in a.values()})
 vals=[[int(r['common_success'])-int(b[i]['common_success']) for i,r in a.items() if r['db_id']==db] for db in dbs]
 totals=np.array([sum(v) for v in vals]);sizes=np.array([len(v) for v in vals])
 draws=np.random.default_rng(20261028).choice(len(dbs),size=(10000,len(dbs)),replace=True)
 ci=100*np.quantile(totals[draws].sum(axis=1)/sizes[draws].sum(axis=1),[.025,.975])
 assert np.allclose(ci,c['database_cluster_ci95_pp'],atol=1e-10),(c,ci)
 difference=100*sum(totals)/sum(sizes)
 assert abs(difference-c['difference_pp'])<1e-10
 checked.append({'family':c['family'],'against':target,'subset':c['subset'],'ci95_pp':ci.tolist()})
result={'status':'passed','contrasts_recomputed':len(checked),'resamples':10000,'seed':20261028,'numpy':np.__version__,'scope':'Exploratory adaptive public development; not selection-corrected','checks':checked}
(E/'interval_reproduction.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
