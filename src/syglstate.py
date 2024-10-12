import serial

import sycfg as c
import sydt
import syfiles

ser = serial.Serial(c.SERIAL_DEVICE)
ser.baudrate = 115200

TRANSPARENT = "TRANSPARENT"
OPAQUE = "OPAQUE"

def log(state, dt=None):
    if dt is None:
        dt = sydt.now()
    dt_str = sydt.get_str(dt)

    fpath = syfiles.get_log_path(dt)
    with fpath.open('a') as f:
        f.write(f"{dt_str},glstate,{state}\n")

def get():
    if syfiles.glstate_transparent_fpath.is_file():
        return TRANSPARENT
    else:
        return OPAQUE

def set(state):
    if state == TRANSPARENT:
        ser.write(b'1')
        syfiles.create_file(syfiles.glstate_transparent_fpath)
    elif state == OPAQUE:
        ser.write(b'0')
        syfiles.remove_file(syfiles.glstate_transparent_fpath)
    else:
        raise Exception("Invalid 'glstate' argument.")

def set_present():
    if syfiles.set_glstate_transparent_fpath.is_file():
        syfiles.remove_file(syfiles.set_glstate_transparent_fpath)
        syfiles.remove_file(syfiles.set_glstate_opaque_fpath) # in case it is also present
        return True, TRANSPARENT
    elif syfiles.set_systate_off_fpath.is_file():
        syfiles.remove_file(syfiles.set_glstate_opaque_fpath)
        return True, OPAQUE

    return False, None

def set_request(state):
    if state == TRANSPARENT:
        syfiles.create_file(syfiles.set_glstate_transparent_fpath)
    elif state == OPAQUE:
        syfiles.create_file(syfiles.set_glstate_opaque_fpath)
    else:
        raise Exception("Invalid 'state' argument.")
