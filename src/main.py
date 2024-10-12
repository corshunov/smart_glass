import cv2

import sycam
import sycfg as c
import sydt
import syfiles
import syglstate
import symode
import systate
import sytemp
import sythr

syfiles.reconfigure_stdout()

def main():
    dt = sydt.now()

    syfiles.prepare_folders()

    sytemp.log_temperature(dt)
    temp_dt = dt

    vc = sycam.get()

    try:
        systate.set(systate.ON)

        mode = symode.get()

        glstate = syglstate.OPAQUE
        syglstate.set(glstate)
        glstate_dt = dt

        try:
            reference_frame = sycam.get_reference_frame(vc)
        except:
            reference_frame = sycam.get_default_reference_frame(vc)

        ref_part_l, ref_part_r = sycam.get_parts(reference_frame)

        thr_l, thr_r = sythr.get()

        part_l_state = False
        part_r_state = False
        parts_state = False

        part_l_state_dt = dt
        part_r_state_dt = dt
        parts_state_dt = dt

        part_l_i = 0
        part_r_i = 0

        while True:
            prev_dt = dt
            dt = sydt.now()
            dt_str = sydt.get_str(dt)

            # Logging temperature.
            if (dt - temp_dt).total_seconds() >= 300:
                temp = sytemp.get()
                sytemp.log(temp, dt)
                temp_dt = dt

            # State defining whether the system should work or be idle.
            if systate.get() == systate.OFF:
                sleep(1)
                continue

            # Reading frame.
            flag, frame = vc.read()
            if not flag:
                raise Exception("Failed to read frame.")
            
            part_l, part_r = sycam.get_parts(frame)

            # Checking requests.
            if sycam.request_frame_present():
                sycam.save_frame(frame, dt, reason='REQUEST')

            if sycam.update_reference_frame_present():
                reference_frame = frame
                ref_part_l, ref_part_r = sycam.get_parts(reference_frame)
                sycam.save_frame(reference_frame, dt, reason='REFERENCE_UPDATE')
                sycam.backup_reference_frame(reference_frame)

            flag, (thr_l_new, thr_r_new) = sythr.update_thresholds_present()
            if flag:
                thr_l, thr_r = thr_l_new, thr_r_new
                sythr.save(thr_l, thr_r)

            # Updating states.
            prev_mode = mode
            mode = symode.get()

            prev_part_l_state = part_l_state
            prev_part_r_state = part_r_state

            part_l_state, part_r_state = sycam.get_parts_state(
                part_l, part_r, ref_part_l, ref_part_r, thr_l, thr_r)
            
            prev_parts_state = parts_state
            parts_state = part_l_state and part_r_state

            prev_glstate = glstate

            # Defining glass state.
            if (dt - glstate_dt).total_seconds() > c.TRANSITION_DURATION:
                if mode == symode.MANUAL:
                    glstate = syglstate.get()
                else:
                    if prev_parts_state != parts_state:
                        parts_state_dt = dt

                    parts_state_delta = (dt - parts_state_dt).total_seconds()
                    if parts_state and prev_glstate == syglstate.OPAQUE and parts_state_delta > c.ON_DELAY:
                        glstate = syglstate.TRANSPARENT
                    elif not parts_state and prev_glstate == syglstate.TRANSPARENT and parts_state_delta > c.OFF_DELAY:
                        glstate = syglstate.OPAQUE

                if prev_glstate != glstate:
                    syglstate.set(glstate)
                    glstate_dt = dt
                    sycam.save_frame(frame, dt, reason=f"GLASS_{glstate}")

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
        import traceback
        tb = traceback.format_exc()
        syfiles.output_error(tb)
