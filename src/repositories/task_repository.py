from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.sql.elements import ColumnElement

from src.api.pagination import TaskCursor
from src.api.task_filters import TaskListFilters
from src.api.task_sorting import SortDirection, SortField, TaskSortSpec
from src.domain.models.task import Task, TaskStatus
from src.extensions import db


class TaskRepository:
    @staticmethod
    def _column_for_sort_field(field: SortField):
        if field == SortField.CREATED_AT:
            return Task.created_at
        if field == SortField.DUE_DATE:
            return Task.due_date
        if field == SortField.STATUS:
            return Task.status
        raise ValueError("Unsupported sort field")

    @classmethod
    def _order_clauses(cls, sort_specs: list[TaskSortSpec]):
        clauses = []
        for spec in sort_specs:
            column = cls._column_for_sort_field(spec.field)
            clauses.append(column.asc() if spec.direction == SortDirection.ASC else column.desc())
        clauses.append(Task.id.desc())
        return clauses

    @classmethod
    def _cursor_value(cls, cursor: TaskCursor, spec: TaskSortSpec):
        raw = cursor.values[spec.field.value]
        if spec.field == SortField.CREATED_AT:
            return datetime.fromisoformat(raw)
        if spec.field == SortField.DUE_DATE:
            return date.fromisoformat(raw)
        if spec.field == SortField.STATUS:
            return TaskStatus(raw)
        raise ValueError("Unsupported sort field")

    @classmethod
    def _cursor_predicate(
        cls, cursor: TaskCursor, sort_specs: list[TaskSortSpec]
    ) -> ColumnElement[bool]:
        conditions: list[ColumnElement[bool]] = []
        for index, spec in enumerate(sort_specs):
            prefix_equals: list[ColumnElement[bool]] = []
            for previous in sort_specs[:index]:
                prev_column = cls._column_for_sort_field(previous.field)
                prev_value = cls._cursor_value(cursor, previous)
                prefix_equals.append(prev_column == prev_value)

            column = cls._column_for_sort_field(spec.field)
            value = cls._cursor_value(cursor, spec)
            comparator = column > value if spec.direction == SortDirection.ASC else column < value
            conditions.append(and_(*prefix_equals, comparator))

        id_prefix: list[ColumnElement[bool]] = []
        for previous in sort_specs:
            prev_column = cls._column_for_sort_field(previous.field)
            prev_value = cls._cursor_value(cursor, previous)
            id_prefix.append(prev_column == prev_value)
        conditions.append(and_(*id_prefix, Task.id < UUID(cursor.values["id"])))
        return or_(*conditions)

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
        user_id: UUID,
        limit: int,
        cursor: TaskCursor | None,
        filters: TaskListFilters,
        sort_specs: list[TaskSortSpec],
    ) -> tuple[list[Task], bool]:
        query = Task.query.filter_by(created_by_id=user_id)
        if filters.status_eq is not None:
            query = query.filter(Task.status == filters.status_eq)
        if filters.status_in is not None:
            query = query.filter(Task.status.in_(filters.status_in))
        if filters.due_date_gte is not None:
            query = query.filter(Task.due_date >= filters.due_date_gte)
        if filters.due_date_lte is not None:
            query = query.filter(Task.due_date <= filters.due_date_lte)
        if filters.created_at_gte is not None:
            query = query.filter(Task.created_at >= filters.created_at_gte)
        if filters.created_at_lte is not None:
            query = query.filter(Task.created_at <= filters.created_at_lte)
        if filters.title_contains is not None:
            query = query.filter(Task.title.ilike(f"%{filters.title_contains}%"))

        if cursor is not None:
            query = query.filter(TaskRepository._cursor_predicate(cursor, sort_specs))

        rows = query.order_by(*TaskRepository._order_clauses(sort_specs)).limit(limit + 1).all()
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
