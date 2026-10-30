"""Re-execute the frozen repair rule on 172 saved choices; no LLM calls."""
import argparse,copy,hashlib,json,platform
from pathlib import Path
from repair import specification,relation
from vega_capture import capture
from screen_order import vega
import display_guard
ROOT=Path(__file__).resolve().parent

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'regenerated');args=parser.parse_args()
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
 records=json.loads((ROOT/'inputs.json').read_text());decisions=[];physical={};specs={};hashes={}
 assert len(records)==172
 for r in records:
  key=(r['family'],r['sample_id']);cc=r['candidates'];spec=specification(cc,r['selected_index'])
  # A perturbation check ensures unused correctness/path fields cannot alter policy.
  changed=copy.deepcopy(cc)
  for c in changed:
   c['benchmark_reference']={'not_used':True}
   for t in c['observed_output'].get('traces',[]):t['path_order']=list(reversed(t.get('path_order',[])))
  assert specification(changed,r['selected_index'])==spec
  decisions.append(dict(family=key[0],sample_id=key[1],repaired=spec is not None))
  if spec is None:continue
  folder=out/key[0]/key[1]
  obs=vega(capture(spec,folder),spec)
  assert relation(obs)==relation(cc[1]['observed_output'])
  assert obs['traces'][0]['mark']==cc[1]['observed_output']['traces'][0]['mark']=='bar'
  assert not display_guard.violations(obs,display_guard.contract_from(cc[0]['program']))
  physical[key]=obs;specs[key]=spec;hashes[key]=hashlib.sha256((folder/'chart.svg').read_bytes()).hexdigest()
  (folder/'physical.json').write_text(json.dumps(obs,indent=2)+'\n')
 # Seal all decisions before loading archived expected results for regression checking.
 (out/'decisions.json').write_text(json.dumps(decisions,indent=2)+'\n')
 expected=json.loads((ROOT/'expected.json').read_text());assert len(expected)==172
 assert decisions==[{k:e[k] for k in ['family','sample_id','repaired']} for e in expected]
 svg_matches=0
 for e in expected:
  if not e['repaired']:continue
  key=(e['family'],e['sample_id'])
  assert specs[key]==e['specification'],key
  assert physical[key]==e['physical'],key
  svg_matches+=hashes[key]==e['svg_sha256']
 assert len(physical)==10
 report={'status':'passed','saved_decisions':172,'decisions_matching_archive':172,'rendered_interventions':10,'specifications_matching_archive':10,'physical_captures_matching_archive':10,'svg_bytes_matching_archive':svg_matches,'exact_pair_and_mark_invariants_passed':10,'python':platform.python_version(),'new_model_calls':0,'independent_validation':False,'scope':'Actual rendering replay from saved choices; not fresh model inference or new accuracy evidence.'}
 (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
