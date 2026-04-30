from src.domain.models.user import User
from src.extensions import db


class UserRepository:
    @staticmethod
    def get_by_email(email: str) -> User | None:
        return User.query.filter_by(email=email).one_or_none()

    @staticmethod
    def create(email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        return user
