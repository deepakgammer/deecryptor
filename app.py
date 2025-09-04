from flask import Flask, request, send_file, jsonify, render_template
from PIL import Image
import numpy as np
import io

app = Flask(__name__)

# ---------------- Step 1: Text ↔ Undefined Language ---------------- #
def text_to_undefined(msg: str) -> bytes:
    data = [c for c in msg.encode("utf-8")]
    return bytes(data)

def undefined_to_text(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")

# ---------------- Step 2: Bytes ↔ JPEG ---------------- #
def bytes_to_jpeg(data: bytes) -> bytes:
    arr = np.frombuffer(data, dtype=np.uint8)
    size = int(len(arr) ** 0.5) + 1
    img = np.zeros((size, size), dtype=np.uint8)
    img.flat[:len(arr)] = arr
    image = Image.fromarray(img, "L")  # Grayscale
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()

def jpeg_to_bytes(jpeg_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(jpeg_bytes)).convert("L")
    arr = np.array(img).flatten()
    return bytes(arr)

# ---------------- Flask Routes ---------------- #
@app.route("/")
def landing():
    return render_template("landing.html")   # Landing page

@app.route("/app")
def tool():
    return render_template("index.html")     # Tool page

@app.route("/encrypt", methods=["POST"])
def encrypt():
    msg = request.form["message"]
    data = text_to_undefined(msg)
    jpeg = bytes_to_jpeg(data)
    return send_file(io.BytesIO(jpeg), mimetype="image/jpeg",
                     as_attachment=True, download_name="encrypted.jpeg")

@app.route("/decrypt", methods=["POST"])
def decrypt():
    file = request.files["file"]
    jpeg_bytes = file.read()
    data = jpeg_to_bytes(jpeg_bytes)
    text = undefined_to_text(data)
    return jsonify({"message": text})

if __name__ == "__main__":
    app.run(debug=True)
