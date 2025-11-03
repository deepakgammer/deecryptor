from flask import Flask, request, jsonify, render_template
from cryptography.fernet import Fernet
import os

app = Flask(__name__)

# -----------------------------------------------------
# 1️⃣ Load or create master encryption key
# -----------------------------------------------------
KEY_FILE = "deecryptor_master.key"

if not os.path.exists(KEY_FILE):
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
else:
    with open(KEY_FILE, "rb") as f:
        key = f.read()

fernet = Fernet(key)


# -----------------------------------------------------
# 2️⃣ Routes
# -----------------------------------------------------

@app.route("/")
def landing():
    # Optional: you can make a landing.html later
    return render_template("landing.html")


@app.route("/app")
def tool():
    # Optional: the main encrypt/decrypt UI page
    return render_template("index.html")


# -----------------------------------------------------
# 3️⃣ Encrypt Route (Stateless Encryption)
# -----------------------------------------------------
@app.route("/encrypt", methods=["POST"])
def encrypt():
    msg = request.form.get("message", "").strip()
    if not msg:
        return jsonify({"error": "Message cannot be empty."}), 400

    # Encrypt message using Fernet (AES + HMAC)
    encrypted = fernet.encrypt(msg.encode()).decode()

    return jsonify({
        "status": "success",
        "encrypted_key": encrypted,
        "tip": "Save this key safely — it’s needed to decrypt later!"
    })


# -----------------------------------------------------
# 4️⃣ Decrypt Route (Stateless Decryption)
# -----------------------------------------------------
@app.route("/decrypt", methods=["POST"])
def decrypt():
    token = request.form.get("key", "").strip()
    if not token:
        return jsonify({"error": "Key cannot be empty."}), 400

    try:
        decrypted = fernet.decrypt(token.encode()).decode()
        return jsonify({
            "status": "success",
            "message": decrypted
        })
    except Exception:
        return jsonify({
            "status": "error",
            "error": "Invalid or tampered key. Make sure you’re using the same one returned during encryption."
        }), 400


# -----------------------------------------------------
# 5️⃣ Run App
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
