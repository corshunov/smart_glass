import sycfg as c
import sydt
import syfiles

def parse(text):
    l = text.split(',')
    thr_l = int(l[0].strip())
    thr_r = int(l[1].strip())
    return thr_l, thr_r

def log(thr_l, thr_r, dt=None):
    if dt is None:
        dt = sydt.now()
    dt_str = sydt.get_str(dt)

    fpath = syfiles.get_log_path(dt)
    with fpath.open('a') as f:
        f.write(f"{dt_str},thresholds,{thr_l}-{thr_r}\n")

def save(thr_l, thr_r):
    with syfiles.thresholds_fpath.open('w') as f:
        f.write(f"{thr_l},{thr_r}\n")
    syfiles.wait_until_file(syfiles.thresholds_fpath, present=True)
    syfiles.create_file(syfiles.update_thresholds_fpath)
    log(thr_l, thr_r)

def get():
    if syfiles.thresholds_fpath.is_file():
        try:
            thr_l, thr_r = parse(text)
            return thr_l, thr_r
        except:
            pass

    save(c.THR_L, c.THR_R)
    return c.THR_L, c.THR_R

def update_thresholds_present():
    if syfiles.update_thresholds_fpath.is_file():
        with syfiles.update_thresholds_fpath.open('r') as f:
            text = f.read()
        
        syfiles.remove_file(syfiles.update_thresholds_fpath)

        try:
            thr_l, thr_r = parse(text)
            return True, (thr_l, thr_r)
        except:
            pass

    return False, (None, None)

def update_thresholds(thr_l, thr_r):
    with syfiles.update_thresholds_fpath.open('w') as f:
        f.write(f"{thr_l},{thr_r}")
    syfiles.wait_until_file(syfiles.update_thresholds_fpath, present=True)

