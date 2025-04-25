import time
import requests
import os
import hashlib
import shutil
import subprocess
import logging
from logging.handlers import TimedRotatingFileHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# CONFIGURATION
DASHBOARD_URL = "http://alfred.local:5000/upload"
CAMERA_NAME = "RPiZ1 Camera"
RECORD_DIR = "/home/rpiz1/RPI-Security/recordings"
PENDING_DIR = os.path.join(RECORD_DIR, "pending")
#LOG_FILE = os.path.join(RECORD_DIR, "upload_log.txt")
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
USE_COMPRESSION = True  # Toggle .mp4 compression

LOG_DIR = os.path.join(RECORD_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "upload.log")

logger = logging.getLogger("uploader")
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler(LOG_PATH, when='midnight', backupCount=7)
formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Ensure pending folder exists
os.makedirs(PENDING_DIR, exist_ok=True)

#def log(message):
#    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
#    with open(LOG_FILE, 'a') as logf:
#        logf.write(f"[{timestamp}] {message}\n")
#    print(message)

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

class UploadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.avi'):
            original_path = event.src_path
            filename = os.path.basename(original_path)
            temp_path = os.path.join(PENDING_DIR, filename)

            try:
                shutil.move(original_path, temp_path)
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

if __name__ == "__main__":
    observer = Observer()
    observer.schedule(UploadHandler(), RECORD_DIR, recursive=False)
    observer.start()
    log("📡 Watching for new recordings...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
