import cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import controls
import time
from timestamp import get_time


if __name__ == '__main__':

    picam2 = Picamera2()

    config = picam2.create_still_configuration(buffer_count=2)
    picam2.configure(config)

    picam2.start()

    #previous_image = None
    #diff = 0

    #i = 0
    while True:
        time.sleep(1)

        image = picam2.capture_array("main")

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        #if previous_image is None:
        #    previous_image = image
        #else:
        #    diff = np.mean(np.abs(image - previous_image))

        #print(diff)

        #if diff > 100:
        #    previous_image = image
        cv2.imwrite(f'images/{get_time()}.jpg', image)
