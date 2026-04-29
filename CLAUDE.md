# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the app
python app.py

# Install dependencies
pip install -r requirements.txt

# Test LLM/DeepSeek API connectivity
python scripts/test_model_connection.py
```

No test suite or linter is configured.

## Architecture

This is a Flet-based desktop todo app with AI-powered natural language task management (Chinese-first UI). The stack is:

```
ui/views/todo_view.py  (TodoApp — main view, owns all state)
    ├── services/llm_service.py   (LangChain + DeepSeek API → TaskPlan)
    │   └── services/task_service.py  (business logic, date resolution)
    │       └── storage/task_repo.py  (CRUD against SQLite)
    │           └── storage/db.py     (connection + schema init)
    └── ui/components/task_item.py    (per-task row widget)
```

**Key data flow:** User message → `LLMService.plan()` → `TaskPlan` (Pydantic) → `LLMService.process()` → `TaskService` → `TaskRepository` → `data/tasks.db`. The UI reloads the full task list after every mutation.

**Deletion confirmation:** `LLMService` stores a pending action keyed by a UUID token. The UI renders a confirm button; calling `LLMService.confirm_delete(token)` executes it. This is the only multi-step flow.

**Undo:** `TodoApp` keeps a list of up to 20 task-list snapshots and restores them on undo — no DB-level rollback.

## Key files

| File | Role |
|---|---|
| [app.py](app.py) | Entry point — initializes Flet, sets theme font, calls `ft.app(target=main)` |
| [core/models/task.py](core/models/task.py) | `TaskRecord` dataclass; `from_row()` / `to_db_values()` for DB ↔ model conversion |
| [core/constants/enums.py](core/constants/enums.py) | `TaskActionType` enum (CREATE, LIST, UPDATE, DELETE, COMPLETE, UNCOMPLETE, SEARCH, HELP, UNKNOWN) |
| [services/llm_service.py](services/llm_service.py) | LangChain `ChatOpenAI` wrapper; system prompt in Chinese; `TaskPlan` Pydantic model for structured LLM output |
| [services/nlp_task_parser.py](services/nlp_task_parser.py) | Regex/keyword fallback parser for when LLM is unavailable |
| [services/task_service.py](services/task_service.py) | Date resolution (今天/明天/后天 → ISO), batch task creation, filter/search logic |
| [storage/db.py](storage/db.py) | SQLite connection with row factory; auto-creates `data/` dir and `tasks` table |
| [ui/theme.py](ui/theme.py) | Sets Microsoft YaHei font globally for CJK support |
| [ui/views/todo_view.py](ui/views/todo_view.py) | Two-panel layout (AI chat left, task list right) with resizable splitter |
| [ui/components/task_item.py](ui/components/task_item.py) | Task row: display/edit toggle, date emoji + color coding, checkbox |

## Environment

API credentials live in `.env` (not committed). Required keys:

```
OPENAI_API_KEY=<deepseek key>
OPENAI_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com/
OPENAI_TEMPERATURE=0.3
```

The app uses the OpenAI-compatible DeepSeek endpoint via LangChain's `ChatOpenAI`. Temperature 0.3 is used for task planning; 0.4 for freeform chat responses.

## UI conventions

- `TaskItem` extends `ft.Column` and manages its own display/edit state internally via `self.display_view` / `self.edit_view`.
- Date color coding: blue = future, orange = today, grey = past.
- The splitter in `TodoView` is a draggable `ft.GestureDetector` that adjusts `left_panel_width` and calls `page.update()`.
- Many UI files under `ui/components/` and `ui/views/` are empty stubs reserved for future features (calendar, settings, etc.).
