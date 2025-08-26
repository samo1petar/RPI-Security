import cv2
import time
import os
import logging
from logging.handlers import RotatingFileHandler
from picamera2 import Picamera2

# Setup logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "motion.log")

logger = logging.getLogger("MotionRecorder")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Camera configuration
frame_width, frame_height = 640, 480
fps = 20
record_dir = "recordings"
os.makedirs(record_dir, exist_ok=True)

# Initialize camera
logger.info("Starting camera...")
picam2 = Picamera2()
picam2.preview_configuration.main.size = (frame_width, frame_height)
picam2.preview_configuration.main.format = "BGR888"
picam2.configure("preview")
picam2.start()
time.sleep(2)
logger.info("Camera started.")

# Recording state
is_recording = False
motion_triggered = False
last_motion_time = time.time()
video_writer = None
recording_start_time = None

def get_new_video_writer():
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_path = f"{record_dir}/video_{timestamp}.avi"
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    logger.info(f"Started new recording: {output_path}")
    return cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

def motion_detected(prev, curr, threshold=30, min_area=5000):
    diff = cv2.absdiff(prev, curr)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return any(cv2.contourArea(c) > min_area for c in contours)

# Main loop
prev_frame = None
logger.info("Motion detection started.")
try:
    while True:
        frame = picam2.capture_array()
        curr_time = time.time()

        if prev_frame is not None:
            if motion_detected(prev_frame, frame):
                if not motion_triggered:
                    logger.info("Motion detected.")
                motion_triggered = True
                last_motion_time = curr_time
            elif motion_triggered and (curr_time - last_motion_time > 10):
                if is_recording:
                    logger.info("Stopping recording due to inactivity.")
                    video_writer.release()
                    video_writer = None
                is_recording = False
                motion_triggered = False

        prev_frame = frame.copy()

        if motion_triggered and not is_recording:
            video_writer = get_new_video_writer()
            is_recording = True
            recording_start_time = curr_time

        if is_recording and (curr_time - recording_start_time > 600):
            logger.info("Max segment length reached. Rotating file.")
            video_writer.release()
            video_writer = get_new_video_writer()
            recording_start_time = curr_time

        if is_recording:
            video_writer.write(frame)

except KeyboardInterrupt:
    logger.info("Keyboard interrupt received. Exiting.")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
finally:
    if video_writer:
        logger.info("Releasing video writer.")
        video_writer.release()
    logger.info("Stopping camera.")
    picam2.stop()
    logger.info("Shutdown complete.")
