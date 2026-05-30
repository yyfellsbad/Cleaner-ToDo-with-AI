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
| [app.py](app.py) | Entry point — initializes Flet, hidden title bar, window constraints, theme manager, LLM config manager, passes `SettingRepo` + `LLMConfigManager` to `TodoApp` |
| [core/models/task.py](core/models/task.py) | `TaskRecord` dataclass: `id`, `name`, `date` (datetime), `end_date` (datetime), `description`, `completed`, `repeat_days`, `repeat_mode`, `completed_dates`; recurring task support with `is_recurring`, `all_occurrences_done`, `mark_occurrence()` |
| [core/constants/enums.py](core/constants/enums.py) | `TaskActionType` enum (CREATE, LIST, UPDATE, DELETE, COMPLETE, UNCOMPLETE, SEARCH, HELP, PLAN, UNKNOWN) |
| [services/llm_service.py](services/llm_service.py) | LangChain `ChatOpenAI` wrapper; `TaskPlan` Pydantic model; plan/plan_tasks/chat tools; conversation memory (persisted via SettingRepo); reads config from `LLMConfigManager` with `.env` fallback |
| [services/llm_config_manager.py](services/llm_config_manager.py) | `LLMConfigManager` singleton: persists API key, base URL, model, chat prompt via `SettingRepo`; `test_connection()` for verifying config |
| [core/constants/defaults.py](core/constants/defaults.py) | `LLM_DEFAULTS` dict with default values for LLM config keys |
| [services/nlp_task_parser.py](services/nlp_task_parser.py) | Regex/keyword fallback parser; duration parsing; plan keyword detection |
| [services/task_service.py](services/task_service.py) | Date resolution, `try_parse_date()`, batch creation, end_date/description support |
| [storage/db.py](storage/db.py) | SQLite connection; auto-migrates `end_date`/`description` columns |
| [storage/setting_repo.py](storage/setting_repo.py) | Key-value settings table for persisting user preferences |
| [storage/daily_assessment_repo.py](storage/daily_assessment_repo.py) | Daily completion assessment table (date, score 0-4, manual flag); auto-backfills unassessed days from task data |
| [ui/theme.py](ui/theme.py) | `ThemeManager` singleton: theme mode (light/dark/system), seed color, language; `AppColors` semantic palette |
| [ui/views/todo_view.py](ui/views/todo_view.py) | VSCode-style sidebar, chat drawer (side panel), task list (ReorderableListView), sorting, filters, date picker |
| [ui/views/stats_view.py](ui/views/stats_view.py) | Stats page: PieChart donut, BarChart 7-day trend, summary cards, GitHub-style heatmap (26-week activity grid with daily completion assessment), entrance animations |
| [ui/views/calendar_view.py](ui/views/calendar_view.py) | Calendar page: month grid with task dot indicators (Morandi colors), year/month navigation, day selection with task detail panel |
| [ui/views/settings_view.py](ui/views/settings_view.py) | Settings page: left sidebar nav (外观, 语言, 助手设置), right content area. Assistant section has interactive LLM config fields (API key, base URL, model, chat prompt with confirm, test connection button), persona preset Chips (阿喵/阿汪/砖家/小冰/默认) |
| [ui/i18n.py](ui/i18n.py) | Translation system: 190+ keys for zh/en, `t(key, *args)` lookup, supports live language switching |
| [ui/components/task_item.py](ui/components/task_item.py) | Card-style task: inline date editor via CustomDatePicker, description expand/collapse, always-visible action buttons, repeat settings editor (interval + mode) |
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

