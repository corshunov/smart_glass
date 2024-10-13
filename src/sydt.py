import time
from datetime import datetime
from pytz import timezone

import sycfg as c

TZ = timezone(c.TZ)

def sleep(seconds):
    time.sleep(seconds)

def now():
    return datetime.now(TZ)

def get_str(dt=None, pattern='%Y%m%dT%H%M%S.%f'):
    if dt is None:
        dt = now()

    if pattern == "nice":
        pattern = "%d.%m.%Y at %H:%M:%S"

    return dt.strftime(pattern)

def path2str(fpath):
    dt_str = fpath.with_suffix('').with_suffix('').name.split('__')[-1]
    dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
    dt_str = get_str(dt, pattern='nice')
    return dt_str
