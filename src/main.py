import sys
sys.stdout.reconfigure(line_buffering=True)

from datetime import datetime
import time
import traceback

import cv2

import config
import camera
import utils

def main():
    dt = datetime.now(config.IS_TZ)
    temperature_dt = dt

    utils.prepare_folders()

    vc = camera.get_camera()

    try:
        utils.set_state("ON")

        mode = utils.get_mode()

        glass_state = "OPAQUE"
        utils.set_glass_state(glass_state)
        glass_state_changed_dt = dt

        reference_frame = camera.get_last_reference_frame(vc)
        ref_part_l, ref_part_r = camera.get_parts(reference_frame)

        thr_l, thr_r = utils.get_thresholds()

        part_l_state = False
        part_r_state = False
        parts_state = False

        stable_state_l_dt = dt
        stable_state_r_dt = dt
        stable_state_dt = dt

        part_l_i = 0
        part_r_i = 0

        while True:
            prev_dt = dt
            dt = datetime.now(config.IS_TZ)
            dt_str = dt.strftime('%Y%m%dT%H%M%S.%f')

            # Logging temperature.
            if (dt - temperature_dt).total_seconds() >= 300:
                utils.log_temperature(dt)
                temperature_dt = dt

            # State defining whether the system should work or be idle.
            state = utils.get_state()
            if state == "OFF":
                time.sleep(1)
                continue

            # Reading frame.
            flag, frame = vc.read()
            if not flag:
                raise Exception("Failed to read frame!")
            
            part_l, part_r = camera.get_parts(frame)

            # Checking requests.
            frame_requested = utils.frame_requested()
            if frame_requested:
                utils.save_frame(frame, dt, reason='REQUEST')

            update_reference_frame_requested = utils.update_reference_frame_requested()
            if update_reference_frame_requested:
                reference_frame = frame
                ref_part_l, ref_part_r = camera.get_parts(reference_frame)
                utils.save_reference_frame(reference_frame, dt)
                utils.save_frame(reference_frame, dt, reason='REFERENCE_UPDATE')

            reference_frame_requested = utils.reference_frame_requested()
            if reference_frame_requested:
                utils.save_frame(reference_frame, dt, reason='REFERENCE_REQUEST')

            update_thresholds_requested, (thr_l_new, thr_r_new) = utils.update_thresholds_requested()
            if update_thresholds_requested:
                thr_l, thr_r = thr_l_new, thr_r_new
                utils.save_thresholds(thr_l, thr_r)

            # Updating states.
            prev_mode = mode
            mode = utils.get_mode()

            prev_part_l_state = part_l_state
            prev_part_r_state = part_r_state

            part_l_state, part_r_state = camera.get_parts_state(part_l,
                                                                part_r,
                                                                ref_part_l,
                                                                ref_part_r,
                                                                thr_l,
                                                                thr_r)
            
            prev_parts_state = parts_state
            parts_state = part_l_state and part_r_state

            prev_glass_state = glass_state

            # Defining glass state.
            if (dt - glass_state_changed_dt).total_seconds() > config.TRANSITION_DURATION:
                if mode == "MANUAL":
                    glass_state = utils.get_glass_state()
                else:
                    if prev_parts_state != parts_state:
                        stable_state_dt = dt

                    stable_state_td = (dt - stable_state_dt).total_seconds()
                    if parts_state and prev_glass_state == "OPAQUE" and stable_state_td > config.ON_DELAY:
                        glass_state = "TRANSPARENT"
                    elif not parts_state and prev_glass_state == "TRANSPARENT" and stable_state_td > config.OFF_DELAY:
                        glass_state = "OPAQUE"

                if prev_glass_state != glass_state:
                    utils.set_glass_state(glass_state)
                    glass_state_changed_dt = dt
                    utils.save_frame(frame, dt, reason=f"GLASS_{glass_state}")

                    with utils.get_log_fpath(dt).open('a') as f:
                        line = f"{dt_str},{mode},{glass_state}\n"
                        f.write(line)

#                elif mode = "AUTO":
#                    if prev_part_l_state != part_l_state:
#                        stable_state_l_dt = dt
#                    stable_state_l_td = (dt - stable_state_dt_l).total_seconds()
#
#                    if prev_part_r_state != part_r_state:
#                        stable_state_r_dt = dt
#                    stable_state_r_td = (dt - stable_state_dt_r).total_seconds()
#
#                    if part_l_state and part_l_i in [0,2] and stable_state_l_td > config.ON_DELAY:
#                        part_l_i = 1
#                        part_l_frame = frame
#                    elif not part_l_state and part_l_i == 1 and stable_state_l_td > config.OFF_DELAY:
#                        part_l_i = 2
#                    elif part_l_i == 2:
#                        part_l_i = 0
#
#                    if part_r_state and part_r_i in [0,2] and stable_state_r_td > config.ON_DELAY:
#                        part_r_i = 1
#                        part_r_frame = frame
#                    elif not part_r_state and part_r_i == 1 and stable_state_r_td > config.OFF_DELAY:
#                        part_r_i = 2
#                    elif part_r_i == 2:
#                        part_r_i = 0
#
#                    if part_l_i == 2 and part_r_i == 0:
#                        save_frame(part_l_frame, dt, reason='single_l')
#                        part_l_i = 0
#                        part_r_i = 0
#                    elif part_r_i == 2 and part_l_i == 0:
#                        save_frame(part_r_frame, dt, reason='single_r')
#                        part_l_i = 0
#                        part_r_i = 0

    except Exception as e:
        print('inside exception')
        vc.release()
        raise(e) from None
        

if __name__ == '__main__':
    try:
        main()

    except KeyboardInterrupt:
        print('\nExit\n')
    except Exception as e:
        tb = traceback.format_exc()
        utils.create_error_file(tb)
