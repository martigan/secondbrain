import base64
import json
from dataclasses import dataclass
from typing import NotRequired, Required, TypedDict, cast


class CursorValues(TypedDict, total=False):
    id: Required[str]
    created_at: NotRequired[str]
    due_date: NotRequired[str]
    status: NotRequired[str]


class InvalidCursorError(ValueError):
    pass


@dataclass(frozen=True)
class TaskCursor:
    sort: str
    values: CursorValues
    query_signature: str


def encode_task_cursor(cursor: TaskCursor) -> str:
    payload = {
        "sort": cursor.sort,
        "values": cursor.values,
        "query_signature": cursor.query_signature,
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    return encoded.rstrip("=")


def decode_task_cursor(cursor: str) -> TaskCursor:
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode((cursor + padding).encode("utf-8")).decode("utf-8")
        payload = json.loads(raw)
        sort = str(payload["sort"])
        values = payload["values"]
        if not isinstance(values, dict):
            raise ValueError("Invalid cursor values")
        normalized_values = cast(
            CursorValues, {str(key): str(value) for key, value in values.items()}
        )
        if "id" not in normalized_values:
            raise ValueError("Cursor values must include id")
        query_signature = str(payload["query_signature"])
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise InvalidCursorError("Invalid cursor") from exc

    return TaskCursor(sort=sort, values=normalized_values, query_signature=query_signature)
