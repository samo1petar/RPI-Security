import cv2
import time
import argparse
from picamera2 import Picamera2
from libcamera import controls, Transform
from lib.utils.timestamp import get_time


def save_image(image, name):
    cv2.imwrite(f'images/{name}_{get_time()}.jpg', image)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', dest='name', type=str)
    parser.add_argument('-r', '--rotate', dest='rotate', ) # ToDo not used yet

    args = parser.parse_args()

    cam = Picamera2()
    cam.set_controls({
        'AfMode': controls.AfModeEnum.Manual,
        'LensPosition': 0.0
    })

    mode = cam.sensor_modes[1]

    print(mode)

    config = cam.create_preview_configuration(
        sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']},
        main={'format': 'RGB888', 'size': (1080, 720)}, #(1920, 1080)}, # (2304, 1296)},
        transform=Transform(hflip=True, vflip=True),
    )
    cam.configure(config)

    cam.start()

    success = cam.autofocus_cycle()

    print(f'Autofocus is a {success}.')

    start = time.time()

    while True:
        if time.time() - start > 1:
            image = cam.capture_array('main')
            save_image(image, args.name)
            start = time.time()
        else:
            time.sleep(0.1)
