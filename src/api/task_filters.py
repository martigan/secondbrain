from dataclasses import dataclass
from datetime import date, datetime

from src.api.schemas import TaskListQueryInput
from src.domain.models.task import TaskStatus


class InvalidTaskFilterError(ValueError):
    pass


@dataclass(frozen=True)
class TaskListFilters:
    status_eq: TaskStatus | None
    status_in: list[TaskStatus] | None
    due_date_gte: date | None
    due_date_lte: date | None
    created_at_gte: datetime | None
    created_at_lte: datetime | None
    title_contains: str | None


def _parse_status_in(raw: str | None) -> list[TaskStatus] | None:
    if raw is None:
        return None
    parts = [item.strip() for item in raw.split(",") if item.strip()]
    if not parts:
        raise InvalidTaskFilterError("status_in cannot be empty")
    statuses: list[TaskStatus] = []
    for part in parts:
        try:
            statuses.append(TaskStatus(part))
        except ValueError as exc:
            raise InvalidTaskFilterError(f"Invalid status in status_in: '{part}'") from exc
    return statuses


def build_task_list_filters(query: TaskListQueryInput) -> TaskListFilters:
    return TaskListFilters(
        status_eq=query.status_eq,
        status_in=_parse_status_in(query.status_in),
        due_date_gte=query.due_date_gte,
        due_date_lte=query.due_date_lte,
        created_at_gte=query.created_at_gte,
        created_at_lte=query.created_at_lte,
        title_contains=query.title_contains,
    )
