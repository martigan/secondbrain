from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import and_, or_

from src.api.pagination import TaskCursor
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
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db.session.add(task)
        db.session.commit()
        return task

    @staticmethod
    def list_by_user_paginated(
        user_id: UUID, limit: int, cursor: TaskCursor | None
    ) -> tuple[list[Task], bool]:
        query = Task.query.filter_by(created_by_id=user_id)
        if cursor is not None:
            query = query.filter(
                or_(
                    Task.created_at < cursor.created_at,
                    and_(Task.created_at == cursor.created_at, Task.id < cursor.id),
                )
            )

        rows = (
            query.order_by(Task.created_at.desc(), Task.id.desc())
            .limit(limit + 1)
            .all()
        )
        has_next = len(rows) > limit
        return rows[:limit], has_next

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
