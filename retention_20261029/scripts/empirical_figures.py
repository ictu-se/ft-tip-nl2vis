"""Publication figures from retained experimental records only. No image model.

Run with the project's matplotlib environment. Each plot exports its source
rows; native PNGs and repair SVGs are embedded without changing chart content.
"""
from pathlib import Path
from collections import Counter
import json, csv, hashlib, subprocess, sys, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'data'
A=ROOT/'regenerated_figures';A.mkdir(parents=True,exist_ok=True)
EDIR=ROOT/'evidence'
OUT=A/'audit';DATA=OUT/'figure_data';DATA.mkdir(parents=True,exist_ok=True)
E=json.loads((EDIR/'evidence_summary.json').read_text())
ROWS=json.loads((EDIR/'core_scores.json').read_text())
FAMS=sorted({r['family'] for r in ROWS});FN={FAMS[0]:'Gemma',FAMS[1]:'Qwen'}
METHODS=['Initial','Typed','Result type','nvAgent','LIDA','Structural','Selector','Replacement','Permutation']
SHORT=['I','T','RT','NV','L','S','H','G','P']
IDX={(r['family'],r['sample_id'],r['configuration']):r for r in ROWS}
BASE=[r for r in ROWS if r['family']==FAMS[0] and r['configuration']=='Selector']
DBS=sorted({r['db_id'] for r in BASE})
IDS=sorted([r['sample_id'] for r in BASE],key=lambda i:(IDX[FAMS[0],i,'Selector']['db_id'],i))
REF={r['sample_id']:r for r in [json.loads(l) for l in (B/'references.jsonl').read_text().splitlines()] if r['sample_id'] in IDS}
REPORT=json.loads((B/'contrasts.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.facecolor':'white'})
BLUE='#247a91';TEAL='#16846e';ORANGE='#db9d37';RED='#be4b43';GRAY='#e7e9ec'
def export(name,rows):
 (DATA/(name+'.json')).write_text(json.dumps(rows,indent=2))
 if rows and isinstance(rows,list) and isinstance(rows[0],dict):
  with (DATA/(name+'.csv')).open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def save(fig,name):
 fig.savefig(A/(name+'.pdf'),bbox_inches='tight');fig.savefig(A/(name+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)

# F2: Every case, not aggregate bars copied from the summary table.
fig,axs=plt.subplots(1,2,figsize=(7.8,7.8),sharey=True)
centers=[];edges=[-.5];db_labels=[]
for db in DBS:
 where=[j for j,i in enumerate(IDS) if IDX[FAMS[0],i,'Selector']['db_id']==db]
 centers.append(np.mean(where));edges.append(max(where)+.5)
 db_labels.append(db.replace('_',' ')+f' ({len(where)})')
label_centers=[]
for y in centers: label_centers.append(max(y,label_centers[-1]+2.5) if label_centers else y)
export_rows=[]
for ax,fam in zip(axs,FAMS):
 mat=[]
 for i in IDS:
  line=[]
  for m in METHODS:
   r=IDX[fam,i,m];state=2 if r['common_success'] else 1 if r['data_correct'] else 0
   assert not r['common_success'] or r['data_correct']
   line.append(state);export_rows.append(dict(family=fam,sample_id=i,db_id=r['db_id'],configuration=m,state=state,complete=r['common_success'],numerical=r['data_correct']))
  mat.append(line)
 ax.imshow(mat,aspect='auto',interpolation='nearest',cmap=ListedColormap([GRAY,ORANGE,TEAL]),vmin=0,vmax=2)
 ax.set_xticks(range(9),SHORT);ax.xaxis.tick_top();ax.tick_params(axis='x',length=0,pad=5)
 ax.set_title(FN[fam],pad=28,fontweight='bold')
 for y in edges:ax.axhline(y,color='white',lw=1.2)
 for x in np.arange(.5,9,1):ax.axvline(x,color='white',lw=.7)
 ax.set_yticks(label_centers,db_labels,fontsize=10);ax.tick_params(axis='y',length=0)
 if fam==FAMS[0]:
  for actual,label_y in zip(centers,label_centers):
   if abs(actual-label_y)>.01:ax.plot([-.7,-.5],[label_y,actual],color='#777',lw=.5,clip_on=False)
 for spine in ax.spines.values():spine.set_visible(False)
axs[1].tick_params(labelleft=False)
fig.legend(handles=[Patch(color=TEAL,label='Complete'),Patch(color=ORANGE,label='Numerically correct, incomplete'),Patch(color=GRAY,label='Numerical failure')],loc='lower center',ncol=1,frameon=False,bbox_to_anchor=(.57,-.015),fontsize=10)
fig.subplots_adjust(left=.28,right=.99,top=.90,bottom=.13,wspace=.08)
save(fig,'f2_case_atlas');export('f2_case_atlas',export_rows)

# F3: Exhaustive intervention inventory, including the replacement regressions.
repairs=sorted(E['repair_checks'],key=lambda r:(r['family'],r['sample_id']))
columns=[('Selector','data_correct'),('Replacement','data_correct'),('Permutation','data_correct'),('Selector','common_success'),('Replacement','common_success'),('Permutation','common_success')]
mat=[];labels=[];audit=[]
for r in repairs:
 fam,i=r['family'],r['sample_id'];vals=[int(IDX[fam,i,m][k]) for m,k in columns]
 mat.append(vals);labels.append(FN[fam][0]+' '+i.replace('viseval_','').replace('@y_name@',' y ').replace('@x_name@',' x '))
 audit.append(dict(family=fam,sample_id=i,**{m+'_'+k:bool(v) for (m,k),v in zip(columns,vals)},pairs=len(r['before']['traces'][0]['screen_order']),same_pair_multiset=True))
fig,ax=plt.subplots(figsize=(7.8,4.8));ax.imshow(mat,aspect='auto',cmap=ListedColormap([GRAY,TEAL]),vmin=0,vmax=1)
ax.set_xticks(range(6),['H','G','P','H','G','P']);ax.xaxis.tick_top();ax.tick_params(length=0)
ax.set_yticks(range(10),labels,fontsize=10)
for y,row in enumerate(mat):
 for x,val in enumerate(row):ax.text(x,y,str(val),ha='center',va='center',color='white' if val else '#4c5661',fontsize=12)
 ax.text(6.05,y,str(audit[y]['pairs']),ha='center',va='center',fontsize=11)
 ax.text(7.05,y,'=',ha='center',va='center',color=TEAL,fontsize=14,fontweight='bold')
 for x in [1]:
  if row[0] and not row[x]:ax.add_patch(plt.Rectangle((x-.48,y-.47),.96,.94,fill=False,edgecolor=RED,lw=2))
for y in np.arange(.5,10,1):ax.axhline(y,color='white',lw=.8)
ax.axhline(4.5,color='#555',lw=1.5);ax.axvline(2.5,color='white',lw=5)
ax.text(1,-1.15,'Numerical',ha='center',fontweight='bold');ax.text(4,-1.15,'Complete',ha='center',fontweight='bold')
ax.text(6.05,-.95,'Pairs',ha='center');ax.text(7.05,-.95,'Invariant',ha='center')
ax.set_xlim(-.5,7.7);ax.set_ylim(9.5,-.5)
for spine in ax.spines.values():spine.set_visible(False)
fig.subplots_adjust(left=.28,right=.98,top=.82,bottom=.08)
save(fig,'f3_intervention_inventory');export('f3_intervention_inventory',audit)

# F4: Reference distributions; query variants are not treated as independent databases.
db_order=sorted(DBS,key=lambda db:(-sum(r['db_id']==db for r in BASE),db))
coverage=[]
for db in db_order:
 rr=[r for r in BASE if r['db_id']==db];n=len(rr)
 marks=Counter(REF[r['sample_id']]['vis_obj']['chart'].lower() for r in rr)
 sorts=Counter('none' if not REF[r['sample_id']]['vis_obj'].get('sort') else REF[r['sample_id']]['vis_obj']['sort']['channel'] for r in rr)
 assert set(marks)<={'bar','line'} and set(sorts)<={'x','y','none'},(marks,sorts)
 coverage.append(dict(database=db,n=n,unflagged=sum(not r['flagged'] for r in rr),flagged=sum(r['flagged'] for r in rr),bar=marks['bar'],line=marks['line'],no_sort=sorts['none'],x_sort=sorts['x'],y_sort=sorts['y']))
assert sum(r['n'] for r in coverage)==86
fig,axs=plt.subplots(1,3,figsize=(7.8,5.8),sharey=True)
panels=[('Reference flags',['unflagged','flagged'],[BLUE,RED],['Unflagged','Flagged']),('Requested mark',['bar','line'],[TEAL,ORANGE],['Bar','Line']),('Sort requirement',['no_sort','x_sort','y_sort'],[GRAY,BLUE,ORANGE],['None','X','Y'])]
for ax,(title,fields,colors,names) in zip(axs,panels):
 left=np.zeros(19)
 for field,color,name in zip(fields,colors,names):
  vals=np.array([r[field] for r in coverage]);ax.barh(range(19),vals,left=left,color=color,height=.7,label=name);left+=vals
 ax.set_title(title,fontsize=11,fontweight='bold');ax.set_xlim(0,max(r['n'] for r in coverage)+1);ax.set_xlabel('Queries',fontsize=10)
 ax.set_xticks([0,5,10]);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
 ax.legend(loc='lower center',bbox_to_anchor=(.5,1.03),ncol=1,frameon=False,fontsize=9)
ax=axs[0];ax.set_yticks(range(19),[r['database'].replace('_',' ')+f" ({r['n']})" for r in coverage],fontsize=10);ax.invert_yaxis()
fig.subplots_adjust(left=.28,right=.99,top=.79,bottom=.10,wspace=.20)
save(fig,'f4_benchmark_coverage');export('f4_benchmark_coverage',coverage)

# F5: Four-state paired transitions for every measured component.
components=[('data_correct','Numeric'),('mark_correct','Mark'),('order_correct','Order'),('selected_visibility_pass','Visibility'),('common_success','Complete')]
trans=[]
for fam in FAMS:
 for method in ['Replacement','Permutation']:
  for field,label in components:
   c=Counter((bool(IDX[fam,i,'Selector'][field]),bool(IDX[fam,i,method][field])) for i in IDS)
   trans.append(dict(family=fam,policy=method,component=label,retained_correct=c[True,True],gain=c[False,True],loss=c[True,False],retained_failure=c[False,False]))
fig,axs=plt.subplots(1,2,figsize=(7.8,5.0),sharey=True)
for ax,fam in zip(axs,FAMS):
 rr=[r for r in trans if r['family']==fam];left=np.zeros(10)
 for field,color in [('retained_correct','#9bc8c2'),('gain',TEAL),('loss',RED),('retained_failure',GRAY)]:
  val=np.array([r[field] for r in rr]);ax.barh(range(10),val,left=left,height=.7,color=color);left+=val
 assert np.all(left==86)
 for y,r in enumerate(rr):ax.text(89,y,f"+{r['gain']} / -{r['loss']}",va='center',fontsize=10)
 ax.axhline(4.5,color='#555',lw=1);ax.set_xlim(0,118);ax.set_xticks([0,43,86]);ax.set_xlabel('Outcomes (86 per row)');ax.set_title(FN[fam],fontweight='bold')
 ax.text(89,-.8,'Gain / loss',fontsize=10)
 ax.set_yticks(range(10),['G: '+l for _,l in components]+['P: '+l for _,l in components],fontsize=11)
 ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
axs[0].invert_yaxis()
fig.legend(handles=[Patch(color='#9bc8c2',label='Retained correct'),Patch(color=TEAL,label='Gain'),Patch(color=RED,label='Loss'),Patch(color=GRAY,label='Retained failure')],loc='lower center',ncol=2,frameon=False,fontsize=10)
fig.subplots_adjust(left=.15,right=.99,top=.87,bottom=.22,wspace=.12)
save(fig,'f5_full_transitions');export('f5_full_transitions',trans)

# F6: Both endpoints, same retained paired bootstrap results.
targets=[('nvagent','nvAgent'),('lida','LIDA'),('source_boundary_repair_plus_calendar_domain','Typed'),('structural_fallback','Structural'),('hybrid_reference_blind_selection','Selector')]
forest=[];fig,axs=plt.subplots(1,2,figsize=(7.8,5.6),sharey=True)
for ax,fam in zip(axs,FAMS):
 for j,(target,name) in enumerate(targets):
  for offset,(key,label,color,marker) in enumerate([('contrasts','Complete',TEAL,'o'),('component_contrasts','Numerical',BLUE,'s')]):
   r=next(r for r in REPORT[key] if r['family']==fam and r['against']==target and r['subset']=='all')
   y=j*2+offset;v=r['difference_pp'];lo,hi=r['database_cluster_ci95_pp']
   ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt=marker,color=color,capsize=3,markersize=5)
   forest.append(dict(family=fam,comparator=name,endpoint=label,difference_pp=v,lower=lo,upper=hi,gain=r['gain'],loss=r['loss']))
  ax.axhline(j*2+1.5,color='#ddd',lw=.7)
 ax.axvline(0,ls='--',color='#555',lw=1);ax.set_xlim(-13,43);ax.set_xticks([-10,0,10,20,30,40]);ax.set_xlabel('Permutation - comparator (pp)',fontsize=10);ax.set_title(FN[fam],fontweight='bold')
