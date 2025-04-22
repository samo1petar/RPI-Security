import cv2
import time
import argparse
from picamera2 import Picamera2
from libcamera import controls
from lib.utils.timestamp import get_time


def save_image(image, name):
    cv2.imwrite(f'images/{name}_{get_time()}.png', image)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', dest='name', type=str)

    args = parser.parse_args()

    cam = Picamera2()
    cam.set_controls({
        'AfMode': controls.AfModeEnum.Manual,
        'LensPosition': 0.0
    })

    cam.start()

    while True:
        time.sleep(1)

        image = cam.capture_array('main')

        save_image(image, args.name)
