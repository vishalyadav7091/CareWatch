from flask import Blueprint, jsonify, request
import bcrypt
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from app.models import User
from app import db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new medical user (Doctor, Nurse, Admin)."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body must be JSON"}), 400

    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "nurse")

    if not full_name or not email or not password:
        return jsonify({
            "success": False,
            "error": "full_name, email, and password are required",
        }), 400

    if role not in ["admin", "doctor", "nurse"]:
        return jsonify({
            "success": False,
            "error": "Invalid role. Must be admin, doctor, or nurse",
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            "success": False,
            "error": "User with this email already exists",
        }), 409

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    user = User(
        full_name=full_name,
        email=email,
        password_hash=hashed,
        role=role,
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "success": True,
        "message": "User registered successfully",
        "token": access_token,
        "user": user.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate staff and return JWT access token."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body must be JSON"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "error": "email and password are required",
        }), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"success": False, "error": "Account is inactive"}), 403

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": access_token,
        "user": user.to_dict(),
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get current authenticated user info."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    return jsonify({
        "success": True,
        "user": user.to_dict(),
    }), 200

