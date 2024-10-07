from pathlib import Path

import cv2
import numpy as np


ref_frame_fname = "ref_frame"
video_fname = "video"

frame_fext = "jpg"
video_fext = "mp4"

cwd = Path.cwd()
data_dpath = cwd / "data"
ref_frames_dpath = data_dpath / "ref_frames"
videos_dpath = data_dpath / "videos"
requests_dpath = data_dpath / "requests"

update_ref_frame_fpath = requests_dpath / "update_ref"
recording_fpath = requests_dpath / "record"

recording_video_fpath = videos_dpath / f"recording.{video_fext}"

manual_mode_fpath = data_dpath / "manual_mode"
manual_state_on_fpath = data_dpath / "manual_state_on"

log_fpath = data_dpath / "log"
error_fpath = data_dpath / "error"

fourcc = cv2.VideoWriter_fourcc(*'mp4v')

def get_filename(fname, dt, fext):
    dt_str = dt.strftime("%Y%m%d_%H%M%S")
    return f"{fname}__{dt_str}.{fext}"

def remove_file(fpath):
    fpath.unlink(missing_ok=True)

    while True:
        if not fpath.is_file():
            break

def prepare_folders():
    data_dpath.mkdir(exist_ok=True)
    videos_dpath.mkdir(exist_ok=True)
    ref_frames_dpath.mkdir(exist_ok=True)

    requests_dpath.mkdir(exist_ok=True)
    remove_file(update_ref_frame_fpath)
    remove_file(recording_fpath)
    remove_file(error_fpath)

def get_resolution(vc):
    w = int(vc.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return (w, h)

def update_ref_frame_requested():
    if update_ref_frame_fpath.is_file():
        remove_file(update_ref_frame_fpath)
        return True

    return False

def recording_requested():
    if recording_fpath.is_file():
        remove_file(recording_fpath)
        return True
    
    return False

def request_recording():
    if recording_video_fpath.is_file():
        return

    recording_fpath.touch()

def both_steps_filled(frame, prev_frame, ref_frame):
    #difference_frame = cv2.absdiff(reference_frame, current_frame)
    return False

def get_ref_frame(vc):
    w, h = get_resolution(vc)
    default_frame = np.zeros((h, w, 3), dtype=np.uint8)
    
    existing_frames = sorted([i for i in ref_frames_dpath.iterdir() if i.suffix == f".{frame_fext}"])
    if len(existing_frames) > 0:
        fpath = existing_frames[-1]
        frame = cv2.imread(fpath)

        if (frame.shape[0] != h) or (frame.shape[1] != w) or (frame.shape[2] != 3):
            frame = default_frame
    else:
        frame = default_frame

    return frame

def save_ref_frame(frame, dt):
    print(frame.shape)
    fpath = ref_frames_dpath / get_filename(ref_frame_fname, dt, frame_fext)
    cv2.imwrite(fpath, frame)

def get_video_fpath(dt):
    return videos_dpath / get_filename(video_fname, dt, video_fext)

def get_video_writer(vc):
    w, h = get_resolution(vc)
    fps = vc.get(cv2.CAP_PROP_FPS)
    return cv2.VideoWriter(recording_video_fpath, fourcc, fps, (w, h))

def save_video(video_writer, fpath):
    video_writer.release()
    recording_video_fpath.rename(fpath)

def manual_mode_enabled():
    if manual_mode_fpath.is_file():
        return True

    return False

def manual_state_on():
    if manual_state_on_fpath.is_file():
        return True

    return False

def create_error_file(text):
    with error_fpath.open('w') as f:
        f.write(text)

def set_glass_transparent(ser, flag):
    if flag:
        cmd = "1"
    else:
        cmd = "0"

    #ser.write(cmd.encode())
