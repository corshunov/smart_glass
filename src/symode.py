import sycfg as c
import sydt
import syfiles

MANUAL = "MANUAL"
AUTO = "AUTO"

def log(mode, dt=None):
    if dt is None:
        dt = sydt.now()
    dt_str = sydt.get_str(dt)

    fpath = syfiles.get_log_path(dt)
    with fpath.open('a') as f:
        f.write(f"{dt_str},mode,{mode}\n")

def get_mode():
    if syfiles.mode_manual_fpath.is_file():
        return MANUAL
    else:
        return AUTO

def set_mode(mode):
    if mode == MANUAL:
        create_file(syfiles.mode_manual_fpath)
    elif mode == AUTO:
        remove_file(syfiles.mode_manual_fpath)
    else:
        raise Exception("Invalid 'mode' argument.")
