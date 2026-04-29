from flask_jwt_extended import JWTManager
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()
api = Api(
    title="Task Management API",
    version="1.0",
    doc="/docs",
    validate=True,
)
