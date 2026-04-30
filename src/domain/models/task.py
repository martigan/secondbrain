from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.extensions import db


class TaskStatus(StrEnum):
    NEW = "new"
    RUNNING = "running"
    PAUSE = "pause"
    COMPLETE = "complete"
    ERROR = "error"


class Task(db.Model):  # type: ignore[misc]
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_user_created_at_id_desc", "created_by_id", "created_at", "id"),
        Index(
            "ix_tasks_user_status_created_at_id",
            "created_by_id",
            "status",
            "created_at",
            "id",
        ),
        Index(
            "ix_tasks_user_due_date_created_at_id",
            "created_by_id",
            "due_date",
            "created_at",
            "id",
        ),
        Index("ix_tasks_user_due_date_id", "created_by_id", "due_date", "id"),
        Index("ix_tasks_user_status_id", "created_by_id", "status", "id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.NEW
    )
    created_by_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    created_by = relationship("User", back_populates="tasks")