axs[0].set_yticks(range(10),[name+'  '+end for _,name in targets for end in ['C','N']],fontsize=11);axs[0].invert_yaxis()
fig.legend(handles=[plt.Line2D([],[],marker='o',color=TEAL,label='C: complete'),plt.Line2D([],[],marker='s',color=BLUE,label='N: numerical')],loc='lower center',ncol=2,frameon=False)
fig.subplots_adjust(left=.19,right=.99,top=.91,bottom=.17,wspace=.12)
save(fig,'f6_joint_numeric_contrasts');export('f6_joint_numeric_contrasts',forest)

# F8: Full workload input and call cost; no uncharged generator branches.
cost=E['summary'];fig,axs=plt.subplots(1,2,figsize=(7.8,4.4),sharey=True)
for ax,fam in zip(axs,FAMS):
 rr=[next(r for r in cost if r['family']==fam and r['method']==m) for m in METHODS]
 for r,code in zip(rr,SHORT):
  x=r['input_tokens']/1000;y=100*r['common_success']/86
  ax.scatter(x,y,s=r['model_calls']*.36,color=TEAL if code=='P' else BLUE,alpha=.8,edgecolor='white',linewidth=.5,marker='D' if code=='P' else 'o')
  offsets={'I':(5,-2),'T':(-10,7),'RT':(5,-10),'NV':(5,0),'L':(5,0),'S':(-13,7),'H':(6,-10),'G':(6,8),'P':(6,0)}
  if fam==FAMS[1] and code=='G':offsets[code]=(14,-1)
  ax.annotate(code,(x,y),xytext=offsets[code],textcoords='offset points',fontsize=11)
 ax.set_xlim(90,1410);ax.set_ylim(35,91);ax.set_xticks([200,600,1000]);ax.set_xlabel('Input tokens (thousands)');ax.set_title(FN[fam],fontweight='bold');ax.grid(alpha=.13);ax.set_axisbelow(True)
