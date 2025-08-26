from flask import Flask, Response, render_template_string, request, send_from_directory
from picamera2 import Picamera2
import cv2
import threading
import time
import os
import numpy as np
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
picam2 = Picamera2()
frame_width, frame_height = 640, 480
fps = 20

# Configure camera
picam2.preview_configuration.main.size = (frame_width, frame_height)
picam2.preview_configuration.main.format = "BGR888"
picam2.configure("preview")
picam2.start()

# Global state
is_recording = False
motion_triggered = False
last_motion_time = time.time()
lock = threading.Lock()
video_writer = None
recording_start_time = None
email_sent_time = 0

# Recording folder
record_dir = "recordings"
os.makedirs(record_dir, exist_ok=True)

# Email settings (EDIT THIS)
EMAIL_ENABLED = False
EMAIL_ADDRESS = "rpiz1@home_zapresic.hr"
EMAIL_PASSWORD = ""
EMAIL_TO = "petar.pavlovic.37@gmail.com"

def send_email_notification():
    global email_sent_time
    now = time.time()
    if now - email_sent_time < 60:  # avoid spam
        return
    email_sent_time = now

    msg = EmailMessage()
    msg["Subject"] = "Motion Detected!"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO
    msg.set_content("Motion was detected on your Raspberry Pi camera.")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("Email sent.")
    except Exception as e:
        print("Failed to send email:", e)

def get_new_video_writer():
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_path = f"{record_dir}/video_{timestamp}.avi"
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    return cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

def motion_detected(prev, curr, threshold=30, min_area=5000):
    diff = cv2.absdiff(prev, curr)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return any(cv2.contourArea(c) > min_area for c in contours)

def generate_frames():
    global is_recording, video_writer, recording_start_time, motion_triggered, last_motion_time
    prev_frame = None

    while True:
        frame = picam2.capture_array()
        curr_time = time.time()

        if prev_frame is not None:
            if motion_detected(prev_frame, frame):
                motion_triggered = True
                last_motion_time = curr_time
                if EMAIL_ENABLED:
                    send_email_notification()
            else:
                if motion_triggered and (curr_time - last_motion_time > 10):
                    with lock:
                        if is_recording and video_writer:
                            video_writer.release()
                        is_recording = False
                        motion_triggered = False

        prev_frame = frame.copy()

        if motion_triggered and not is_recording:
            with lock:
                video_writer = get_new_video_writer()
                is_recording = True
                recording_start_time = curr_time

        if is_recording and (curr_time - recording_start_time > 600):
            with lock:
                if video_writer:
                    video_writer.release()
                video_writer = get_new_video_writer()
                recording_start_time = curr_time

        if is_recording:
            with lock:
                video_writer.write(frame)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    elapsed = 0
    if is_recording and recording_start_time:
        elapsed = int(time.time() - recording_start_time)

    return render_template_string('''
        <h1>🎥 Raspberry Pi Smart Cam</h1>
        <img src="{{ url_for('video') }}" width="640"><br><br>
        <form action="/start" method="post"><button type="submit">▶️ Start Manual Recording</button></form>
        <form action="/stop" method="post"><button type="submit">⏹ Stop Manual Recording</button></form>
        <p>Status: {{ "Recording" if is_recording else "Idle" }}</p>
        <p>Motion Trigger: {{ "Active" if motion_triggered else "None" }}</p>
        {% if is_recording %}
        <p>🕒 Recording Time: {{ elapsed }} seconds</p>
        {% endif %}
        <hr>
        <h3>📁 Recordings:</h3>
        <ul>
        {% for file in files %}
            <li><a href="/recordings/{{ file }}">{{ file }}</a></li>
        {% endfor %}
        </ul>
    ''', is_recording=is_recording, motion_triggered=motion_triggered,
       elapsed=elapsed, files=sorted(os.listdir(record_dir), reverse=True))

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start', methods=['POST'])
def start_recording():
    global is_recording, video_writer, recording_start_time
    with lock:
        if not is_recording:
            video_writer = get_new_video_writer()
            is_recording = True
            recording_start_time = time.time()
    return ('', 204)

@app.route('/stop', methods=['POST'])
def stop_recording():
    global is_recording, video_writer
    with lock:
        if video_writer:
            video_writer.release()
        is_recording = False
    return ('', 204)

@app.route('/status')
def status():
    return {
        "recording": is_recording,
        "motion": motion_triggered,
        "recording_time": int(time.time() - recording_start_time) if is_recording else 0,
        "files": sorted(os.listdir(record_dir), reverse=True)
    }

@app.route('/delete')
def delete_file():
    filename = request.args.get("file")
    path = os.path.join(record_dir, filename)
    if os.path.exists(path):
        os.remove(path)
        return f"Deleted {filename}", 200
    return "File not found", 404

@app.route('/recordings/<path:filename>')
def serve_recording(filename):
    return send_from_directory(record_dir, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
