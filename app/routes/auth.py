from flask import Blueprint, request, jsonify, url_for
from flask_jwt_extended import create_access_token
import os
import base64
import logging
from app.config.config import *

auth_bp = Blueprint('auth', __name__)

def generate_verification_token():
    return base64.urlsafe_b64encode(os.urandom(24)).decode('utf-8')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('username')
    username = email[:-10]
    password = data.get('password')

    logging.info(f'Received login request: email={email}')

    user = login_data.find_one({"$or": [{"email": email}, {"username": username}], "verified": True})
    if user and bcrypt.check_password_hash(user['password'], password):
        access_token = create_access_token(identity=str(user['_id']), additional_claims={"username": user['username']})
        return jsonify({'message': 'Successfully logged in!', 'access_token': access_token})
    
    return jsonify({'message': 'Invalid Credentials, please try again!'}), 401

@auth_bp.route('/signup', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    username = email[:-10]

    existing_user = login_data.find_one({"email": email})
    if existing_user and existing_user['verified']:
        return jsonify({'message': 'User already exists'}), 403

    verification_token = generate_verification_token()
    verification_url = url_for('auth.verify_account', email=email, token=verification_token, _external=True)
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    user = {'username': username, 'email': email, 'password': hashed_password, 'name': name,
            'verification_token': verification_token, 'verified': False}

    if existing_user:
        login_data.replace_one({"_id": existing_user['_id']}, user)
    else:
        login_data.insert_one(user)

    # You need to import your email sender here
    # email_sender.send_email(email, verification_url, True)

    return jsonify({'message': 'A verification link has been sent to your email.'}), 200

@auth_bp.route('/signup/verify', methods=['GET'])
def verify_account():
    email = request.args.get('email')
    token = request.args.get('token')

    user = login_data.find_one({"email": email})
    if user:
        if user['verification_token'] == token:
            login_data.update_one({"email": email}, {"$set": {"verified": True}})
            return jsonify({"message": "User verified successfully!"}), 200
        return jsonify({"message": "Invalid token!"}), 400
    
    return jsonify({"message": "User not found"}), 404
