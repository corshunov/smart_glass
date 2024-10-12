import time
from datetime import datetime
from pytz import timezone

import sycgf as c

TZ = timezone(c.TZ)

def sleep(seconds):
    time.sleep(seconds)

def now():
    return datetime.now(TZ)

def get_str(dt=None, pattern='%Y%m%dT%H%M%S.%f'):
    if dt is None:
        dt = dtnow()

    return dt.strftime(pattern)

#def fname2get_nice_dt_str_from_fpath(fpath):
#    dt_str = fpath.with_suffix('').name.split('__')[-1]
#    dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
#    return dt.strftime("%d.%m.%Y at %H:%M:%S")
