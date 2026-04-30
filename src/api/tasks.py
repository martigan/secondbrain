import hashlib
from typing import Any, cast
from uuid import UUID

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource
from pydantic import ValidationError

from src.api.pagination import (
    CursorValues,
    InvalidCursorError,
    TaskCursor,
    decode_task_cursor,
    encode_task_cursor,
)
from src.api.schemas import (
    TaskCreateInput,
    TaskListOutput,
    TaskListQueryInput,
    TaskOutput,
    TaskPageOutput,
    TaskUpdateInput,
)
from src.api.task_filters import (
    InvalidTaskFilterError,
    build_task_list_filters,
    task_filters_signature,
)
from src.api.task_sorting import (
    InvalidTaskSortError,
    TaskSortSpec,
    canonical_task_sort,
    parse_task_sort,
)
from src.domain.models.task import Task
from src.domain.services.task_state_machine import InvalidTaskTransitionError, TaskStateMachine
from src.repositories.task_repository import TaskRepository

tasks_ns = Namespace("tasks", description="Task operations")


def _validation_errors(exc: ValidationError) -> list[dict[str, object]]:
    errors = cast(list[dict[str, Any]], exc.errors())
    for error in errors:
        ctx = error.get("ctx")
        if isinstance(ctx, dict) and "error" in ctx:
            ctx["error"] = str(ctx["error"])
    return errors


def _current_user_id() -> UUID:
    return UUID(get_jwt_identity())


def _build_query_signature(filter_signature: str, sort_signature: str) -> str:
    canonical = f"{filter_signature}|{sort_signature}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _cursor_value_for_field(task: Task, spec: TaskSortSpec) -> str:
    if spec.field.value == "created_at":
        return task.created_at.isoformat()
    if spec.field.value == "due_date":
        return task.due_date.isoformat()
    if spec.field.value == "status":
        return task.status.value
    raise ValueError("Unsupported sort field")


@tasks_ns.route("")
class TaskListResource(Resource):
    @jwt_required()
    def get(self) -> tuple[dict[str, object], int]:
        query_payload = {
            "limit": request.args.get("limit", default=20, type=int),
            "cursor": request.args.get("cursor"),
            "sort": request.args.get("sort"),
            "status_eq": request.args.get("status_eq"),
            "status_in": request.args.get("status_in"),
            "due_date_gte": request.args.get("due_date_gte"),
            "due_date_lte": request.args.get("due_date_lte"),
            "created_at_gte": request.args.get("created_at_gte"),
            "created_at_lte": request.args.get("created_at_lte"),
            "title_contains": request.args.get("title_contains"),
        }
        try:
            query_input = TaskListQueryInput.model_validate(query_payload)
        except ValidationError as exc:
            return {"message": "Validation error", "errors": _validation_errors(exc)}, 400
        try:
            filters = build_task_list_filters(query_input)
        except InvalidTaskFilterError as exc:
            return {"message": "Validation error", "errors": [{"msg": str(exc)}]}, 400
        filters_signature = task_filters_signature(filters)
        try:
            sort_specs = parse_task_sort(query_input.sort)
        except InvalidTaskSortError as exc:
            return {"message": "Validation error", "errors": [{"msg": str(exc)}]}, 400
        sort_signature = canonical_task_sort(sort_specs)
        query_signature = _build_query_signature(filters_signature, sort_signature)

        parsed_cursor: TaskCursor | None = None
        if query_input.cursor is not None:
            try:
                parsed_cursor = decode_task_cursor(query_input.cursor)
            except InvalidCursorError:
                return {"message": "Invalid cursor"}, 400
            if parsed_cursor.query_signature != query_signature:
                return {"message": "Invalid cursor"}, 400
            if parsed_cursor.sort != sort_signature:
                return {"message": "Invalid cursor"}, 400

        tasks, has_next = TaskRepository.list_by_user_paginated(
            user_id=_current_user_id(),
            limit=query_input.limit,
            cursor=parsed_cursor,
            filters=filters,
            sort_specs=sort_specs,
        )
        next_cursor = None
        if has_next and tasks:
            last_task = tasks[-1]
            cursor_values = cast(
                CursorValues,
                {
                    spec.field.value: _cursor_value_for_field(last_task, spec)
                    for spec in sort_specs
                },
            )
            cursor_values["id"] = str(last_task.id)
            next_cursor = encode_task_cursor(
                TaskCursor(
                    sort=sort_signature,
                    values=cursor_values,
                    query_signature=query_signature,
                )
            )

        response_payload = TaskListOutput(
            items=[TaskOutput.model_validate(task) for task in tasks],
            page=TaskPageOutput(
                limit=query_input.limit,
                has_next=has_next,
                next_cursor=next_cursor,
            ),
        )
        return response_payload.model_dump(mode="json"), 200

    @jwt_required()
    def post(self) -> tuple[dict[str, str], int]:
        payload = request.get_json(silent=True) or {}
        try:
            task_input = TaskCreateInput.model_validate(payload)
        except ValidationError as exc:
            return {"message": "Validation error", "errors": _validation_errors(exc)}, 400

        task = TaskRepository.create(
            title=task_input.title,
            description=task_input.description,
            due_date=task_input.due_date,
            created_by_id=_current_user_id(),
        )
        return TaskOutput.model_validate(task).model_dump(mode="json"), 201


@tasks_ns.route("/<string:task_id>")
class TaskResource(Resource):
    @staticmethod
    def _parse_task_id(task_id: str) -> UUID | None:
        try:
            return UUID(task_id)
        except ValueError:
            return None

    @jwt_required()
    def get(self, task_id: str) -> tuple[dict[str, str], int]:
        parsed_id = self._parse_task_id(task_id)
        if parsed_id is None:
            return {"message": "Invalid task id"}, 400
        task = TaskRepository.get_by_id_for_user(task_id=parsed_id, user_id=_current_user_id())
        if task is None:
            return {"message": "Task not found"}, 404
        return TaskOutput.model_validate(task).model_dump(mode="json"), 200

    @jwt_required()
    def put(self, task_id: str) -> tuple[dict[str, str], int]:
        parsed_id = self._parse_task_id(task_id)
        if parsed_id is None:
            return {"message": "Invalid task id"}, 400
        task = TaskRepository.get_by_id_for_user(task_id=parsed_id, user_id=_current_user_id())
        if task is None:
            return {"message": "Task not found"}, 404

        payload = request.get_json(silent=True) or {}
        try:
            task_input = TaskUpdateInput.model_validate(payload)
        except ValidationError as exc:
            return {"message": "Validation error", "errors": _validation_errors(exc)}, 400

        update_data = task_input.model_dump(exclude_none=True)
        if "status" in update_data:
            try:
                TaskStateMachine.assert_transition(task.status, update_data["status"])
            except InvalidTaskTransitionError as exc:
                return {"message": str(exc)}, 409

        for key, value in update_data.items():
            setattr(task, key, value)

        TaskRepository.save(task)
        return TaskOutput.model_validate(task).model_dump(mode="json"), 200

    @jwt_required()
    def delete(self, task_id: str) -> tuple[dict[str, str], int]:
        parsed_id = self._parse_task_id(task_id)
        if parsed_id is None:
            return {"message": "Invalid task id"}, 400
        task = TaskRepository.get_by_id_for_user(task_id=parsed_id, user_id=_current_user_id())
        if task is None:
            return {"message": "Task not found"}, 404
        TaskRepository.delete(task)
        return {"message": "Task deleted"}, 200
