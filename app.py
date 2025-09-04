from flask import Flask, request, send_file, jsonify, render_template
from PIL import Image
import numpy as np
import io
import wave

app = Flask(__name__)

# ---------------- Core Functions ---------------- #
def text_to_undefined(msg: str) -> str:
    gibberish = []
    for c in msg.encode("utf-8"):
        gibberish.append(chr(0xE000 + (c % 6400)))
    return "".join(gibberish)

def undefined_to_text(undef: str) -> str:
    vals = [(ord(c) - 0xE000) % 256 for c in undef]
    return bytes(vals).decode("utf-8", errors="ignore")

def undefined_to_image(undef: str) -> bytes:
    data = [ord(c) % 256 for c in undef]
    size = int(len(data) ** 0.5) + 1
    arr = np.zeros((size, size, 3), dtype=np.uint8)
    for i, val in enumerate(data):
        x, y = divmod(i, size)
        arr[x, y] = [val, (val * 2) % 256, (val * 3) % 256]
    from PIL import Image
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

def image_to_audio(img_bytes: bytes) -> bytes:
    samples = bytearray(img_bytes)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(1)
        wf.setframerate(8000)
        wf.writeframes(bytes(samples))
    return buf.getvalue()

def audio_to_image(audio_bytes: bytes) -> bytes:
    buf = io.BytesIO(audio_bytes)
    with wave.open(buf, "rb") as wf:
        raw = wf.readframes(wf.getnframes())
    return bytes(raw)

# ---------------- Routes ---------------- #
@app.route("/")
def landing():
    return render_template("landing.html")   # Landing page

@app.route("/app")
def home():
    return render_template("index.html")     # The tool

@app.route("/encrypt", methods=["POST"])
def encrypt():
    msg = request.form["message"]
    undef = text_to_undefined(msg)
    img = undefined_to_image(undef)
    wav = image_to_audio(img)
    return send_file(io.BytesIO(wav), mimetype="audio/wav",
                     as_attachment=True, download_name="encrypted.wav")

@app.route("/decrypt", methods=["POST"])
def decrypt():
    file = request.files["file"]
    audio_bytes = file.read()
    img = audio_to_image(audio_bytes)
    undef = image_to_undefined(img)
    text = undefined_to_text(undef)
    return jsonify({"message": text})

if __name__ == "__main__":
    app.run(debug=True)
