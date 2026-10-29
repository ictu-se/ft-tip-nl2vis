from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
d=json.loads((root/'evidence/evidence_summary.json').read_text())
(root/'regenerated_tables').mkdir(exist_ok=True)
rows=d['summary'];fams=sorted({r['family'] for r in rows})
methods=['Initial','Typed','Result type','nvAgent','LIDA','Structural','Selector','Replacement','Permutation']
def get(m,f):return next(r for r in rows if r['method']==m and r['family']==f)
def table(name,caption,label,cols,header,body,foot=''):
 text='\\begin{table}[pos=htb]\n\\centering\n\\caption{'+caption+'}\n\\label{'+label+'}\n\\begin{tabular}{@{}'+cols+'@{}}\n\\toprule\n'+header+'\\\\\n\\midrule\n'+'\n'.join(body)+'\n\\bottomrule\n\\end{tabular}\n'+foot+'\n\\end{table}\n'
 (root/'regenerated_tables'/name).write_text(text)
body=[]
for m in methods:
 a,b=[get(m,f) for f in fams]
 body.append(m+' & '+' & '.join(str(r[k]) for r in [a,b] for k in ['common_success','data_correct','order_correct'])+r' \\')
table('table_accuracy.tex','Public raw-table outcomes, each out of 86. Complete is numerical, mark, physical order and selected visibility jointly; Numeric is strict full-relation agreement. All configurations use the same queries and same within-family model blob.','tab:accuracy','lrrrrrr',r'& \multicolumn{3}{c}{Gemma} & \multicolumn{3}{c}{Qwen}\\\cmidrule(lr){2-4}\cmidrule(lr){5-7} Configuration & Complete & Numeric & Order & Complete & Numeric & Order',body)
body=[]
for m in methods:
 a,b=[get(m,f) for f in fams]
 body.append(m+' & '+' & '.join(str(r[k]) for r in [a,b] for k in ['unflagged_success','official_data_component'])+r' \\')
table('table_sensitivity.tex','Fixed reference sensitivity and secondary numerical checker. Unflagged counts complete outputs among the same 73 preselected queries. Published data counts the unmodified VisEval data-check component among all 86; it is not full VisEval accuracy.','tab:sensitivity','lrrrr',r'& \multicolumn{2}{c}{Gemma} & \multicolumn{2}{c}{Qwen}\\\cmidrule(lr){2-3}\cmidrule(lr){4-5} Configuration & Unflagged /73 & Published /86 & Unflagged /73 & Published /86',body)
body=[]
for m in methods:
 if m in ['Replacement','Permutation']:continue
 vals=[]
 for f in fams:
  r=get(m,f);vals.extend([str(r['model_calls']),f"{r['input_tokens']/1000:.1f}",f"{r['output_tokens']/1000:.1f}"])
 body.append(m+' & '+' & '.join(vals)+r' \\')
table('table_cost.tex','Total inference cost on 86 queries per family. Tokens are in thousands. Replacement and permutation have exactly the Selector costs; they add no model inference. Structural includes both generators even when only one chart is returned.','tab:cost','lrrrrrr',r'& \multicolumn{3}{c}{Gemma} & \multicolumn{3}{c}{Qwen}\\\cmidrule(lr){2-4}\cmidrule(lr){5-7} Configuration & Calls & Input & Output & Calls & Input & Output',body)
