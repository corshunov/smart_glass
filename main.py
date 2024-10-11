import sys
sys.stdout.reconfigure(line_buffering=True)

from copy import deepcopy
from datetime import datetime
from pytz import timezone
import time
import traceback

import cv2

import camera
import utils

is_tz = timezone('Israel')

vc = camera.get_camera()

def main():
    try:
        utils.prepare_folders()

        dt = datetime.now(is_tz)

        reference_frame = utils.get_last_reference_frame(vc)
        ref_part_l, ref_part_r = camera.get_parts(reference_frame)

        thr_l, thr_r = utils.get_thresholds()

        part_l_state = False
        part_r_state = False
        parts_state = False
        stable_state_dt = dt

        utils.set_glass_state(False)
        glass_state_on = False
        glass_state_changed_dt = dt

        mode_manual = utils.is_mode_manual()

        stable_state_l_dt = dt
        stable_state_r_dt = dt

        part_l_i = 0
        part_r_i = 0

        log_file = utils.get_log_fpath(dt).open('w')
        n_log_rows = 0

        while True:
            prev_dt = dt
            dt = datetime.now(is_tz)
            dt_str = dt.strftime('%Y%m%dT%H%M%S.%f')

            # State defining whether the system should work or be idle.
            state_on = utils.is_state_on():
            if not state_on:
                time.sleep(1)
                continue

            # Reading frame.
            flag, frame = vc.read()
            if not flag:
                raise Exception("Failed to read frame!")
            
            part_l, part_r = utils.get_parts(frame)

            # Checking requests.
            frame_requested = utils.frame_requested()
            if frame_requested:
                utils.save_frame(frame, dt, reason='request')

            reference_frame_requested = utils.reference_frame_requested()
            if reference_frame_requested:
                utils.save_reference_frame(reference_frame, dt, update=False)
            
            update_reference_frame_requested = utils.update_reference_frame_requested()
            if update_reference_frame_requested:
                reference_frame = frame
                ref_part_l, ref_part_r = camera.get_parts(reference_frame)
                utils.save_reference_frame(reference_frame, dt, update=True)
                utils.save_reference_frame(reference_frame, dt, update=False)

            update_thresholds_requested, (thr_l_new, thr_r_new) = utils.update_thresholds_requested()
            if update_thresholds_requested:
                thr_l, thr_r = thr_l_new, thr_r_new
                save_thresholds(thr_l, thr_r)

            # Updating states.
            prev_part_l_state = part_l_state
            prev_part_r_state = part_r_state
            prev_parts_state = parts_state

            part_l_state, part_r_state = utils.get_parts_state(part_l,
                                                               part_r,
                                                               ref_part_l,
                                                               ref_part_r)
            parts_state = part_l_state and part_r_state

            # Defining action.
            action = None
            if (dt - glass_state_changed_dt).total_seconds() > config.TRANSITION_DURATION:
                prev_mode_manual = mode_manual
                mode_manual = utils.is_mode_manual()

                if mode_manual:
                    if prev_mode_manual:
                        glass_state_on_to_set = utils.glass_state_on_to_set()
                    else:
                        if glass_state_on:
                            glass_state_on_to_set = True
                            utils.set_glass_state_on(True)
                        else:
                            glass_state_on_to_set = False
                            utils.set_glass_state_on(False)

                    if glass_state_on_to_set and not glass_state_on:
                        action = 1
                    elif not glass_state_on_to_set and glass_state_on:
                        action = 0
                else:
                    if prev_parts_state != parts_state:
                        stable_state_dt = dt

                    stable_state_td = (dt - stable_state_dt).total_seconds()
                    if parts_state and not glass_state_on and stable_state_td > config.ON_DELAY:
                        action = 1
                    if not parts_state and glass_state_on and stable_state_td > config.OFF_DELAY:
                        action = 0

                if action: 
                    if action == 1:
                        utils.set_glass_state(True)
                        glass_state_on = True
                        glass_state_changed_dt = dt
                        utils.save_frame(frame, dt, reason='on')

                        log_file.write(f"{dt_str},action,{action}")
                        n_log_rows += 1
                    elif action == 0:
                        utils.set_glass_state(False)
                        glass_state_on = False
                        glass_state_changed_dt = dt
                        utils.save_frame(frame, dt, reason='off')
                        
                        log_file.write(f"{dt_str},action,{action}")
                        n_log_rows += 1

                if not mode_manual:
                    if prev_part_l_state != part_l_state:
                        stable_state_l_dt = dt
                    stable_state_l_td = (dt - stable_state_dt_l).total_seconds()

                    if prev_part_r_state != part_r_state:
                        stable_state_r_dt = dt
                    stable_state_r_td = (dt - stable_state_dt_r).total_seconds()

                    if part_l_state and part_l_i in [0,2] and stable_state_l_td > config.ON_DELAY:
                        part_l_i = 1
                        part_l_frame = frame
                    elif not part_l_state and part_l_i == 1 and stable_state_l_td > config.OFF_DELAY:
                        part_l_i = 2
                    elif part_l_i == 2:
                        part_l_i = 0

                    if part_r_state and part_r_i in [0,2] and stable_state_r_td > config.ON_DELAY:
                        part_r_i = 1
                        part_r_frame = frame
                    elif not part_r_state and part_r_i == 1 and stable_state_r_td > config.OFF_DELAY:
                        part_r_i = 2
                    elif part_r_i == 2:
                        part_r_i = 0

                    if part_l_i == 2 and part_r_i == 0:
                        save_frame(part_l_frame, dt, reason='single_l')
                        part_l_i = 0
                        part_r_i = 0
                    elif part_r_i == 2 and part_l_i == 0:
                        save_frame(part_r_frame, dt, reason='single_r')
                        part_l_i = 0
                        part_r_i = 0

            if (dt - temperature_dt).total_seconds() > 60:
                t_cpu = utils.get_temperature()
                log_file.write(f"{dt_str},t_cpu,{t_cpu:.1f}")
                n_log_rows += 1
                temperature_dt = dt

            if n_log_rows > 9999:
                log_file.close()
                log_file = utils.get_log_fpath(dt).open('w')
                n_log_rows = 0

    except Exception as e:
        vc.release()
        log_file.close()
        raise(e) from None
        

if __name__ == '__main__':
    try:
        main()

    except KeyboardInterrupt:
        print('\nExit\n')
    except Exception as e:
        tb = traceback.format_exc()
        utils.create_error_file(tb)
