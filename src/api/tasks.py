from uuid import UUID

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource
from pydantic import ValidationError

from src.api.schemas import TaskCreateInput, TaskOutput, TaskUpdateInput
from src.domain.services.task_state_machine import InvalidTaskTransitionError, TaskStateMachine
from src.repositories.task_repository import TaskRepository

tasks_ns = Namespace("tasks", description="Task operations")


def _validation_errors(exc: ValidationError) -> list[dict[str, object]]:
    errors = exc.errors()
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
    def get(self) -> tuple[list[dict[str, str]], int]:
        tasks = TaskRepository.list_by_user(_current_user_id())
        return [TaskOutput.model_validate(task).model_dump(mode="json") for task in tasks], 200

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
