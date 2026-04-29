from enum import Enum


class TaskActionType(str, Enum):
    CREATE = "create"
    LIST = "list"
    UPDATE = "update"
    DELETE = "delete"
    COMPLETE = "complete"
    UNCOMPLETE = "uncomplete"
    SEARCH = "search"
    HELP = "help"
    UNKNOWN = "unknown"
