from pathlib import Path
import shutil

import cv2
import serial

import config

ser = serial.Serial("/dev/ttyUSB0")
ser.baudrate = 115200

root_dpath = Path(__file__).parent.parent

error_fpath = root_dpath / "error"

logs_dpath = root_dpath / "logs"

data_dpath = root_dpath / "data"
frames_dpath = data_dpath / "frames"
reference_frames_dpath = data_dpath / "reference_frames"
state_on_fpath = data_dpath / "state_on"
mode_manual_fpath = data_dpath / "mode_manual"
glass_state_transparent_fpath = data_dpath / "glass_state_transparent"
thresholds_fpath = data_dpath / "thresholds"

requests_dpath = root_dpath / "requests"
frame_request_fpath = requests_dpath / "frame"
reference_frame_request_fpath = requests_dpath / "ref"
update_reference_frame_request_fpath = requests_dpath / "updateref"
update_thresholds_request_fpath = requests_dpath / "updatethr"
update_thresholds_request_done_fpath = \
    update_thresholds_request_fpath.parent / f"done.{update_thresholds_request_fpath.name}"

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

def move_file(fpath_old, fpath_new):
    remove_file(fpath_new)

    fpath_old.rename(fpath_new)

    while True:
        if fpath_new.is_file():
            break

def prepare_folders(clean=True):
    if clean:
        remove_file(error_fpath)

        if requests_dpath.is_dir():
            shutil.rmtree(requests_dpath)

    logs_dpath.mkdir(exist_ok=True)
    
    data_dpath.mkdir(exist_ok=True)
    frames_dpath.mkdir(exist_ok=True)
    reference_frames_dpath.mkdir(exist_ok=True)

    if not thresholds_fpath.is_file():
        save_thresholds(config.THR_L, config.THR_R)

    requests_dpath.mkdir(exist_ok=True)

def get_nice_dt_str_from_fpath(fpath):
    dt_str = fpath.with_suffix('').name.split('__')[-1]
    dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
    return dt.strftime("%d.%m.%Y at %H:%M:%S")

def get_filename(fname, dt, fext, dt_pattern="%Y%m%d_%H%M%S"):
    dt_str = dt.strftime(dt_pattern)
    return f"{fname}__{dt_str}.{fext}"

def get_log_fpath(dt):
    return logs_dpath / get_filename("log", dt, "csv", dt_pattern="%Y%m%d")

def get_temperature():
    with temperature_fpath.open('r') as f:
        text = f.read()
        t_cpu = round(int(text) / 1000, 1)

    return t_cpu

def log_temperature(dt):
    dt_str = dt.strftime('%Y%m%dT%H%M%S.%f')

    t_cpu = get_temperature()

    fpath = logs_dpath / get_filename("temp_log", dt, "csv", dt_pattern="%Y%m%d")
    with fpath.open('a') as f:
        f.write(f"{dt_str},{t_cpu:.1f}\n")

def create_error_file(text):
    with error_fpath.open('w') as f:
        f.write(text)

def get_state():
    if state_on_fpath.is_file():
        return "ON"
    else:
        return "OFF"

def set_state(state):
    if state == "ON":
        create_file(state_on_fpath)
    elif state == "OFF":
        remove_file(state_on_fpath)

def get_mode():
    if mode_manual_fpath.is_file():
        return "MANUAL"
    else:
        return "AUTO"

def set_mode(mode):
    if mode == "MANUAL":
        create_file(mode_manual_fpath)
    elif mode == "AUTO":
        remove_file(mode_manual_fpath)

def get_glass_state():
    if glass_state_transparent_fpath.is_file():
        return "TRANSPARENT"
    else:
        return "OPAQUE"

def set_glass_state(state):
    if state == "TRANSPARENT":
        ser.write(b'1')
        create_file(glass_state_transparent_fpath)
    elif state == "OPAQUE":
        ser.write(b'0')
        remove_file(glass_state_transparent_fpath)

def frame_requested():
    return remove_file(frame_request_fpath)

def request_frame():
    create_file(frame_request_fpath)

def reference_frame_requested():
    return remove_file(reference_frame_request_fpath)

def request_reference_frame():
    create_file(reference_frame_request_fpath)

def update_reference_frame_requested():
    return remove_file(update_reference_frame_request_fpath)

def request_update_reference_frame():
    create_file(update_reference_frame_request_fpath)

def parse_thresholds(text):
    try:
        thr_list = text.split(',')
        thr_l = int(thr_list[0].strip())
        thr_r = int(thr_list[1].strip())
        return True, (thr_l, thr_r)
    except:
        return False, (None, None)

def update_thresholds_requested():
    if update_thresholds_request_fpath.is_file():
        with update_thresholds_request_fpath.open('r') as f:
            text = f.read()

        move_file(update_thresholds_request_fpath,
                  update_thresholds_request_done_fpath)
        flag, (thr_l, thr_r) = parse_thresholds(text)
        if flag:
            return True, (thr_l, thr_r)

    return False, (None, None)

def get_thresholds():
    with thresholds_fpath.open('r') as f:
        text = f.read()

    return parse_thresholds(text)

def save_frame(frame, dt, reason):
    if reason == "REQUEST":
        fname = "frame_request"
    elif reason == "REFERENCE_REQUEST":
        fname = "frame_reference_request"
    elif reason == "REFERENCE_UPDATE":
        fname = "frame_reference_update"
    elif reason == "GLASS_TRANSPARENT":
        fname = "frame_glass_transparent"
    elif reason == "GLASS_OPAQUE":
        fname = "frame_glass_opaque"
    else:
        raise Exception("Invalid reason")

    fpath = frames_dpath / get_filename(fname, dt, config.PICTURE_EXT)
    cv2.imwrite(fpath, frame)

def save_reference_frame(frame, dt):
    fpath = reference_frames_dpath / get_filename("frame_reference", dt, config.PICTURE_EXT)
    cv2.imwrite(fpath, frame)

def save_thresholds(thr_l, thr_r):
    with thresholds_fpath.open('w') as f:
        f.write(f"{thr_l},{thr_r}\n")
