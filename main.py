from copy import deepcopy
from datetime import datetime, timedelta

import cv2
import serial

fps = 20.0
video_length = 5 # seconds


def set_glass_transparent(ser, flag):
    if flag:
        cmd = "1"
    else:
        cmd = "0"

    #ser.write(cmd.encode())

def run_main_loop(vc, ser):
    try:
        utils.prepare_folders()

        ref_frame = utils.get_ref_frame(vc)
        frame = deepcopy(ref_frame)

        video_out = None

        glass_transparent = False
        set_glass_transparent(False)

        log_file = open(utils.log_file)

        while True:
            dt = datetime.now()
            dt_str = dt.strftime("%d.%m.%Y %H:%M:%S")

            prev_frame = deepcopy(frame)

            flag, frame = vc.read()
            if not flag:
                raise Exception("Failed to read frame!")

            update_ref_frame_flag = update_ref_frame_requested()
            if update_ref_frame_flag:
                ref_frame = deepcopy(frame)
                utils.save_ref_frame(ref_frame, dt)

            if video_out:
                recording_flag = True

                video_out.write(frame)

                if dt > video_end_dt:
                    video_out.release()
                    video_out = None
            else:
                recording_flag = False

                if recording_requested():
                    video_end_dt = dt + timedelta(seconds=video_length)
                    video_out = utils.get_video_writer(vc, dt)

            if both_steps_filled(frame, prev_frame, ref_frame):
                if not glass_transparent:
                    set_glass_transparent(ser, True)
                    glass_transparent = True
            else:
                if glass_transparent:
                    set_glass_transparent(ser, False)
                    glass_transparent = False
            
            line = f"{dt_str},{update_ref_frame_flag},{recording_flag},{glass_transparent}"
            log_file.write(line)

    except Exception as e:
        vc.release()

        if video_out is not None:
            video_out.release()
            video_out = None

        log_file.close()

        raise(e) from None
        

if __name__ == '__main__':
    try:
        ser = serial.Serial("/dev/ttyUSB0")
        ser.baudrate = 115200

        vc = cv2.VideoCapture(0)
        vc.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        vc.set(cv2.CAP_PROP_EXPOSURE, 40)

        if not vc.isOpened():
            raise Exception("Camera is NOT opened!")

        run_main_loop(vc, ser)

    except KeyboardInterrupt:
        print('Exit')
    except Exception as e:
        utils.create_error_file(str(e))
