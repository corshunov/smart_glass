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

def get_default_reference_frame(vc):
    w, h = get_resolution(vc)
    return np.zeros((h, w, 3), dtype=np.uint8)

def get_reference_frame(vc):
    if syfiles.reference_frame_fpath.is_file():
        frame = cv2.imread(syfiles.reference_frame_fpath)

        w, h = get_resolution(vc)
        if (frame.shape[0] == h) or (frame.shape[1] == w) or (frame.shape[2] == 3):
            return frame

    raise Exception("No valid reference frame found.")

def log_frame(reason, dt=None):
    if dt is None:
        dt = sydt.now()
    dt_str = sydt.get_str(dt)

    fpath = syfiles.get_log_path(dt)
    with fpath.open('a') as f:
        f.write(f"{dt_str},frame,{reason}\n")

def save_frame(frame, dt, reason):
    if reason == "save_frame":
        ext = f"save_frame-.{c.PICTURE_EXT}"
    elif reason == "update_save_ref_frame":
        ext = f"update_save_ref_frame-.{c.PICTURE_EXT}"
    elif reason == "set_glass_on":
        ext = f"set_glass_on-.{c.PICTURE_EXT}"
    elif reason == "set_glass_off":
        ext = f"set_glass_off-.{c.PICTURE_EXT}"
    else:
        raise Exception("Invalid 'reason' argument.")

    fpath = syfiles.frames_dpath / syfiles.get_filename("frame", dt, ext)
    cv2.imwrite(fpath, frame)
    syfiles.wait_until_file(fpath, present=True)
    log_frame(reason, dt)

def backup_reference_frame(frame):
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

def get_part_level(frame, reference_frame):
    diff = cv2.absdiff(frame, reference_frame)
    level = int(diff.mean())
    return level

def save_frame_present():
    return syfiles.remove_file(syfiles.save_frame_fpath)

def save_frame_request():
    syfiles.create_file(syfiles.save_frame_fpath)

def update_save_reference_frame_present():
    return syfiles.remove_file(syfiles.update_save_reference_frame_fpath)

def update_save_reference_frame_request():
    syfiles.create_file(syfiles.update_save_reference_frame_fpath)
