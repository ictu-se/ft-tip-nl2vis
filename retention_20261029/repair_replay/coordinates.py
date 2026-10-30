import math
from datetime import datetime

def canonical_x(x):
    # Numeric year strings and numeric coordinates denote the same year.
    try:
        n=float(x)
        if math.isfinite(n):return ('number',n)
    except (TypeError,ValueError):pass
    if isinstance(x,str) and len(x)>=10 and x[4:5]=='-' and x[7:8]=='-':
        try:return ('number',float(datetime.fromisoformat(x).year))
        except ValueError:pass
    return ('text',str(x).strip().casefold())
