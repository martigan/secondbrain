from flask import request
from flask_jwt_extended import create_access_token
from flask_restx import Namespace, Resource
from pydantic import ValidationError
from werkzeug.security import check_password_hash, generate_password_hash

from src.api.schemas import LoginInput, RegisterInput
from src.repositories.user_repository import UserRepository

auth_ns = Namespace("auth", description="Authentication operations")


def _validation_errors(exc: ValidationError) -> list[dict[str, object]]:
    errors = exc.errors()
    for error in errors:
        ctx = error.get("ctx")
        if isinstance(ctx, dict) and "error" in ctx:
            ctx["error"] = str(ctx["error"])
    return errors


@auth_ns.route("/register")
class RegisterResource(Resource):
    def post(self) -> tuple[dict[str, str], int]:
        payload = request.get_json(silent=True) or {}
        try:
            register_input = RegisterInput.model_validate(payload)
        except ValidationError as exc:
            return {"message": "Validation error", "errors": _validation_errors(exc)}, 400

        existing = UserRepository.get_by_email(register_input.email)
        if existing is not None:
            return {"message": "Email already exists"}, 409

        password_hash = generate_password_hash(register_input.password)
        user = UserRepository.create(email=register_input.email, password_hash=password_hash)
        return {"id": str(user.id), "email": user.email}, 201


@auth_ns.route("/login")
class LoginResource(Resource):
    def post(self) -> tuple[dict[str, str], int]:
        payload = request.get_json(silent=True) or {}
        try:
            login_input = LoginInput.model_validate(payload)
        except ValidationError as exc:
            return {"message": "Validation error", "errors": _validation_errors(exc)}, 400

        user = UserRepository.get_by_email(login_input.email)
        if user is None or not check_password_hash(user.password_hash, login_input.password):
            return {"message": "Invalid credentials"}, 401

        token = create_access_token(identity=str(user.id))
        return {"access_token": token}, 200
