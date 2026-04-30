import hashlib
import json
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

    def signature_payload(self) -> dict[str, object]:
        return {
            "status_eq": self.status_eq.value if self.status_eq is not None else None,
            "status_in": sorted(status.value for status in self.status_in)
            if self.status_in is not None
            else None,
            "due_date_gte": (
                self.due_date_gte.isoformat()
                if self.due_date_gte is not None
                else None
            ),
            "due_date_lte": (
                self.due_date_lte.isoformat()
                if self.due_date_lte is not None
                else None
            ),
            "created_at_gte": self.created_at_gte.isoformat()
            if self.created_at_gte is not None
            else None,
            "created_at_lte": self.created_at_lte.isoformat()
            if self.created_at_lte is not None
            else None,
            "title_contains": (
                self.title_contains.lower()
                if self.title_contains is not None
                else None
            ),
        }


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


def task_filters_signature(filters: TaskListFilters) -> str:
    payload = filters.signature_payload()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
