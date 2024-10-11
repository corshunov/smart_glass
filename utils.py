from pathlib import Path
import shutil

import cv2
import numpy as np
import serial

import config

ser = serial.Serial("/dev/ttyUSB0")
ser.baudrate = 115200

picture_ext = "jpg"

cwd = Path.cwd()

error_fpath = cwd / "error"

logs_dpath = cwd / "logs"

data_dpath = cwd / "data"
frames_dpath = data_dpath / "frames"
reference_frames_dpath = data_dpath / "reference_frames"
state_on_fpath = data_dpath / "state_on"
mode_manual_fpath = data_dpath / "mode_manual"
glass_state_on_fpath = data_dpath / "glass_state_on"
thresholds_fpath = data_dpath / "thresholds"

requests_dpath = cwd / "requests"
frame_requested_fpath = requests_dpath / "frame"
reference_frame_requested_fpath = requests_dpath / "reference_frame"
update_reference_frame_requested_fpath = requests_dpath / "update_reference_frame"
update_thresholds_requested_fpath = requests_dpath / "update_thresholds_frame"

temperature_fpath = Path(r"/sys/class/hwmon/hwmon0/temp1_input")

def remove_file(fpath):
    if fpath.is_file():
        fpath.unlink()

        while True:
            if not fpath.is_file():
                return True
    else:
        return False

def create_file(fpath):
    if not fpath.is_file():
        fpath.touch()

        while True:
            if fpath.is_file():
                break
            
def prepare_folders():
    remove_file(error_fpath)

    logs_dpath.mkdir(exist_ok=True)
    
    data_dpath.mkdir(exist_ok=True)
    frames_dpath.mkdir(exist_ok=True)
    reference_frames_dpath.mkdir(exist_ok=True)

    if not thresholds_fpath.is_file():
        save_thresholds(config.THR_L, config.THR_R)

    if requests_dpath.is_dir():
        shutil.rmtree(requests_dpath)
    requests_dpath.mkdir()

def get_filename(fname, dt, fext, dt_pattern="%Y%m%d_%H%M%S"):
    dt_str = dt.strftime(dt_pattern)
    return f"{fname}__{dt_str}.{fext}"

def get_log_fpath(dt):
    return logs_dpath / get_filename("log", dt, "csv")

def create_error_file(text):
    with error_fpath.open('w') as f:
        f.write(text)

def is_state_on():
    return state_on_fpath.is_file():

def set_state_on(state):
    if state:
        create_file(state_on_fpath)
    else:
        remove_file(state_on_fpath)

def is_mode_manual():
    return mode_manual_fpath.is_file():

def set_mode_manual(state):
    if state:
        create_file(state_on_fpath)
    else:
        remove_file(state_on_fpath)

def is_set_glass_state_on():
    return glass_state_on_fpath.is_file():

def set_glass_state_on(state):
    if state:
        create_file(glass_state_on_fpath)
    else:
        remove_file(glass_state_on_fpath)

def frame_requested():
    return remove_file(frame_requested_fpath)

def reference_frame_requested():
    return remove_file(reference_frame_requested_fpath)

def update_reference_frame_requested():
    return remove_file(update_reference_frame_requested_fpath)

def update_thresholds_requested():
    if update_thresholds_requested_fpath.is_file():
        with update_thresholds_requested_fpath.open('r') as f:
            text = f.read()

        remove_file(update_thresholds_requested_fpath)
        return True, parse_thresholds(text)
    else:
        return False, (None, None)

def get_last_reference_frame(vc):
    w, h = get_resolution(vc)
    default_frame = np.zeros((h, w, 3), dtype=np.uint8)
    
    reference_frames = sorted([i for i in reference_frames_dpath.iterdir() if i.suffix == f".{picture_ext}"])
    if len(reference_frames) > 0:
        fpath = reference_frames[-1]
        frame = cv2.imread(fpath)

        if (frame.shape[0] != h) or (frame.shape[1] != w) or (frame.shape[2] != 3):
            frame = default_frame
    else:
        frame = default_frame

    return frame

def parse_thresholds(text):
    thr_list = text.split(',')
    thr_l = int(thr_list[0].strip())
    thr_r = int(thr_list[1].strip())
    return (thr_l, thr_r)

def get_thresholds():
    with thresholds_fpath.open('r') as f:
        text = f.read()

    return parse_thresholds(text)

def save_frame(frame, dt):
    fpath = frames_dpath / get_filename("frame", dt, picture_ext)
    cv2.imwrite(fpath, frame)

def save_reference_frame(frame, dt, update=False):
    if update:
        dpath = reference_frames_dpath
    else:
        dpath = frames_dpath

    fpath = dpath / get_filename("reference_frame", dt, picture_ext)
    cv2.imwrite(fpath, frame)

def save_thresholds(thr_l, thr_r):
    with thresholds_fpath.open('w') as f:
        f.write(f"{thr_l},{thr_r}\n")

def set_glass_state(state):
    if state:
        ser.write(b'1')
    else:
        ser.write(b'0')

def get_temperature():
    with temperature_fpath.open('r') as f:
        text = f.read()
        t_cpu = round(int(text) / 1000, 1)

    return t_cpu
