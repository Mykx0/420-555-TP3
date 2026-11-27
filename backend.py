import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_vite import Vite
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import jsonBD 
import jsonLog

app = Flask(__name__)
vite = Vite(app)
app.config['JWT_SECRET_KEY'] = 'your_super_secret_key'
jwt = JWTManager(app)
CORS(app)

MIN_PIN_LENGTH = 4
MAX_PIN_LENGTH = 6

def valid_length(value, min_len, max_len):
    return min_len <= len(value) <= max_len

def check_login(pin, passcode, source):
    if not isinstance(pin, str) or not isinstance(passcode, str):
        return False

    user = jsonBD.get(pin)
    if user is None or user["passcode"] != passcode:
        jsonLog.warning("login", f"failed attempt for pin {pin} from {source}")
        return False

    return True

@app.route("/api/health")
def health():
    return jsonify({"message": "Backend is healthy!"})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    pin = data.get('pin')
    passcode = data.get('passcode')
    name = data.get('name')
    
    if pin is None or passcode is None or name is None: 
        return jsonify({"msg": "invalid form"}), 400
    
    if not valid_length(pin, MIN_PIN_LENGTH, MAX_PIN_LENGTH):
        return jsonify({"msg": "invalid pin"}), 400
    
    if not valid_length(passcode, MIN_PIN_LENGTH, MAX_PIN_LENGTH):
            return jsonify({"msg": "invalid passcode"}), 400
    
    if not jsonBD.put(pin, name.strip(), passcode):
        jsonLog.warning("register", f"pin {pin} already in use")
        return jsonify({"msg": "pin already in use"}), 409
    
    jsonLog.info("register", f"user created: pin={pin}, name={name.strip()}")
    return jsonify({"token": create_access_token(identity=pin)}), 200
    

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    pin = data.get('pin')
    passcode = data.get('passcode')

    if not isinstance(pin, str) or not isinstance(passcode, str):
        return jsonify({"msg": "invalid form"}), 400

    if not check_login(pin, passcode, request.remote_addr):
        return jsonify({"msg": "invalid credentials"}), 401

    jsonLog.info("web login", f"pin {pin} logged in from {request.remote_addr}")
    return jsonify({"token": create_access_token(identity=pin)}), 200

@app.route("/api/logs")
@jwt_required()
def logs():
    return jsonify(jsonLog.get_all()), 200

def start():
    thread = threading.Thread(
        target=lambda: app.run(
            port=8080,
            host="127.0.0.1",
            debug=False,
            use_reloader=False,
        ),
        daemon=True,
    )
    thread.start()
    print("Web server started on port 8080")

@app.route("/api/change-passcode", methods=["POST"])
@jwt_required()
def change_passcode():
    pin = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    current = data.get("current")
    new = data.get("new")

    if not isinstance(current, str) or not isinstance(new, str):
        return jsonify({"msg": "invalid form"}), 400

    if not (new.isdigit() and MIN_PIN_LENGTH <= len(new) <= MAX_PIN_LENGTH):
        return jsonify({"msg": "new passcode must be 4 to 6 digits"}), 400

    user = jsonBD.get(pin)
    if user is None:
        return jsonify({"msg": "user not found"}), 404

    if user["passcode"] != current:
        jsonLog.warning("passcode", f"pin {pin}: change refused, wrong current passcode")
        return jsonify({"msg": "current passcode is incorrect"}), 403   # not 401, see notes

    if new == current:
        return jsonify({"msg": "new passcode must be different"}), 400

    jsonBD.set_passcode(pin, new)
    jsonLog.info("passcode", f"pin {pin} changed their passcode")
    return jsonify({"msg": "passcode updated"}), 200
