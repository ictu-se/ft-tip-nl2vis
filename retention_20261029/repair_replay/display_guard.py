"""Preserve a usable typed display contract when accepting another chart.

Inputs are saved predictions and execution observations, never reference labels
or query-specific exceptions. A predicted contract can itself be semantically
wrong; this guard establishes only conditional contract preservation.
"""
import math
from datetime import datetime


def coordinate(value):
    try:
        number=float(value)
        if math.isfinite(number):return ('number',number)
    except (ValueError,TypeError):pass
    if isinstance(value,str) and len(value)>=10 and value[4:5]=='-' and value[7:8]=='-':
        try:return ('number',float(datetime.fromisoformat(value).year))
        except ValueError:pass
    return ('text',str(value).strip().casefold())


def contract_from(program):
    plan=program.get('temporal_plan');order=program.get('display_order')
    if program.get('execution_error') is not None or not isinstance(plan,dict) or not isinstance(order,dict):
        return None
    if plan.get('mark') not in ['bar','line']:
        return None
    axis,direction=order.get('axis'),order.get('direction')
    if (axis,direction)!=('none','none') and (axis not in ['year','value'] or direction not in ['asc','desc']):
        return None
    return dict(mark=plan['mark'],axis=axis,direction=direction)


def violations(observation,contract):
    if observation.get('status')!='captured_screen_order':return ['not_a_captured_chart']
    traces=observation.get('traces',[])
    if len(traces)!=1:return ['not_one_observed_trace']
    trace=traces[0];points=trace.get('screen_order',[])
    if not points:return ['no_observed_points']
    errors=[]
    if observation.get('visibility_issues'):errors.append('selected_visibility_issue')
    if trace.get('mark')!=contract['mark']:errors.append('declared_mark_violation')
    try:
        ys=[float(point[1]) for point in points]
        if not all(math.isfinite(y) for y in ys):return errors+['nonfinite_numeric_value']
        if contract['axis']!='none':
            values=ys if contract['axis']=='value' else [coordinate(point[0]) for point in points]
            ordered=all(a<=b if contract['direction']=='asc' else a>=b for a,b in zip(values,values[1:]))
            if not ordered:errors.append('declared_spatial_order_violation')
    except (TypeError,ValueError,IndexError):
        errors.append('uninterpretable_observation')
    return errors


def choose(candidates,selected_index):
    """Candidate0 is the preceding typed planner; candidate1 is nvAgent.

    Preserve an abstention or typed selection. Override a native selection only
    when both alternatives are captured charts, the typed chart satisfies its
    own declared mark/order/visibility contract, and the native chart violates
    it. Artist construction order and model rationale are never consulted.
    """
    if len(candidates)!=2 or selected_index not in [None,0,1]:raise ValueError('invalid_candidate_selection')
    result=dict(selected_index=selected_index,overridden=False,contract=None,violations=[],reason='selection_preserved')
    if selected_index!=1:return result
    typed,native=candidates
    contract=contract_from(typed['program'])
    if contract is None:return dict(result,reason='no_usable_typed_contract')
    result['contract']=contract
    if violations(typed['observed_output'],contract):return dict(result,reason='typed_output_does_not_satisfy_its_contract')
    # A support decline is not converted into a chart by this display guard.
    if native['observed_output'].get('status')!='captured_screen_order':return dict(result,reason='selected_nonchart_preserved')
    problems=violations(native['observed_output'],contract)
    if not problems:return dict(result,reason='selected_chart_satisfies_typed_display_contract')
    return dict(result,selected_index=0,overridden=True,violations=problems,reason='typed_display_contract_fallback')
