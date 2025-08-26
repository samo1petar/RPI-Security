import time
import requests
import os
import hashlib
import shutil
import subprocess
import logging
from threading import Thread
from logging.handlers import TimedRotatingFileHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# CONFIGURATION
DASHBOARD_URL = "http://alfred.local:5000/upload"
CAMERA_NAME = "RPiZ1 Camera"
RECORD_DIR = "/home/rpiz1/RPI-Security/recordings"
PENDING_DIR = os.path.join(RECORD_DIR, "pending")
MAX_RETRIES = 300
RETRY_DELAY = 5  # seconds
CHECK_INTERVAL = 5
IDLE_TIME_REQUIRED = 10  # seconds
USE_COMPRESSION = True  # Use ffmpeg to compress .avi to .mp4

LOG_DIR = os.path.join(RECORD_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "upload.log")

logger = logging.getLogger("uploader")
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler(LOG_PATH, when='midnight', backupCount=7)
formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Ensure required dirs
os.makedirs(PENDING_DIR, exist_ok=True)

# Track files waiting for processing
pending_files = {}

def log(msg):
    logger.info(msg)
    print(msg)

def compress_video(input_path):
    base, _ = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(PENDING_DIR, f"{base}.mp4")
    try:
        subprocess.run([
            "ffmpeg", "-i", input_path, "-vcodec", "libx264", "-crf", "28", output_path
        ], check=True)
        return output_path
    except subprocess.CalledProcessError:
        log(f"❌ Compression failed for {input_path}")
        return None

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def upload_file(filepath):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (os.path.basename(filepath), f)}
                checksum = calculate_md5(filepath)
                data = {'camera': CAMERA_NAME, 'checksum': checksum}
                r = requests.post(DASHBOARD_URL, files=files, data=data)

            if r.status_code == 200:
                log(f"✅ Uploaded {filepath}")
                os.remove(filepath)
                return True
            else:
                log(f"❌ Upload failed ({r.status_code}) - attempt {attempt}")
        except Exception as e:
            log(f"🚨 Upload error on attempt {attempt}: {e}")

        time.sleep(RETRY_DELAY)

    log(f"⚠️ Giving up on {filepath} after {MAX_RETRIES} attempts.")
    return False

def background_processor():
    while True:
        now = time.time()
        ready_files = []

        for path, last_mod_time in list(pending_files.items()):
            if os.path.exists(path):
                current_mod_time = os.path.getmtime(path)
                if current_mod_time == last_mod_time and now - current_mod_time >= IDLE_TIME_REQUIRED:
                    ready_files.append(path)
            else:
                pending_files.pop(path, None)

        for filepath in ready_files:
            pending_files.pop(filepath, None)
            filename = os.path.basename(filepath)
            temp_path = os.path.join(PENDING_DIR, filename)

            try:
                shutil.move(filepath, temp_path)
                log(f"📂 Moved {filename} to pending/")

                # Compress
                final_path = compress_video(temp_path) if USE_COMPRESSION else temp_path

                # Remove raw .avi after compression
                if final_path and final_path != temp_path:
                    os.remove(temp_path)

                # Upload
                if final_path:
                    upload_file(final_path)

            except Exception as e:
                log(f"🚨 Error processing {filename}: {e}")

        time.sleep(CHECK_INTERVAL)

class RecordingWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.avi'):
            path = event.src_path
            pending_files[path] = os.path.getmtime(path)
            log(f"🕒 Detected new file: {path}")

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.avi'):
            pending_files[event.src_path] = os.path.getmtime(event.src_path)

if __name__ == "__main__":
    observer = Observer()
    observer.schedule(RecordingWatcher(), RECORD_DIR, recursive=False)
    observer.start()

    Thread(target=background_processor, daemon=True).start()
    log("📡 Watching for complete recordings...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
