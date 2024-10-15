from datetime import datetime
from pathlib import Path
import shutil
import sys

import sycfg as c
import sydt

root_dpath = Path(__file__).parent.parent
data_dpath = root_dpath / "data"
logs_dpath = data_dpath / "logs"
state_dpath = data_dpath / "state"
frames_dpath = data_dpath / "frames"
requests_dpath = data_dpath / "requests"
system_requests_dpath = requests_dpath / "system"
bot_requests_dpath = requests_dpath / "bot"

light_on_fpath = state_dpath / "light_on"
state_on_fpath = state_dpath / "on"
mode_manual_fpath = state_dpath / "manual"
glstate_on_fpath = state_dpath / "glon"
reference_frame_fpath = state_dpath / f"reference_frame.{c.PICTURE_EXT}"
black_frame_fpath = state_dpath / f"black_frame.{c.PICTURE_EXT}"
thresholds_fpath = state_dpath / "thresholds"

set_state_on_fpath = system_requests_dpath / "on"
set_state_off_fpath = system_requests_dpath / "off"

set_mode_manual_fpath = system_requests_dpath / "manual"
set_mode_auto_fpath = system_requests_dpath / "auto"

set_glstate_on_fpath = system_requests_dpath / "glon"
set_glstate_off_fpath = system_requests_dpath / "gloff"

save_frame_fpath = system_requests_dpath / "frame"
update_save_reference_frame_fpath = system_requests_dpath / "updateref"

update_thresholds_fpath = system_requests_dpath / "updatethr"

temp_source_fpath = Path("/sys/class/hwmon/hwmon0/temp1_input")

def reconfigure_stdout():
    sys.stdout.reconfigure(line_buffering=True)

def wait_until_file(fpath, present):
    if present:
        while True:
            if fpath.is_file():
                break
    else:
        while True:
            if not fpath.is_file():
                break

def remove_file(fpath):
    if fpath.is_file():
        fpath.unlink()
        wait_until_file(fpath, present=False)
        return True
    else:
        return False

def create_file(fpath):
    if not fpath.is_file():
        fpath.touch()
        wait_until_file(fpath, present=True)

def move_file(fpath_old, fpath_new):
    remove_file(fpath_new)
    fpath_old.rename(fpath_new)
    wait_until_file(fpath_new, present=True)

def prepare_folders(clean=True):
    if clean:
        if requests_dpath.is_dir():
            shutil.rmtree(requests_dpath)

    data_dpath.mkdir(exist_ok=True)
    logs_dpath.mkdir(exist_ok=True)
    state_dpath.mkdir(exist_ok=True)
    frames_dpath.mkdir(exist_ok=True)
    requests_dpath.mkdir(exist_ok=True)
    system_requests_dpath.mkdir(exist_ok=True)
    bot_requests_dpath.mkdir(exist_ok=True)

def get_frame_path(metadata):
    dt, level_l, level_r, thr_l, thr_r, reason = metadata
    dt_str = sydt.get_str(dt, "%Y%m%d_%H%M%S")
    name = f"frame__{dt_str}__{level_l}_{level_r}__{thr_l}_{thr_r}__{reason}-.{c.PICTURE_EXT}"
    return frames_dpath / name

def get_log_path(dt):
    dt_str = sydt.get_str(dt, pattern="%Y%m%d")
    name = f"log__{dt_str}.csv"
    return logs_dpath / name

def path2metadata(fpath):
    name = fpath.name
    l = name.split('__')

    dt_str = l[1]
    dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")

    levels = l[2]
    levels_l = levels.split('_')
    level_l = int(levels_l[0])
    level_r = int(levels_l[1])

    thresholds = l[3]
    thresholds_l = thresholds.split('_')
    thr_l = int(thresholds_l[0])
    thr_r = int(thresholds_l[1])

    last_part = l[4]
    reason = last_part.split('-')[0]

    return dt, level_l, level_r, thr_l, thr_r, reason
