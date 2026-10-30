"""Original repair functions, extracted without algorithm changes. No reference scoring."""
import collections, math
import display_guard
import coordinates as metric

def relation(observation):
    traces=observation.get('traces',[])
    if observation.get('status')!='captured_screen_order' or len(traces)!=1:raise ValueError('not_single_trace')
    return collections.Counter((metric.canonical_x(x),float(y)) for x,y in traces[0]['screen_order'])

def specification(candidates,selection):
    decision=display_guard.choose(candidates,selection)
    if not decision['overridden'] or decision['violations']!=['declared_spatial_order_violation']:return None
    observed=candidates[1]['observed_output'];trace=observed['traces'][0];contract=decision['contract']
    if trace['mark']!='bar' or contract['mark']!='bar' or observed.get('visibility_issues'):return None
    points=trace['screen_order'];keys=[metric.canonical_x(x) for x,y in points]
    if any(k[0]!='number' or not float(k[1]).is_integer() for k in keys) or len(set(keys))!=len(keys):return None
    if not all(math.isfinite(float(y)) for x,y in points):return None
    ordered=sorted(points,key=lambda p:metric.canonical_x(p[0])[1] if contract['axis']=='year' else float(p[1]),reverse=contract['direction']=='desc')
    labels=[str(int(metric.canonical_x(x)[1])) for x,y in ordered]
    return {'$schema':'https://vega.github.io/schema/vega-lite/v5.json','width':600,'height':310,
        'data':{'values':[{'year':label,'value':float(p[1])} for label,p in zip(labels,ordered)]},
        'mark':{'type':'bar','color':'#4c78a8'},
        'encoding':{'x':{'field':'year','type':'ordinal','sort':labels,'title':'Year (ordered categories)'},
                    'y':{'field':'value','type':'quantitative','title':'Plotted value'}},
        'config':{'axis':{'labelFontSize':12,'titleFontSize':13},'view':{'stroke':None}}}
