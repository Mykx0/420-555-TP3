from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_vite import Vite
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import jsonBD 

app = Flask(__name__)
vite = Vite(app)
app.config['JWT_SECRET_KEY'] = 'your_super_secret_key'  # Change in production
jwt = JWTManager(app)
CORS(app)

@app.route("/api/health")
def health():
    return jsonify({"message": "Backend is healthy!"})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    print(email,password)
    
    if email is None or password is None: 
        return jsonify({"msg": "invalid form"}), 400
    
    if not jsonBD.put(email, password):
        return jsonify({"msg": "email already in use"}), 409
    
    return jsonify({"token": create_access_token(identity=email)}), 200
    

def start():
    print("Starting web server")
    app.run(port=8080, host='0.0.0.0', debug=True)
    print("Server has finished loading")
