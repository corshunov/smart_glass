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
        f.write(f"{dt_str},systate,{state}\n")

def get():
    if syfiles.systate_on_fpath.is_file():
        return ON
    else:
        return OFF

def set(state):
    if state == ON:
        create_file(syfiles.systate_on_fpath)
    elif state == OFF:
        remove_file(syfiles.systate_on_fpath)
    else:
        raise Exception("Invalid 'systate' argument.")

    log(state)
