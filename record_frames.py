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
    config = cam.create_still_configuration(transform=Transform(hflip=True, vflip=True))
    cam.configure(config)
    cam.start()

    start = time.time()

    while True:
        if time.time() - start > 1:
            image = cam.capture_array('main')
            # image = cv2.rotate(image, cv2.ROTATE_180_CLOCKWISE)
            save_image(image, args.name)
            start = time.time()
        else:
            time.sleep(0.1)
