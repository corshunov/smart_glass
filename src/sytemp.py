import sycfg as c
import sydt
import syfiles

def log(temp, dt=None):
    if dt is None:
        dt = sydt.now()
    dt_str = sydt.get_str(dt)

    fpath = syfiles.get_log_path(dt)
    with fpath.open('a') as f:
        f.write(f"{dt_str},temp,{temp:.1f}\n")

def get():
    with syfiles.temp_source_fpath.open('r') as f:
        text = f.read()
        t_cpu = round(int(text) / 1000, 1)

    return t_cpu
