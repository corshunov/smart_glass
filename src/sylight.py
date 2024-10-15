import sycfg as c
import sydt
import syfiles

ON = "ON"
OFF = "OFF"

def log(state, dt=None):
    if dt is None:
        dt = sydt.now()
    dt_str = sydt.get_str(dt)

    fpath = syfiles.get_log_path(dt)
    with fpath.open('a') as f:
        f.write(f"{dt_str},light,{state}\n")

def get():
    if syfiles.light_on_fpath.is_file():
        return ON
    else:
        return OFF

def set(state):
    if state == ON:
        syfiles.create_file(syfiles.light_on_fpath)
    elif state == OFF:
        syfiles.remove_file(syfiles.light_on_fpath)
    else:
        raise Exception("Invalid 'state' argument.")

    log(state)
