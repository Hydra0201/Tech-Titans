from flask import Flask, jsonify
app = Flask(__name__)

@app.get("/api/healthz")
def health():
    return jsonify(ok=True)
