"""Gold-blind data extraction from the runtime that exports the saved SVG.

Prospective unit bar/line adapter. Does not score appearance, clipping, labels,
or refusal quality. Unknown representations stay unscorable, not discarded.
"""
import json
import math
import os
from pathlib import Path
import subprocess
import shutil
from datetime import datetime
import vl_convert as vlc

ROOT=Path(__file__).resolve().parent
NODE=os.environ.get('P09_NODE') or shutil.which('node')
if not NODE: raise RuntimeError('Node.js is required; set P09_NODE or add node to PATH')


def finite(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError('nonfinite_or_nonnumeric_value')
    return value


def field(channel):
    if channel['kind'] not in ['field','constant'] or 'value' not in channel:
        raise ValueError('unresolved_compiled_encoding')
    return channel['value']


def extract(capture,spec):
    if capture['status']!='captured':
        return {'status':'execution_error','traces':[], 'reason':capture.get('error')}
    try:
        if any(k in spec for k in ['layer','facet','repeat','concat','hconcat','vconcat']):
            raise ValueError('unsupported_composed_spec')
        encoding=spec['encoding'];x_type=encoding['x']['type']
        if isinstance(spec.get('mark'),dict) and spec['mark'].get('orient')=='horizontal':
            raise ValueError('unsupported_horizontal_bar')
        if encoding['y']['type']!='quantitative':
            raise ValueError('unsupported_nonquantitative_y')
        if any('bin' in encoding.get(k,{}) for k in ['x','y']):
            raise ValueError('unsupported_numeric_bins')
        def x_value(item):
            value=field(item['channels']['x'])
            if x_type=='temporal':
                if encoding['x'].get('timeUnit') not in ['year','utcyear']:
                    raise ValueError('unsupported_temporal_unit')
                if not isinstance(value,str):
                    raise ValueError('unresolved_temporal_value')
                return datetime.fromisoformat(value.replace('Z','+00:00')).year
            if x_type not in ['nominal','ordinal','quantitative'] or value is None or isinstance(value,(dict,list)):
                raise ValueError('unsupported_x_coordinate')
            return value
        traces=[]
        for mark in capture['marks']:
            if mark['type'] not in ['line','rect']:
                raise ValueError('unsupported_mark_type')
            items=mark['items']
            if not items:raise ValueError('empty_trace')
            if mark['type']=='rect':
                stacks={}
                for item in items:
                    c=item['channels']
                    base=finite(field(c['y2']));end=finite(field(c['y']))
                    position=finite(item['geometry'].get('x'))
                    stacks.setdefault((round(position,9),end-base>=0),[]).append((base,end))
                for segments in stacks.values():
                    expected=0
                    for base,end in sorted(segments,key=lambda pair:abs(pair[0])):
                        # Zero-based independent bars and contiguous stacked bars
                        # match the existing matplotlib observation contract.
                        if not math.isclose(base,0,abs_tol=1e-7) and not math.isclose(base,expected,rel_tol=1e-7,abs_tol=1e-7):
                            raise ValueError('floating_bar_without_verifiable_stack')
                        expected=end
            groups={}
            for item in items:
                if item['geometry'].get('defined') is False:
                    continue
                c=item['channels']
                color=c['stroke' if mark['type']=='line' else 'fill']
                name=None
                if color['kind']=='field' and color['field']!=c['x'].get('field'):
                    name=str(field(color))
                y=finite(field(c['y']))
                if mark['type']=='rect':
                    y-=finite(field(c['y2']))
                groups.setdefault(name,[]).append((x_value(item),y,item['geometry'].get('x')))
            if mark['type']=='line' and len(groups)>1:
                raise ValueError('connected_line_with_mixed_groups')
            for name,points in groups.items():
                if mark['type']=='rect':
                    for _,_,position in points:finite(position)
                    points.sort(key=lambda p:p[2])
                traces.append({'figure':0,'axis':0,'mark':'line' if mark['type']=='line' else 'bar',
                    'label':name,'points':[[x,y] for x,y,_ in points]})
        if not traces:raise ValueError('empty_chart_or_trace')
        return {'status':'observed','traces':traces}
    except (ValueError,KeyError,TypeError) as exc:
        return {'status':'unscorable','reason':str(exc),'traces':[]}


def capture(spec,destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    (destination/'input.vl.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
    try:
        compiled=vlc.vegalite_to_vega(spec,vl_version='5.16')
        (destination/'compiled.vg.json').write_text(json.dumps(compiled,ensure_ascii=False,indent=2)+'\n')
    except Exception as exc:
        result={'status':'execution_error','error':'compile: '+str(exc)}
    else:
        run=subprocess.run([NODE,str(ROOT/'vega_runtime/capture.mjs')],input=json.dumps(compiled),
            text=True,capture_output=True,timeout=45,env={**os.environ,'TZ':'UTC'})
        # Missing JSON or process failure outside the defined renderer error
        # envelope is infrastructure failure, never an ordinary model score.
        result=json.loads(run.stdout)
        if run.returncode not in [0,1] or run.stderr:
            raise RuntimeError('capture_worker_protocol_failure: '+run.stderr)
        if result['status']=='captured':
            assert run.returncode==0
            (destination/'chart.svg').write_text(result.pop('svg'))
        else:
            assert run.returncode==1 and result['status']=='execution_error'
    result['observation']=extract(result,spec)
    (destination/'capture.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
