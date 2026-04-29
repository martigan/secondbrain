from src.domain.models.task import TaskStatus


class InvalidTaskTransitionError(ValueError):
    def __init__(self, from_status: TaskStatus, to_status: TaskStatus) -> None:
        super().__init__(f"Invalid transition from '{from_status.value}' to '{to_status.value}'")
        self.from_status = from_status
        self.to_status = to_status


class TaskStateMachine:
    _allowed_transitions: dict[TaskStatus, set[TaskStatus]] = {
        TaskStatus.NEW: {TaskStatus.RUNNING},
        TaskStatus.RUNNING: {TaskStatus.COMPLETE, TaskStatus.ERROR, TaskStatus.PAUSE},
        TaskStatus.PAUSE: {TaskStatus.RUNNING},
        TaskStatus.COMPLETE: set(),
        TaskStatus.ERROR: set(),
    }

    @classmethod
    def can_transition(cls, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        return to_status in cls._allowed_transitions[from_status]

    @classmethod
    def assert_transition(cls, from_status: TaskStatus, to_status: TaskStatus) -> None:
        if from_status == to_status:
            return
        if not cls.can_transition(from_status=from_status, to_status=to_status):
            raise InvalidTaskTransitionError(from_status=from_status, to_status=to_status)
