import numpy as np
import cv2

import sycfg as c
import sydt
import syfiles

def get(i=0):
    vc = cv2.VideoCapture(i)
    vc.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
    vc.set(cv2.CAP_PROP_FRAME_WIDTH, c.REAL_W)
    vc.set(cv2.CAP_PROP_FRAME_HEIGHT, c.REAL_H)
    vc.set(cv2.CAP_PROP_FPS, c.FPS)
    vc.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    vc.set(cv2.CAP_PROP_EXPOSURE, c.EXPOSURE)

    if not vc.isOpened():
        raise Exception("Camera is NOT opened!")

    return vc

def get_resolution(vc):
    w = int(vc.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return (w, h)

def get_black_frame(vc):
    w, h = get_resolution(vc)
    return np.zeros((h, w, 3), dtype=np.uint8)

def get_reference_frame(vc):
    if syfiles.reference_frame_fpath.is_file():
        frame = cv2.imread(syfiles.reference_frame_fpath)

        w, h = get_resolution(vc)
        if (frame.shape[0] == h) or (frame.shape[1] == w) or (frame.shape[2] == 3):
            return frame

    raise Exception("No valid reference frame found.")

def log_frame(metadata):
    dt, level_l, level_r, thr_l, thr_r, reason = metadata
    if dt is None:
        dt = sydt.now()
    dt_str = sydt.get_str(dt)

    text = f"{level_l};{level_r}  {thr_l};{thr_r}  {reason}"

    fpath = syfiles.get_log_path(dt)
    with fpath.open('a') as f:
        f.write(f"{dt_str},frame,{text}\n")

def save_frame(frame, metadata):
    fpath = syfiles.get_frame_path(metadata)
    cv2.imwrite(fpath, frame)
    syfiles.wait_until_file(fpath, present=True)
    log_frame(metadata)

def save_state_frame(frame, kind):
    if kind == "reference":
        fpath = syfiles.reference_frame_fpath
    elif kind == "black":
        fpath = syfiles.black_frame_fpath
    else:
        raise Exception("Invalid 'kind' argument")

    cv2.imwrite(fpath, frame)
    syfiles.wait_until_file(fpath, present=True)

def save_black_frame(frame):
    cv2.imwrite(syfiles.reference_frame_fpath, frame)
    syfiles.wait_until_file(syfiles.reference_frame_fpath, present=True)

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
                               (c.RESIZED_W, c.RESIZED_H))

    return frame_resized

def get_parts(frame):
    part_l = get_part(
        frame, c.LRUD_BEFORE_ROT_L,
        c.ANGLE_L, c.LRUD_AFTER_ROT_L)

    part_r = get_part(
        frame, c.LRUD_BEFORE_ROT_R,
        c.ANGLE_R, c.LRUD_AFTER_ROT_R)

    return part_l, part_r

def get_level(frame, reference_frame):
    diff = cv2.absdiff(frame, reference_frame)
    level = int(diff.mean())
    return level

def is_light_on(frame):
    black_frame = cv2.imread(syfiles.black_frame_fpath)
    level = get_level(frame, black_frame)
    if level > 40:
        return True

    return False

def save_frame_present():
    return syfiles.remove_file(syfiles.save_frame_fpath)

def save_frame_request():
    syfiles.create_file(syfiles.save_frame_fpath)

def update_save_reference_frame_present():
    return syfiles.remove_file(syfiles.update_save_reference_frame_fpath)

def update_save_reference_frame_request():
    syfiles.create_file(syfiles.update_save_reference_frame_fpath)