axs[0].set_ylabel('Complete output (%)')
handles=[plt.scatter([],[],s=c*.36,color=BLUE,label=str(c)+' calls') for c in [86,172,426]]
fig.legend(handles=handles,loc='lower center',ncol=3,frameon=False,fontsize=10)
fig.subplots_adjust(left=.11,right=.99,top=.89,bottom=.24,wspace=.12)
save(fig,'f8_input_cost');export('f8_input_cost',cost)

# F1/F7: Original archived artifacts + exact captured-value strip.
vlpython=Path(os.environ.get('PAPER09_SVG_PYTHON',sys.executable))
for case,stem,failure in [('viseval_468@y_name@DESC_1','f1_actual_success',False),('viseval_3290@y_name@ASC_0','f7_actual_failure',True)]:
 fam=FAMS[0];r=next(r for r in repairs if r['family']==fam and r['sample_id']==case)
 png=B/'cases'/case/'native.png'
 svg=B/'cases'/case/'repair.svg'
 rendered=OUT/(stem+'_repair.png')
 subprocess.run([str(vlpython),'-c','import sys,vl_convert as v;from pathlib import Path;Path(sys.argv[2]).write_bytes(v.svg_to_png(Path(sys.argv[1]).read_text(),scale=2))',str(svg),str(rendered)],check=True)
 fig=plt.figure(figsize=(7.8,8.0));gs=fig.add_gridspec(3,1,height_ratios=[3,3,1.15],hspace=.15)
 for j,(path,label) in enumerate([(png,'(a) Native output: screen order fails'),(rendered,'(b) Actual permutation repair: screen order passes')]):
  ax=fig.add_subplot(gs[j]);ax.imshow(plt.imread(path));ax.axis('off');ax.set_title(label,fontsize=12,loc='left',pad=4)
 ax=fig.add_subplot(gs[2]);ax.axis('off')
 before=r['before']['traces'][0]['screen_order'];after=r['after']['traces'][0]['screen_order']
 if failure:
  years=sorted({int(float(x)) for x in REF[case]['vis_obj']['x_data'][0]})
  expected={int(float(x)):y for x,y in zip(REF[case]['vis_obj']['x_data'][0],REF[case]['vis_obj']['y_data'][0])}
  obs={int(float(x)):y for x,y in after}
  cells=[[str(y) for y in years],[str(expected[y]) for y in years],[str(obs[y]) if y in obs else 'missing' for y in years]]
  labels=['Year','Reference','Both outputs']
 else:
  cells=[[str(int(float(x))) for x,y in before],[str(y) for x,y in before],[str(int(float(x))) for x,y in after],[str(y) for x,y in after]];labels=['Native year','Native value','Repair year','Repair value']
 tab=ax.table(cellText=cells,rowLabels=labels,loc='center',cellLoc='center',bbox=[.16,0,.83,.98]);tab.auto_set_font_size(False);tab.set_fontsize(11)
 for (row,col),cell in tab.get_celld().items():
  cell.set_edgecolor('#ccd2d8');cell.set_linewidth(.5)
  if cell.get_text().get_text()=='missing':cell.set_facecolor('#f6d5d1');cell.get_text().set_color('#932d28')
 fig.subplots_adjust(left=.03,right=.99,top=.97,bottom=.02)
 save(fig,stem)
 export(stem,{'family':fam,'sample_id':case,'query':r['query'],'native_png':str(png.relative_to(ROOT)),'native_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'repair_svg':str(svg.relative_to(ROOT)),'repair_sha256':hashlib.sha256(svg.read_bytes()).hexdigest(),'before':before,'after':after,'reference':REF[case]['vis_obj'],'displayed_table':dict(zip(labels,cells))})

sources={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [EDIR/'core_scores.json',EDIR/'evidence_summary.json']}
sources[str((B/'references.jsonl').relative_to(ROOT))]=hashlib.sha256((B/'references.jsonl').read_bytes()).hexdigest()
manifest={'source':'Retained experimental scores, published references and actual archived chart artifacts','image_generation_used':False,'new_model_calls':0,'source_hashes':sources,'case_atlas_cells':len(export_rows),'interventions':len(audit),'benchmark_queries':sum(r['n'] for r in coverage),'full_transition_rows':len(trans),'paired_contrasts':len(forest),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(OUT/'figure_provenance.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
