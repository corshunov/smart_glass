from datetime import timedelta
import traceback

import cv2

import sycam
import sycfg as c
import sydt
import syfiles
import syglstate
import sylight
import symode
import systate
import sytemp
import sythr

syfiles.reconfigure_stdout()

def log(state, dt=None):
    if dt is None:
        dt = sydt.now()
    dt_str = sydt.get_str(dt)

    fpath = syfiles.get_log_path(dt)
    with fpath.open('a') as f:
        f.write(f"{dt_str},service,{state}\n")

def main():
    dt = sydt.now()
    log("start", dt)

    vc = sycam.get()

    try:
        syfiles.prepare_folders()

        temp_delta = timedelta(minutes=5)
        next_temp_dt = dt - temp_delta # to update it on the 1st iteration

        light_delta = timedelta(seconds=10)
        next_light_dt = dt - light_delta # to update it on the 1st iteration

        state = systate.ON
        systate.set(state)

        mode = symode.get()

        glstate = syglstate.OFF
        syglstate.set(glstate)
        glstate_dt = dt

        black_frame = sycam.get_black_frame(vc)
        sycam.save_state_frame(black_frame, kind="black")

        try:
            reference_frame = sycam.get_reference_frame(vc)
        except:
            reference_frame = black_frame

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

            # Temperature.
            if dt > next_temp_dt:
                temp = sytemp.get()
                sytemp.log(temp, dt)
                next_temp_dt = dt + temp_delta

            # State.
            prev_state = state

            flag, state_new = systate.set_present()
            if flag:
                systate.set(state_new)
                state = state_new
            else:
                state = systate.get()

            # Mode.
            prev_mode = mode

            flag, mode_new = symode.set_present()
            if flag:
                symode.set(mode_new)
                mode = mode_new
            else:
                mode = symode.get()

            # Update thresholds request.
            flag, (thr_l_new, thr_r_new) = sythr.update_thresholds_present()
            if flag:
                sythr.save(thr_l_new, thr_r_new)
                thr_l, thr_r = thr_l_new, thr_r_new

            # Continue or idle.
            if state == systate.OFF:
                if glstate == syglstate.ON:
                    glstate = syglstate.OFF 
                    syglstate.set(glstate)
                    glstate_dt = dt
                    sycam.save_frame(frame, metadata+[f"set_glass_{glstate.lower()}"])

                print(f"{dt_str} - {state} - {mode} - L --- ({thr_l}) - R --- ({thr_r}) - {glstate}")

                sydt.sleep(1)
                continue

            # Frame.
            flag, frame = vc.read()
            if not flag:
                raise Exception("Failed to read frame.")

            # Light.
            if dt > next_light_dt:
                if sycam.is_light_on(frame):
                    light_state = sylight.ON
                else:
                    light_state = sylight.OFF

                sylight.set(light_state)
                next_light_dt = dt + light_delta

            # Parts.
            prev_part_l_state = part_l_state
            prev_part_r_state = part_r_state

            part_l, part_r = sycam.get_parts(frame)

            level_l = sycam.get_level(part_l, ref_part_l)
            level_r = sycam.get_level(part_r, ref_part_r)
            
            part_l_state = level_l > thr_l
            part_r_state = level_r > thr_r

            prev_parts_state = parts_state
            parts_state = part_l_state and part_r_state

            # Frame metadata.
            metadata = [
                dt,
                level_l,
                level_r,
                thr_l,
                thr_r,
            ]

            # Save frame request.
            if sycam.save_frame_present():
                sycam.save_frame(frame, metadata+['save_frame'])

            # Update and save reference frame request.
            if sycam.update_save_reference_frame_present():
                reference_frame = frame
                ref_part_l, ref_part_r = sycam.get_parts(reference_frame)
                sycam.save_frame(reference_frame, metadata+['update_save_ref_frame'])
                sycam.save_state_frame(reference_frame, kind="reference")

            # Glass state.
            prev_glstate = glstate

            if (dt - glstate_dt).total_seconds() > c.TRANSITION_DURATION:
                if mode == symode.MANUAL:
                    flag, glstate_new = syglstate.set_present()
                    if flag:
                        glstate = glstate_new
                else:
                    # Invoked just to remove 'set_glstate' files which are not relevant in AUTO mode.
                    syglstate.set_present() 

                    if prev_parts_state != parts_state:
                        parts_state_dt = dt

                    parts_state_delta = (dt - parts_state_dt).total_seconds()
                    if parts_state and prev_glstate == syglstate.OFF and parts_state_delta > c.ON_DELAY:
                        glstate = syglstate.ON
                    elif not parts_state and prev_glstate == syglstate.ON and parts_state_delta > c.OFF_DELAY:
                        glstate = syglstate.OFF

                    if light_state == sylight.OFF:
                        glstate = syglstate.OFF

                if prev_glstate != glstate:
                    syglstate.set(glstate)
                    glstate_dt = dt
                    sycam.save_frame(frame, metadata+[f"set_glass_{glstate.lower()}"])

                    if glstate == syglstate.OFF:
                        part_l_i = 3
                        part_r_i = 3

            # Parts state.
            if prev_part_l_state != part_l_state:
                part_l_state_dt = dt
            part_l_state_delta = (dt - part_l_state_dt).total_seconds()

            if prev_part_r_state != part_r_state:
                part_r_state_dt = dt
            part_r_state_delta = (dt - part_r_state_dt).total_seconds()

            if part_l_state and part_l_i == 0 and part_l_state_delta > c.ON_DELAY:
                part_l_i = 1
                part_l_frame = frame
                metadata_l = [
                    dt,
                    level_l,
                    level_r,
                    thr_l,
                    thr_r,
                ]
            elif not part_l_state and part_l_i == 1 and part_l_state_delta > c.OFF_DELAY:
                part_l_i = 2
            elif part_l_i == 2:
                part_l_i = 0
            elif part_l_i == 3 and not part_l_state and not part_r_state:
                part_l_i = 0

            if part_r_state and part_r_i == 0 and part_r_state_delta > c.ON_DELAY:
                part_r_i = 1
                part_r_frame = frame
                metadata_r = [
                    dt,
                    level_l,
                    level_r,
                    thr_l,
                    thr_r,
                ]
            elif not part_r_state and part_r_i == 1 and part_r_state_delta > c.OFF_DELAY:
                part_r_i = 2
            elif part_r_i == 2:
                part_r_i = 0
            elif part_r_i == 3 and not part_l_state and not part_r_state:
                part_r_i = 0

            if part_l_i == 2 and part_r_i == 0:
                sycam.save_frame(part_l_frame, metadata_l+['single'])
            elif part_r_i == 2 and part_l_i == 0:
                sycam.save_frame(part_r_frame, metadata_r+['single'])

            # Print.
            print(f"{dt_str} - {state} - {mode} - L {level_l:3} ({thr_l}) {part_l_state} {part_l_i} - R {level_r:3} ({thr_r}) {part_r_state} {part_r_i} - {glstate}")

    except Exception as e:
        vc.release()
        raise(e) from e
        

if __name__ == '__main__':
    try:
        main()

    except KeyboardInterrupt:
        log("end")
        print('\nExit\n')
    except Exception as e:
        tb = traceback.format_exc()
        log("error")
        print(tb)
