from flask import Flask, request, send_file, jsonify, render_template
from PIL import Image
import numpy as np
import io

app = Flask(__name__)

# ---------------- Step 1: Text ↔ Undefined Language ---------------- #
def text_to_undefined(msg: str) -> str:
    gibberish = []
    for c in msg.encode("utf-8"):
        gibberish.append(chr(0xE000 + (c % 6400)))  # U+E000–U+F8FF private area
    return "".join(gibberish)

def undefined_to_text(undef: str) -> str:
    vals = [(ord(c) - 0xE000) % 256 for c in undef]
    return bytes(vals).decode("utf-8", errors="ignore")

# ---------------- Step 2: Undefined ↔ PNG Image ---------------- #
def undefined_to_image(undef: str) -> bytes:
    data = [ord(c) % 256 for c in undef]
    size = int(len(data) ** 0.5) + 1
    arr = np.zeros((size, size, 3), dtype=np.uint8)

    for i, val in enumerate(data):
        x, y = divmod(i, size)
        arr[x, y] = [val, (val * 2) % 256, (val * 3) % 256]

    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def image_to_undefined(png_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(png_bytes))
    arr = np.array(img)
    vals = [int(p[0]) for row in arr for p in row]
    undef = "".join(chr(0xE000 + (v % 6400)) for v in vals if v != 0)
    return undef

# ---------------- Step 3: PNG ↔ JPEG ---------------- #
def image_to_jpeg(img_bytes: bytes) -> bytes:
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    size = int(len(arr) ** 0.5) + 1
    img = np.zeros((size, size), dtype=np.uint8)
    img.flat[:len(arr)] = arr
    image = Image.fromarray(img, "L")
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()

def jpeg_to_image(jpeg_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(jpeg_bytes)).convert("L")
    arr = np.array(img).flatten()
    return arr.tobytes()

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
    undef = text_to_undefined(msg)
    img = undefined_to_image(undef)      # PNG bytes
    jpeg = image_to_jpeg(img)            # convert to JPEG
    return send_file(io.BytesIO(jpeg), mimetype="image/jpeg",
                     as_attachment=True, download_name="encrypted.jpeg")

@app.route("/decrypt", methods=["POST"])
def decrypt():
    file = request.files["file"]
    jpeg_bytes = file.read()
    img_bytes = jpeg_to_image(jpeg_bytes)   # back to PNG bytes
    undef = image_to_undefined(img_bytes)   # PNG → Undefined
    text = undefined_to_text(undef)         # Undefined → Text
    return jsonify({"message": text})

if __name__ == "__main__":
    app.run(debug=True)
