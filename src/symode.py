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

def get():
    if syfiles.mode_manual_fpath.is_file():
        return MANUAL
    else:
        return AUTO

def set(mode):
    if mode == MANUAL:
        syfiles.create_file(syfiles.mode_manual_fpath)
    elif mode == AUTO:
        syfiles.remove_file(syfiles.mode_manual_fpath)
    else:
        raise Exception("Invalid 'mode' argument.")

def set_present():
    if syfiles.set_mode_manual_fpath.is_file():
        syfiles.remove_file(syfiles.set_mode_manual_fpath)
        syfiles.remove_file(syfiles.set_mode_auto_fpath) # in case it is also present
        return True, MANUAL
    elif syfiles.set_mode_auto_fpath.is_file():
        syfiles.remove_file(syfiles.set_mode_auto_fpath)
        return True, AUTO

    return False, None

def set_request(state):
    if state == MANUAL:
        syfiles.create_file(syfiles.set_mode_manual_fpath)
    elif state == AUTO:
        syfiles.create_file(syfiles.set_mode_auto_fpath)
    else:
        raise Exception("Invalid 'state' argument.")
