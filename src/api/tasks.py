from typing import Any, cast
from uuid import UUID

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource
from pydantic import ValidationError

from src.api.pagination import (
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


@tasks_ns.route("")
class TaskListResource(Resource):
    @jwt_required()
    def get(self) -> tuple[dict[str, object], int]:
        query_payload = {
            "limit": request.args.get("limit", default=20, type=int),
            "cursor": request.args.get("cursor"),
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

        parsed_cursor: TaskCursor | None = None
        if query_input.cursor is not None:
            try:
                parsed_cursor = decode_task_cursor(query_input.cursor)
            except InvalidCursorError:
                return {"message": "Invalid cursor"}, 400
            if parsed_cursor.query_signature != filters_signature:
                return {"message": "Invalid cursor"}, 400

        tasks, has_next = TaskRepository.list_by_user_paginated(
            user_id=_current_user_id(),
            limit=query_input.limit,
            cursor=parsed_cursor,
            filters=filters,
        )
        next_cursor = None
        if has_next and tasks:
            last_task = tasks[-1]
            next_cursor = encode_task_cursor(
                TaskCursor(
                    created_at=last_task.created_at,
                    id=last_task.id,
                    query_signature=filters_signature,
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
