from flask import Flask, render_template, request, redirect, url_for, Response
import cv2
from ultralytics import YOLO
import numpy as np
from PIL import Image
import io
import base64
import threading

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

confidence_interval = 0.2


def b64encode(data):
    return base64.b64encode(data).decode('utf-8')

app.jinja_env.filters['b64encode'] = b64encode
webcam_active = False
webcam_thread = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global webcam_active
    global webcam_thread

    if webcam_active:
        webcam_active = False
        webcam_thread.join()

    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        img_bytes = file.read()
        img = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(img)

        if img_array.ndim == 2:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        elif img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        model = YOLO("models/model.pt")
        results = model([img_array], conf=confidence_interval)
        try:
            emotion = results[0].names[int(results[0].boxes.cls[0].int())]
        except:
            emotion = "No Emotion Detected!"

        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=70)
        img_io.seek(0)
        img_bytes = img_io.getvalue()

        return render_template('result.html', original_image=img_bytes, emotion=emotion)

def generate_frames():
    global webcam_active
    cap = cv2.VideoCapture(0)
    while webcam_active:
        success, frame = cap.read()
        if not success:
            break
        else:
            model = YOLO("models/model.pt")
            results = model.track(frame, persist=True, conf=confidence_interval)
            annotated_frame = results[0].plot()
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_webcam')
def start_webcam():
    global webcam_active
    global webcam_thread

    if not webcam_active:
        webcam_active = True
        webcam_thread = threading.Thread(target=generate_frames)
        webcam_thread.start()
    return "Webcam started"

@app.route('/stop_webcam')
def stop_webcam():
    global webcam_active
    global webcam_thread

    if webcam_active:
        webcam_active = False
        webcam_thread.join()
    return "Webcam stopped"

if __name__ == '__main__':
    app.run(debug=True)