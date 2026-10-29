"""Portable saved-output audit. Python 3 standard library only; no model calls.

Run from the release root: python3 scripts/reproduce_counts.py
This verifies exported scores and artifact pair invariants, not fresh inference.
"""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence'
if not E.exists(): E=ROOT/'verification'
d=json.loads((E/'evidence_summary.json').read_text())
rows=json.loads((E/'core_scores.json').read_text())
groups=defaultdict(list)
for r in rows:groups[r['configuration'],r['family']].append(r)
for s in d['summary']:
 rr=groups[s['method'],s['family']]
 assert len(rr)==86 and len({r['sample_id'] for r in rr})==86
 assert len({r['db_id'] for r in rr})==19
 for key in ['common_success','data_correct','mark_correct','order_correct','selected_visibility_pass','official_data_component']:
  assert sum(bool(r[key]) for r in rr)==s[key],(s['method'],key)
 assert sum(r['common_success'] for r in rr if not r['flagged'])==s['unflagged_success']
 for key in ['model_calls','input_tokens','output_tokens']:
  assert sum(r[key] or 0 for r in rr)==s[key]
index={(r['configuration'],r['family'],r['sample_id']):r for r in rows}
for t in d['transitions']:
 rr=groups['Selector',t['family']];key=t['endpoint']
 gain=loss=0
 for a in rr:
  b=index[t['method'],a['family'],a['sample_id']]
  gain+=not a[key] and b[key];loss+=a[key] and not b[key]
 assert (gain,loss)==(t['gains'],t['losses'])
def relation(o):
 assert len(o['traces'])==1 and o['traces'][0]['mark']=='bar'
 return Counter((int(float(x)),float(y)) for x,y in o['traces'][0]['screen_order'])
for r in d['repair_checks']:assert relation(r['before'])==relation(r['after'])
assert len(d['repair_checks'])==10
manifest=ROOT/'MANIFEST.json'
if manifest.exists():
 for item in json.loads(manifest.read_text())['files']:
  p=ROOT/item['path'];assert p.is_file(),p
  assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],p
print(json.dumps({'status':'passed','configurations':len(groups),'saved_outcomes':len(rows),'repair_multisets':10,'model_calls_made':0,'scope':'Counts, transitions, saved pair invariants and packaged file hashes; not new inference or independent confirmation'},indent=2))
