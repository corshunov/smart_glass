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
