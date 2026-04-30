from dataclasses import dataclass
from enum import StrEnum


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class SortField(StrEnum):
    CREATED_AT = "created_at"
    DUE_DATE = "due_date"
    STATUS = "status"


@dataclass(frozen=True)
class TaskSortSpec:
    field: SortField
    direction: SortDirection


class InvalidTaskSortError(ValueError):
    pass


def parse_task_sort(raw_sort: str | None) -> list[TaskSortSpec]:
    if raw_sort is None:
        return [TaskSortSpec(field=SortField.CREATED_AT, direction=SortDirection.DESC)]

    entries = [entry.strip() for entry in raw_sort.split(",") if entry.strip()]
    if not entries:
        raise InvalidTaskSortError("sort cannot be empty")

    specs: list[TaskSortSpec] = []
    seen_fields: set[SortField] = set()
    for entry in entries:
        if ":" not in entry:
            raise InvalidTaskSortError("Each sort entry must be in field:direction format")
        field_raw, direction_raw = entry.split(":", 1)
        try:
            field = SortField(field_raw.strip())
        except ValueError as exc:
            raise InvalidTaskSortError(f"Unsupported sort field: '{field_raw.strip()}'") from exc
        try:
            direction = SortDirection(direction_raw.strip())
        except ValueError as exc:
            invalid_direction = direction_raw.strip()
            raise InvalidTaskSortError(
                f"Invalid sort direction: '{invalid_direction}'"
            ) from exc
        if field in seen_fields:
            raise InvalidTaskSortError(f"Duplicate sort field: '{field.value}'")
        seen_fields.add(field)
        specs.append(TaskSortSpec(field=field, direction=direction))
    return specs


def canonical_task_sort(specs: list[TaskSortSpec]) -> str:
    return ",".join(f"{spec.field.value}:{spec.direction.value}" for spec in specs)
