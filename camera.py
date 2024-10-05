from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np

window_name = "CameraStream"
timeout = 20 # milliseconds
fps = 20.0
video_length = 5 # seconds

reference_frame_base_fname = "reference_frame"
video_base_fname = "video"

file_ext = "jpg"
video_ext = "mp4"

data_dname = "data"
videos_dname = "videos"
reference_frames_dname = "reference_frames"

cwd = Path.cwd()
data_dpath = cwd / data_dname
videos_dpath = data_dpath / videos_dname
reference_frames_dpath = data_dpath / reference_frames_dname

fourcc = cv2.VideoWriter_fourcc(*'mp4v')

def prepare_folders():
    data_dpath.mkdir(exist_ok=True)
    videos_dpath.mkdir(exist_ok=True)
    reference_frames_dpath.mkdir(exist_ok=True)

def get_filename(base_fname, dt, ext):
    dt_str = dt.strftime("%Y%m%d_%H%M%S")
    return f"{base_fname}__{dt_str}.{ext}"

def list_cameras(n=10):
    l = []
    for i in range(n):
        vc = cv2.VideoCapture(i)
        if vc.isOpened():
            l.append(i)
        vc.release()

    return l

def get_camera(i=0):
    vc = cv2.VideoCapture(i)
    if vc.isOpened():
        vc.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        vc.set(cv2.CAP_PROP_EXPOSURE, 40)
        return vc
    
    raise Exception("Camera with index {i} was NOT found!")

def get_resolution(vc):
    w = int(vc.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return (w, h)

def get_reference_frame(vc):
    w, h = get_resolution(vc)
    default_frame = np.zeros((h, w, 3), dtype=np.uint8)
    
    existing_frames = sorted([i for i in reference_frames_dpath.iterdir() if i.suffix == f".{file_ext}"])
    if len(existing_frames) > 0:
        fpath = existing_frames[-1]
        frame = cv2.imread(fpath)

        if (frame.shape[0] != h) or (frame.shape[1] != w) or (frame.shape[2] != 3):
            frame = default_frame
    else:
        frame = default_frame

    return frame

def update_reference_frame(frame, dt):
    fpath = reference_frames_dpath / get_filename(reference_frame_base_fname, dt, file_ext)
    cv2.imwrite(fpath, frame)

def get_video_writer(vc, dt):
    w, h = get_resolution(vc)

    fpath = videos_dpath / get_filename(video_base_fname, dt, video_ext)
    return cv2.VideoWriter(fpath, fourcc, fps, (w, h))

def capture_video():
    break_flag = False
    update_reference_frame_flag = True
    record_video_flag = True
    video_out = None

    prepare_folders()

    vc = get_camera()
    reference_frame = get_reference_frame(vc)

    if record_video_flag:
        video_start_dt = datetime.now()
        video_end_dt = video_start_dt + timedelta(seconds=video_length)
        video_out = get_video_writer(vc, video_start_dt)

    while True:
        dt = datetime.now()
        
        flag, current_frame = vc.read()
        if not flag:
            continue

        if update_reference_frame_flag:
            reference_frame = current_frame
            update_reference_frame(reference_frame, dt)
            update_reference_frame_flag = False

        if record_video_flag:        
            if dt < video_end_dt:
                video_out.write(current_frame)
            else:
                video_out.release()
                video_out = None
                record_video_flag = False

        difference_frame = cv2.absdiff(reference_frame, current_frame)

        show_frame = cv2.hconcat([current_frame, reference_frame, difference_frame])
        #cv2.imshow(window_name, show_frame)
        
        #_ = cv2.waitKey(timeout)

        if break_flag:
            break

    #cv2.destroyWindow(window_name)
    #_ = cv2.waitKey(1)

    vc.release()

if __name__ == '__main__':
    try:
        capture_video()
    except KeyboardInterrupt:
        print('Exit')
