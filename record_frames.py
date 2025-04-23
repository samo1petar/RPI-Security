import cv2
import time
import argparse
from picamera2 import Picamera2
from libcamera import controls, Transform
from lib.utils.timestamp import get_time


def save_image(image, name):
    cv2.imwrite(f'images/{name}_{get_time()}.png', image)


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

    config = cam.create_preview_configuration(
        sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']},
        transform=Transform(hflip=True, vflip=True),
    )
    cam.configure(config)
    cam.start()

    start = time.time()

    while True:
        if time.time() - start > 1:
            image = cam.capture_array('main')
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            save_image(image, args.name)
            start = time.time()
        else:
            time.sleep(0.1)
