from flask import Flask, jsonify
from flask_cors import CORS
from flask_vite import Vite

app = Flask(__name__)
vite = Vite(app)
CORS(app)

@app.route("/api/health")
def health():
    return jsonify({"message": "Backend is healthy!"})

def start():
    print("Starting web server")
    app.run(port=8080, host='0.0.0.0', debug=True)
    print("Server has finished loading")
