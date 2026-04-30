from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restx import Resource

from src.api.auth import auth_ns
from src.api.tasks import tasks_ns
from src.config import get_settings
from src.extensions import api, db, jwt


def create_app() -> Flask:
    settings = get_settings()
    app = Flask(__name__)
    app.config["ENV"] = settings.app_env
    app.config["DEBUG"] = settings.app_debug
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["JWT_SECRET_KEY"] = settings.jwt_secret_key
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    api.init_app(app)
    jwt.init_app(app)
    _register_routes()
    _register_error_handlers(cast_jwt_manager=jwt)
    return app


def _register_routes() -> None:
    @api.route("/health")
    class HealthResource(Resource):
        def get(self) -> tuple[dict[str, str], int]:
            return {"status": "ok"}, 200

    existing_namespaces = {namespace.name for namespace in api.namespaces}
    if auth_ns.name not in existing_namespaces:
        api.add_namespace(auth_ns, path="/auth")
    if tasks_ns.name not in existing_namespaces:
        api.add_namespace(tasks_ns, path="/tasks")


def _register_error_handlers(cast_jwt_manager: JWTManager) -> None:
    @cast_jwt_manager.unauthorized_loader
    def unauthorized_callback(message: str) -> tuple[dict[str, str], int]:
        return {"message": message}, 401

    @cast_jwt_manager.invalid_token_loader
    def invalid_token_callback(message: str) -> tuple[dict[str, str], int]:
        return {"message": message}, 401
