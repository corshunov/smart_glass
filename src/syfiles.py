from pathlib import Path
import shutil
import sys

import sydt

root_dpath = Path(__file__).parent.parent
data_dpath = root_dpath / "data"
logs_dpath = data_dpath / "logs"
state_dpath = data_dpath / "state"
frames_dpath = data_dpath / "frames"
requests_dpath = data_dpath / "requests"
system_requests_dpath / requests_dpath / "system"
bot_requests_dpath / requests_dpath / "bot"

error_fpath = root_dpath / "error"

systate_on_fpath = state_dpath / "systate_on"
mode_manual_fpath = state_dpath / "mode_manual"
glstate_transparent_fpath = state_dpath / "glstate_transparent"
thresholds_fpath = state_dpath / "thresholds"
reference_frame_fpath = state_dpath / f"reference_frame.{PICTURE_EXT}"

update_systate_on_fpath = system_requests_dpath / "update_systate_on"
update_systate_off_fpath = system_requests_dpath / "update_systate_off"

update_mode_manual_fpath = system_requests_dpath / "update_mode_manual"
update_mode_auto_fpath = system_requests_dpath / "update_mode_auto"

update_glstate_transparent_fpath = system_requests_dpath / "update_glstate_transparent"
update_glstate_opaque_fpath = system_requests_dpath / "update_glstate_opaque"

request_frame_fpath = system_requests_dpath / "request_frame"
update_reference_frame_fpath = system_requests_dpath / "update_reference_frame"

update_thresholds_fpath = system_requests_dpath / "update_thresholds"

request_reference_frame_fpath = bot_requests_dpath / "request_reference_frame"

temp_source_fpath = Path("/sys/class/hwmon/hwmon0/temp1_input")

def reconfigure_stdout():
    sys.stdout.reconfigure(line_buffering=True)

def output_error(text):
    with error_fpath.open('w') as f:
        f.write(text)

def get_filename(name, dt, ext, pattern="%Y%m%d_%H%M%S"):
    dt_str = sydt.get_str(dt)
    return f"{fname}__{dt_str}.{fext}"

def get_log_path(dt):
    return logs_dpath / get_filename("log", dt, "csv", "%Y%m%d")

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

def prepare_folders(clean=True):
    if clean:
        remove_file(error_fpath)

        if requests_dpath.is_dir():
            shutil.rmtree(requests_dpath)

    data_dpath.mkdir(exist_ok=True)
    logs_dpath.mkdir(exist_ok=True)
    state_dpath.mkdir(exist_ok=True)
    frames_dpath.mkdir(exist_ok=True)
    requests_dpath.mkdir(exist_ok=True)
    system_requests_dpath.mkdir(exist_ok=True)
    bot_requests_dpath.mkdir(exist_ok=True)
