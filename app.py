from flask import Flask, request, send_file, jsonify, render_template
from PIL import Image
import numpy as np
import io

app = Flask(__name__)

# ---------------- Step 1: Text ↔ Bytes ---------------- #
def text_to_bytes(msg: str) -> bytes:
    return msg.encode("utf-8")

def bytes_to_text(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")

# ---------------- Step 2: Bytes ↔ PNG ---------------- #
def bytes_to_png(data: bytes) -> bytes:
    arr = np.frombuffer(data, dtype=np.uint8)
    size = int(len(arr) ** 0.5) + 1
    img = np.zeros((size, size), dtype=np.uint8)
    img.flat[:len(arr)] = arr
    image = Image.fromarray(img, "L")  # grayscale
    buf = io.BytesIO()
    image.save(buf, format="PNG")      # lossless
    return buf.getvalue()

def png_to_bytes(png_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(png_bytes)).convert("L")
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
    data = text_to_bytes(msg)
    png = bytes_to_png(data)
    return send_file(io.BytesIO(png), mimetype="image/png",
                     as_attachment=True, download_name="encrypted.png")

@app.route("/decrypt", methods=["POST"])
def decrypt():
    file = request.files["file"]
    png_bytes = file.read()
    data = png_to_bytes(png_bytes)
    text = bytes_to_text(data)
    return jsonify({"message": text})

if __name__ == "__main__":
    app.run(debug=True)
