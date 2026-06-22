from flask import Blueprint, request, jsonify
from sqlalchemy import Identity
from werkzeug.security import check_password_hash, generate_password_hash
import validators
from src.database import User, db
from flask_jwt_extended import (
    get_jwt,
    jwt_required,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
)
from src.constants.http_status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_409_CONFLICT,
)
from flasgger import swag_from

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth.post("/register")
@swag_from("./docs/auth/register.yaml")
def register():
    # Use .get() to avoid KeyErrors if fields are missing in JSON
    username = request.json.get("username", "").strip()
    email = request.json.get("email", "").strip()
    password = request.json.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), HTTP_400_BAD_REQUEST

    if len(password) < 6:
        return jsonify({"error": "Password is too short"}), HTTP_400_BAD_REQUEST

    if len(username) < 3:
        return jsonify({"error": "Username is too short"}), HTTP_400_BAD_REQUEST

    if not username.isalnum():
        return (
            jsonify({"error": "Username should be alphanumeric without spaces"}),
            HTTP_400_BAD_REQUEST,
        )

    if not validators.email(email):
        return jsonify({"error": "Email is not valid"}), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"error": "Email is taken"}), HTTP_409_CONFLICT

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"error": "Username is taken"}), HTTP_409_CONFLICT

    pwd_hash = generate_password_hash(password)

    user = User(username=username, password=pwd_hash, email=email)
    db.session.add(user)
    db.session.commit()

    return (
        jsonify(
            {"message": "User Created", "user": {"username": username, "email": email}}
        ),
        HTTP_201_CREATED,
    )


@auth.post("/login")
@swag_from("./docs/auth/login.yaml")
def login():
    email = request.json.get("email", "").strip()
    password = request.json.get("password", "")

    user = User.query.filter_by(email=email).first()

    # FIX: Check credentials safely and handle non-existent users
    if user and check_password_hash(user.password, password):
        # Convert user.id to string as modern JWT managers require string identities
        refresh = create_refresh_token(identity=str(user.id))
        access = create_access_token(identity=str(user.id))

        return (
            jsonify(
                {
                    "user": {
                        "refresh": refresh,
                        "access": access,
                        "username": user.username,
                        "email": user.email,
                    }
                }
            ),
            HTTP_200_OK,
        )

    # FIX: This now catches BOTH wrong password AND wrong email
    return jsonify({"error": "Wrong Credentials"}), HTTP_401_UNAUTHORIZED


@auth.get("/me")
@jwt_required()
def me():
    # Fetch identity securely from the token validation layer
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), HTTP_401_UNAUTHORIZED

    return jsonify({"username": user.username, "email": user.email}), HTTP_200_OK


# Creating the Refreshing Token
@auth.post("/token/refresh")
@jwt_required(refresh=True)
def refresh_users_token():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)

    return jsonify({"access": access}), HTTP_200_OK
