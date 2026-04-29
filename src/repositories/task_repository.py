from datetime import date
from uuid import UUID

from src.domain.models.task import Task, TaskStatus
from src.extensions import db


class TaskRepository:
    @staticmethod
    def create(
        title: str,
        description: str,
        due_date: date,
        created_by_id: UUID,
        status: TaskStatus = TaskStatus.NEW,
    ) -> Task:
        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            created_by_id=created_by_id,
            status=status,
        )
        db.session.add(task)
        db.session.commit()
        return task

    @staticmethod
    def list_by_user(user_id: UUID) -> list[Task]:
        return Task.query.filter_by(created_by_id=user_id).order_by(Task.created_at.desc()).all()

    @staticmethod
    def get_by_id_for_user(task_id: UUID, user_id: UUID) -> Task | None:
        return Task.query.filter_by(id=task_id, created_by_id=user_id).one_or_none()

    @staticmethod
    def delete(task: Task) -> None:
        db.session.delete(task)
        db.session.commit()

    @staticmethod
    def save(task: Task) -> Task:
        db.session.add(task)
        db.session.commit()
        return task
