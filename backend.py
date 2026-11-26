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

    user = jsonBD.get(pin)
    if user is None or not (user["passcode"] == passcode):
        jsonLog.warning("login", f"failed attempt for pin {pin} from {request.remote_addr}")
        return jsonify({"msg": "invalid credentials"}), 401

    jsonLog.info("login", f"pin {pin} logged in")
    return jsonify({"token": create_access_token(identity=pin)}), 200

@app.route("/api/logs")
@jwt_required()
def logs():
    return jsonify(jsonLog.get_all()), 200

def start():
    print("Starting web server")
    app.run(port=8080, host='0.0.0.0', debug=True)
    print("Server has finished loading")
