from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

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
