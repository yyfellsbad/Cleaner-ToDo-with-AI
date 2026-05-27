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

**LLM memory:** `LLMService` maintains a conversation memory (last 10 turns) persisted to the `settings` table as JSON (`"llm_memory"` key) via `SettingRepo`. Loaded on startup, saved after every exchange.

**Deletion confirmation:** `LLMService` stores a pending action keyed by a UUID token. The UI renders a confirm button; calling `LLMService.confirm_delete(token)` executes it. This is the only multi-step flow.

**Undo:** `TodoApp` keeps a list of up to 20 task-list snapshots and restores them on undo — no DB-level rollback.

## Key files

| File | Role |
|---|---|
| [app.py](app.py) | Entry point — initializes Flet, hidden title bar, window constraints, theme manager, passes `SettingRepo` to `TodoApp` |
| [core/models/task.py](core/models/task.py) | `TaskRecord` dataclass: `id`, `name`, `date` (datetime), `end_date` (datetime), `description`, `completed`; `_parse_datetime`/`_fmt_db` helpers |
| [core/constants/enums.py](core/constants/enums.py) | `TaskActionType` enum (CREATE, LIST, UPDATE, DELETE, COMPLETE, UNCOMPLETE, SEARCH, HELP, PLAN, UNKNOWN) |
| [services/llm_service.py](services/llm_service.py) | LangChain `ChatOpenAI` wrapper; `TaskPlan` Pydantic model; plan/plan_tasks/chat tools; conversation memory (persisted via SettingRepo) |
| [services/nlp_task_parser.py](services/nlp_task_parser.py) | Regex/keyword fallback parser; duration parsing; plan keyword detection |
| [services/task_service.py](services/task_service.py) | Date resolution, `try_parse_date()`, batch creation, end_date/description support |
| [storage/db.py](storage/db.py) | SQLite connection; auto-migrates `end_date`/`description` columns |
| [storage/setting_repo.py](storage/setting_repo.py) | Key-value settings table for persisting user preferences |
| [ui/theme.py](ui/theme.py) | `ThemeManager` singleton: theme mode (light/dark/system), seed color, language; `AppColors` semantic palette |
| [ui/views/todo_view.py](ui/views/todo_view.py) | VSCode-style sidebar, chat drawer (side panel), task list (ReorderableListView), sorting, filters, date picker |
| [ui/views/settings_view.py](settings_view.py) | Settings page with left sidebar nav (外观, 语言, 助手设置) |
| [ui/components/task_item.py](ui/components/task_item.py) | Card-style task: inline date editor via CustomDatePicker, description expand/collapse, always-visible action buttons |
| [ui/components/date_picker.py](ui/components/date_picker.py) | Custom calendar widget: auto range detection, adaptive time layout, hour/minute dropdowns + direct input |

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

- `Task` (task_item.py) extends `ft.Column` with display/edit views, inline date editor using `CustomDatePicker` (auto range, adaptive time), description expand/collapse, always-visible edit/delete buttons. Card styling: expired=0.5 opacity + "过期" tag, completed=darker bg + "完成" tag, ongoing=green timestamp.
- `CustomDatePicker` (date_picker.py): built-in calendar widget with auto range detection (click second date → duration), adaptive time rows (single/same-day/cross-day), hour/minute dropdowns (width=110) + direct input, `set_range()`/`reset()` methods.
- `TodoApp` (todo_view.py) uses `ft.ReorderableListView` for drag-and-drop task reordering.
- Custom title bar via `ft.WindowDragArea` with minimize/maximize/close buttons.
- VSCode-style left sidebar (48px): icon buttons for chat, calendar (placeholder), and settings. Chat and settings are mutually exclusive.
- Chat drawer: side panel in a `ft.Row` layout (sidebar → drawer → content), uses `animate_opacity` for fade transition. Rounded corners: `ft.BorderRadius(12, 4, 4, 12)`. Assistant bubbles use `ft.Markdown` (GITHUB_WEB). Thinking animation with ProgressRing while LLM processes.
- Date color coding: blue = future, orange = today, grey = past, green = ongoing (between start and end). Expired = past deadline + not completed.
- Filter logic: "active" = not completed (includes expired). "ongoing" = currently between start and end dates.
- `ThemeManager` singleton persists theme mode (light/dark/system), seed color, and language via `SettingRepo`.
- Settings page: left sidebar nav (外观, 语言, 助手设置), right content area. Theme mode uses RadioGroup (浅色/深色/跟随系统).
- Flet 0.84.0 API notes: `Dropdown` uses `on_select` (not `on_change`); `Switch` does not support `dense`; use `ft.Border.all()` not `ft.border.all()`.
