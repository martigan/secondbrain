from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from src.domain.models.task import TaskStatus


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TaskCreateInput(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    due_date: date

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value: date) -> date:
        if value <= date.today():
            raise ValueError("due_date must be in the future")
        return value


class TaskUpdateInput(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    due_date: date | None = None
    status: TaskStatus | None = None

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value: date | None) -> date | None:
        if value is not None and value <= date.today():
            raise ValueError("due_date must be in the future")
        return value


class TaskOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    due_date: date
    status: TaskStatus
    created_by_id: UUID


class TaskListQueryInput(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = None
    status_eq: TaskStatus | None = None
    status_in: str | None = None
    due_date_gte: date | None = None
    due_date_lte: date | None = None
    created_at_gte: datetime | None = None
    created_at_lte: datetime | None = None
    title_contains: str | None = None

    @field_validator("title_contains")
    @classmethod
    def normalize_title_contains(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("title_contains cannot be empty")
        return stripped

    @field_validator("created_at_gte", "created_at_lte")
    @classmethod
    def require_timezone_aware_created_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("created_at filters must include timezone (ISO-8601 with offset)")
        return value

    @model_validator(mode="after")
    def validate_ranges_and_conflicts(self) -> "TaskListQueryInput":
        if self.status_eq is not None and self.status_in is not None:
            raise ValueError("status_eq and status_in cannot be used together")
        if self.due_date_gte is not None and self.due_date_lte is not None:
            if self.due_date_gte > self.due_date_lte:
                raise ValueError("due_date_gte cannot be greater than due_date_lte")
        if self.created_at_gte is not None and self.created_at_lte is not None:
            if self.created_at_gte > self.created_at_lte:
                raise ValueError("created_at_gte cannot be greater than created_at_lte")
        return self


class TaskPageOutput(BaseModel):
    limit: int
    has_next: bool
    next_cursor: str | None


class TaskListOutput(BaseModel):
    items: list[TaskOutput]
    page: TaskPageOutput
