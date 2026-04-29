import base64
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


class InvalidCursorError(ValueError):
    pass


@dataclass(frozen=True)
class TaskCursor:
    created_at: datetime
    id: UUID


def encode_task_cursor(cursor: TaskCursor) -> str:
    payload = {
        "created_at": cursor.created_at.isoformat(),
        "id": str(cursor.id),
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    return encoded.rstrip("=")


def decode_task_cursor(cursor: str) -> TaskCursor:
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode((cursor + padding).encode("utf-8")).decode("utf-8")
        payload = json.loads(raw)
        created_at = datetime.fromisoformat(payload["created_at"])
        task_id = UUID(payload["id"])
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise InvalidCursorError("Invalid cursor") from exc

    return TaskCursor(created_at=created_at, id=task_id)
