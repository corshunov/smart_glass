from datetime import datetime
from pathlib import Path

import numpy as np
import cv2

import config
import utils

def get_camera(i=0):
    vc = cv2.VideoCapture(i)
    vc.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
    vc.set(cv2.CAP_PROP_FRAME_WIDTH, config.REAL_W)
    vc.set(cv2.CAP_PROP_FRAME_HEIGHT, config.REAL_H)
    vc.set(cv2.CAP_PROP_FPS, config.FPS)
    vc.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    vc.set(cv2.CAP_PROP_EXPOSURE, config.EXPOSURE)

    if not vc.isOpened():
        raise Exception("Camera is NOT opened!")

    return vc

def get_resolution(vc):
    w = int(vc.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return (w, h)

def get_last_reference_frame(vc):
    w, h = get_resolution(vc)
    default_frame = np.zeros((h, w, 3), dtype=np.uint8)
    
    files = sorted(utils.reference_frames_dpath.glob(f"*{config.PICTURE_EXT}"))
    if len(files) > 0:
        fpath = files[-1]
        frame = cv2.imread(fpath)

        if (frame.shape[0] != h) or (frame.shape[1] != w) or (frame.shape[2] != 3):
            frame = default_frame
    else:
        frame = default_frame

    return frame

def rotate_frame(frame, angle):
    h, w = frame.shape[:2]
    rotate_matrix = cv2.getRotationMatrix2D(
        center=(w/2, h/2),
        angle=angle,
        scale=1)
    
    frame_rotated = cv2.warpAffine(
        src=frame,
        M=rotate_matrix,
        dsize=(w, h))

    return frame_rotated

def get_part(frame, lrud_before_rot, angle, lrud_after_rot):
    xl, xr, yu, yd = lrud_before_rot
    frame_cropped_before_rot = frame[xl:xr, yu:yd]

    frame_rotated = rotate_frame(frame_cropped_before_rot, angle=angle)

    xl, xr, yu, yd = lrud_after_rot
    frame_cropped_after_rot = frame_rotated[xl:xr, yu:yd]

    frame_resized = cv2.resize(frame_cropped_after_rot,
                               (config.RESIZED_W, config.RESIZED_H))

    return frame_resized

def get_parts(frame):
    part_l = get_part(
        frame, config.LRUD_BEFORE_ROT_L,
        config.ANGLE_L, config.LRUD_AFTER_ROT_L)

    part_r = get_part(
        frame, config.LRUD_BEFORE_ROT_R,
        config.ANGLE_R, config.LRUD_AFTER_ROT_R)

    return part_l, part_r

def get_part_level(frame, ref_frame):
    diff = cv2.absdiff(frame, ref_frame)
    level = int(diff.mean())
    return level

def get_parts_state(part_l, part_r, ref_part_l, ref_part_r, thr_l, thr_r):
    level_l = get_part_level(part_l, ref_part_l)
    level_r = get_part_level(part_r, ref_part_r)

    l = level_l > thr_l
    r = level_r > thr_r

    dt_str = datetime.now(config.IS_TZ).strftime("%d.%m.%Y %H:%M:%S.%f")
    print(f"[{dt_str}]    {level_l:3} ({thr_l})    {level_r:3} ({thr_r})")

    return l, r
