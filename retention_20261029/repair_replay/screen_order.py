import math

def finite(x):
    if type(x) not in [int, float] or not math.isfinite(x):
        raise ValueError('nonfinite_display_position')
    return x

def ordered(points, positions, top_down=False):
    if len(points) != len(positions):
        raise ValueError('position_count_mismatch')
    for value in positions:
        finite(value)
    # Do not invent a visual order where marks have the same screen position.
    if len(set(round(x, 9) for x in positions)) != len(positions):
        raise ValueError('overlapping_positions_require_separate_semantics')
    indices = sorted(range(len(points)), key=lambda i: positions[i], reverse=top_down)
    return [points[i] for i in indices]

def vega(captured, spec):
    if captured['status'] != 'captured':
        return {'status': captured['status'], 'traces': []}
    if any(k in spec for k in ['layer', 'facet', 'repeat', 'concat', 'hconcat', 'vconcat']):
        return {'status': 'unscorable', 'reason': 'composed_spec', 'traces': []}
    traces = []; issues = []
    try:
        if spec['encoding']['y']['type'] != 'quantitative':
            raise ValueError('only_vertical_unit_bar_line_supported')
        for mark in captured['marks']:
            if mark['type'] not in ['line', 'rect']:
                raise ValueError('unsupported_mark_type')
            grouped = {}
            for item in mark['items']:
                g, channels = item['geometry'], item['channels']
                if g.get('defined') is False:
                    raise ValueError('undefined_mark_requires_gap_semantics')
                x = channels['x']['value']; value = channels['y']['value']
                if mark['type'] == 'rect':
                    value -= channels['y2']['value']
                finite(value)
                color = channels['stroke' if mark['type'] == 'line' else 'fill']
                label = color['value'] if color['kind'] == 'field' else None
                grouped.setdefault(label, []).append(([x, value], finite(g['x'])))
                if g.get('opacity', 1) == 0 or g.get('strokeOpacity' if mark['type'] == 'line' else 'fillOpacity', 1) == 0:
                    issues.append({'label': label, 'issue': 'transparent_mark'})
            for label, values in grouped.items():
                points = [x[0] for x in values]
                if mark['type'] == 'line' and len(points) == 1:
                    # Symbol layers are unsupported above, so a sole line item
                    # has no separate marker in this strict unit-chart capture.
                    issues.append({'label': label, 'issue': 'singleton_without_marker'})
                traces.append({'mark': 'line' if mark['type'] == 'line' else 'bar', 'label': label,
                               'path_order': points, 'screen_order': ordered(points, [x[1] for x in values]),
                               'direction': 'left_to_right'})
        return {'status': 'captured_screen_order', 'traces': traces, 'visibility_issues': issues,
                'full_chart_correct': None}
    except (ValueError, KeyError, TypeError) as exc:
        return {'status': 'unscorable', 'reason': str(exc), 'traces': [], 'full_chart_correct': None}