- `Task` (task_item.py) extends `ft.Column` with display/edit views, inline date editor using `CustomDatePicker` (auto range, adaptive time), description expand/collapse, always-visible edit/delete buttons. Edit view includes repeat settings with preset frequency Chips (不重复/每天/隔天/每3天/每7天/自定义) and mode Chips with descriptions (只需一次/每次都要). Card styling: expired=0.5 opacity + "过期" tag, completed=darker bg + "完成" tag, ongoing=green timestamp.
- New task input area: repeat settings with same Chip-based UI appears alongside date picker and description when input is focused. Labels updated on language switch.
- `CustomDatePicker` (date_picker.py): built-in calendar widget with auto range detection (click second date → duration), adaptive time rows (single/same-day/cross-day), hour/minute dropdowns (width=110) + direct input, `set_range()`/`reset()` methods.
- `TodoApp` (todo_view.py) uses `ft.ReorderableListView` for drag-and-drop task reordering.
- Custom title bar via `ft.WindowDragArea` with minimize/maximize/close buttons.
- VSCode-style left sidebar (48px): icon buttons for chat, stats, calendar, and settings. Chat drawer toggles independently; stats, calendar, and settings are mutually exclusive content views.
- Chat drawer: side panel in a `ft.Row` layout (sidebar → drawer → content), uses `animate_opacity` for fade transition. Rounded corners: `ft.BorderRadius(12, 4, 4, 12)`. Shadow: `blur_radius=8, opacity=0.1, offset=2` (soft). Chat history `bgcolor=ft.Colors.SURFACE`. Assistant bubbles use `ft.Markdown` (GITHUB_WEB). Thinking animation with ProgressRing while LLM processes. On first open, assistant greets with time-based greeting + urgent task summary (ASCII art if no urgent tasks). Quick action Chips above input: "最近七天计划", "我接下来该做什么", "查看所有待办", "清除已完成".
- Date color coding: blue = future, orange = today, grey = past, green = ongoing (between start and end). Expired = past deadline + not completed.
- Filter logic: "active" = not completed (includes expired). "ongoing" = currently between start and end dates.
- `ThemeManager` singleton persists theme mode (light/dark/system), seed color, and language via `SettingRepo`.
- Settings page: left sidebar nav (外观, 语言, 助手设置), right content area. Theme mode uses RadioGroup (浅色/深色/跟随系统). Assistant section: API key (password field), base URL, model name, persona preset Chips (阿喵/阿汪/砖家/小冰/默认 — click fills chat prompt), chat prompt (multiline with confirm button), test connection button. Config persisted via `LLMConfigManager` → `SettingRepo` with `.env` fallback.
- Task sorting: default is urgency (紧迫程度) — sorts by `(end_date or date) - today` ascending, completed tasks sink below. Also supports date, name, duration ascending/descending.
- Stats page (stats_view.py): uses `flet-charts` (`PieChart` with `center_space_radius` for donut, `BarChart` for 7-day trend). GitHub-style full-year heatmap (7×52 grid, 12px cells) with year navigation (`[◀] YYYY [▶]`). Shows all 365 days including future dates (light grey). Today's assessment section below heatmap — tap Chip to rate (0-4), heatmap cell updates color instantly. Historical dates clickable with assessment dialog. Unassessed past days auto-backfilled from task completion ratio on page open. Midnight auto-refresh for next day. Morandi green color scale (4 levels).
- Recurring tasks: `TaskRecord` has `repeat_days` (interval), `repeat_mode` ("once"/"each"), `completed_dates` (JSON array of ISO dates). "once" mode = complete once = done. "each" mode = each occurrence independently tracked via `mark_occurrence(date)`. LLM auto-detects type from semantics (e.g., "每天跑步" → each, "持续一周考试" → once). UI uses preset frequency Chips (不重复/每天/隔天/每3天/每7天/自定义) and mode Chips (只需一次/每次都要) with descriptions. Display shows progress as "{}/{} 已打卡".
- Calendar page (calendar_view.py): two-card layout — grid card (month navigation with `≪` `≫` year / `<` `>` month, 7-column day grid with Morandi-colored task dots) + detail card (selected day's tasks with repeat labels and progress). Day states: completed=灰蓝, expired=赭石, today=赤金, ongoing=灰绿, future=淡紫, pending=燕麦. Card style: `border_radius=16`, shadow, 30px vertical padding.
- i18n (i18n.py): `t(key, *args)` function reads `ThemeManager.language`, returns localized string. All UI strings use `t()` calls. Language switch triggers `_rebuild_views()` for live refresh (no restart). NLP parser and LLM system prompts stay Chinese-only.
- Flet 0.85+ API notes: `Dropdown` uses `on_select` (not `on_change`); `Switch` does not support `dense`; use `ft.Border.all()` not `ft.border.all()`; `ft.Alignment.CENTER` not `ft.alignment.center`; `BarChartGroup` uses `rods=` not `bars=`.

## Workflow

每次修改代码后，必须同步更新以下文档：
1. **CLAUDE.md** — 更新 key files 表、UI conventions、architecture（如有结构变化）
2. **README.md** — 更新功能列表、项目结构
3. **optimize.md** — 追加本次优化记录（问题描述 + 实现方案 + 修改文件清单）
