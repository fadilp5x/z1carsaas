from flask import Flask, request, send_file, jsonify
import cv2
import numpy as np
from PIL import Image
import io, os
import requests

app = Flask(__name__)

Z1CARS_LOGO_PATH = "static/z1cars_logo.png"
CANVA_API_KEY = os.getenv("CANVA_API_KEY", "YOUR_CANVA_API_KEY")
CANVA_TEMPLATE_ID = os.getenv("CANVA_TEMPLATE_ID", "YOUR_TEMPLATE_ID")

# --- Number plate masking + logo overlay ---
def process_image(file_stream):
    image = Image.open(file_stream).convert("RGB")
    cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Haar cascade for plate detection
    plate_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_russian_plate_number.xml")
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    plates = plate_cascade.detectMultiScale(gray, 1.1, 4)

    logo = Image.open(Z1CARS_LOGO_PATH).convert("RGBA")
    for (x, y, w, h) in plates:
        resized_logo = logo.resize((w, h))
        image.paste(resized_logo, (x, y), resized_logo)

    return image

# --- Canva integration ---
def push_to_canva(processed_image, car_details):
    buffer = io.BytesIO()
    processed_image.save(buffer, format="PNG")
    buffer.seek(0)

    headers = {"Authorization": f"Bearer {CANVA_API_KEY}"}
    url = f"https://api.canva.com/designs/{CANVA_TEMPLATE_ID}/images"
    files = {"file": ("car.png", buffer, "image/png")}
    data = {"car_details": car_details}

    response = requests.post(url, headers=headers, files=files, data=data)
    return response.json()

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    details = request.form.get("details", "No details")
    processed_image = process_image(file.stream)

    output = io.BytesIO()
    processed_image.save(output, format="PNG")
    output.seek(0)
    return send_file(output, mimetype="image/png", as_attachment=True, download_name="poster.png")

@app.route("/canva", methods=["POST"])
def canva():
    file = request.files["file"]
    details = request.form.get("details", "")
    processed_image = process_image(file.stream)
    response = push_to_canva(processed_image, details)
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
