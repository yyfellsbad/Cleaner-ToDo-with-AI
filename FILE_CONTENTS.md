# Flet 项目文件内容确认

更新时间：2026-04-29

## 项目描述

本项目是一个基于 Flet 的桌面待办管理应用，具备 AI 自然语言交互能力（中文优先）。系统采用 SQLite 本地持久化，以 core/storage/services/ui 四层架构实现界面、业务与数据解耦。当前版本已完整实现：任务增删改查、完成状态切换、条件筛选、日期颜色编码、AI 对话驱动的任务操作（通过 DeepSeek API）、删除二次确认、撤销（最多 20 步）、可拖拽分栏布局，以及 NLP 回退解析器。

---

## 1) 入口与配置

### app.py
- 应用唯一入口，调用 `ft.run(main)`。
- `main(page)` 设置标题、主题字体（Microsoft YaHei）、内边距，挂载 `TodoApp`。

### requirements.txt
- `Flet=0.84.0`、`Flutter=3.41.4`、`Pyodide=0.27.7`
- `langchain>=0.2.14`、`langchain-openai>=0.1.22`、`python-dotenv>=1.0.1`

### .env（不提交）
- `OPENAI_API_KEY`：DeepSeek API Key
- `OPENAI_MODEL=deepseek-chat`
- `OPENAI_BASE_URL=https://api.deepseek.com/`
- `OPENAI_TEMPERATURE=0.3`

---

## 2) core 层

### core/constants/enums.py
- `TaskActionType(str, Enum)`：CREATE / LIST / UPDATE / DELETE / COMPLETE / UNCOMPLETE / SEARCH / HELP / UNKNOWN

### core/models/task.py
- `TaskRecord(dataclass, slots=True)`：`id`、`name`、`date`、`completed`
- `from_row(row)`：支持 `sqlite3.Row` 和普通元组
- `to_db_values()`：返回 `(name, date_iso, completed_int)` 供 SQL 绑定

---

## 3) storage 层

### storage/db.py
- `get_connection(db_path)`：自动创建 `data/` 目录，设置 `row_factory=sqlite3.Row`，调用 `ensure_schema`。
- `ensure_schema(conn)`：建表 `tasks(id, name, date, completed)`（幂等）。

### storage/task_repo.py
- `TaskRepository`：封装所有 SQLite CRUD。
- 方法：`list_tasks`（按 date DESC, id DESC）、`get_task`、`find_tasks`（LIKE 模糊搜索）、`create_task`、`update_task`、`delete_task`、`bulk_delete`、`delete_all`、`create_many`（批量插入，单次 commit）。

---

## 4) services 层

### services/task_service.py
- `TaskService`：业务逻辑层，依赖 `TaskRepository`。
- 主要方法：
  - `list_tasks(status, keyword)`：支持 all/active/completed 过滤 + 关键词过滤
  - `create_task` / `create_tasks`（批量，自动加 `#1 #2 ...` 后缀）
  - `update_task`、`delete_task`、`delete_tasks`、`delete_all_tasks`
  - `mark_complete` / `complete_task` / `uncomplete_task`
  - `replace_all_tasks`（用于 undo 恢复）
  - `resolve_date(value)`：解析 今天/明天/后天/ISO/MM-DD 等格式

### services/llm_service.py
- 核心 AI 编排层，使用 LangChain `ChatOpenAI`（OpenAI 兼容接口）。
- **数据模型**：
  - `TaskPlan(BaseModel)`：LLM 结构化输出 schema（tool、action、task_name、target_text、new_text、date_text、status、batch_count、delete_scope、complete_scope、confirmation_required、reply）
  - `PlannedTaskIntent(dataclass)`：内部意图对象
  - `AssistantResult(dataclass)`：返回给 UI 的结果（message、action、tasks、pending_confirmation、confirmation_token、suggested_actions）
  - `PendingAction(dataclass)`：待确认删除操作，keyed by UUID token
- **主要方法**：
  - `plan(text) → PlannedTaskIntent`：调用 LLM planner（temperature=0.3），解析 JSON 输出
  - `process(text, confirmed, confirmation_token, current_status) → AssistantResult`：路由到对应操作
  - `confirm_delete(token) → AssistantResult`：执行已确认的删除
  - `chat(text) → str`：自由对话（temperature=0.4）
- **系统提示**：中文，要求只输出 JSON，含 few-shot 示例
- **删除流程**：先返回 `pending_confirmation=True` + token，UI 点击确认后调用 `confirm_delete`

### services/nlp_task_parser.py
- LLM 不可用时的正则/关键词回退解析器。
- `parse_task_intent(text) → ParsedTaskIntent`
- 支持：CREATE（含批量数量提取、日期提取、核心名称提取）、DELETE（含 all/current/matched scope）、UPDATE（改名/改日期）、COMPLETE/UNCOMPLETE（含 scope）、LIST、HELP、UNKNOWN
- `_extract_create_name`：7 步渐进式清洗（移除前缀、日期词、数量词、通用词、"的"分割、虚词、截断）

---

## 5) ui 层

### ui/theme.py
- `AppColors`：集中定义面板背景、分割条、聊天气泡、日期颜色（蓝/橙/灰）、编辑确认按钮色、辅助文字色。
- `get_app_theme()`：返回 `ft.Theme(font_family="Microsoft YaHei")`。

### ui/views/todo_view.py
- `TodoApp(ft.Column)`：主视图，持有所有状态。
- **布局**：左面板（AI 对话）+ 可拖拽分割条 + 右面板（任务列表），双栏宽度可拖拽调整（`resize_panels`）。
- **左面板**：聊天历史（`ft.ListView`）、输入框、发送按钮、确认删除按钮（`ai_confirm_button`，默认隐藏）。
- **右面板**：手动新增输入框、筛选按钮（all/active/completed）、任务列表、items left 计数、Clear completed、Undo 按钮。
- **AI 交互流程**（`handle_user_message`）：
  1. 检测确认/取消关键词（"确认"/"取消"等）处理待删除操作
  2. 调用 `llm_service.plan` 判断是否为变更操作，提前 push undo 快照
  3. 调用 `llm_service.process` 获取结果，更新 UI
- **Undo**：`push_undo_snapshot` 保存最多 20 个任务列表快照；`undo_last` 调用 `replace_all_tasks` 恢复。
- **设置页**：骨架占位（左列"设置列表（预留）"，右列"具体设置界面（预留）"），通过 `open_settings`/`close_settings` 切换可见性。

### ui/components/task_item.py
- `Task(ft.Column)`：单任务行组件。
- **display_view**：任务名（W_500）+ 日期标签（含 emoji 📅，颜色编码）+ 复选框 + 编辑/删除按钮。
- **edit_view**：文本输入框 + 确认按钮（绿色对勾），默认隐藏。
- 日期显示：明天/后天/MM-DD，颜色：未来=蓝，今天=橙，过去=灰。
- `status_changed`：复选框变更后调用 `app.save_task(self)`。
- `save_clicked`：保存编辑后调用 `app.save_task(self)`。

---

## 6) 空骨架文件（预留扩展）

- `core/models/setting.py`、`core/constants/defaults.py`
- `storage/setting_repo.py`
- `services/calendar_service.py`
- `ui/app_shell.py`、`ui/i18n.py`、`ui/state.py`
- `ui/views/settings_view.py`、`ui/views/calendar_view.py`
- `ui/components/task_list.py`、`ui/components/settings_menu.py`、`ui/components/settings_panels.py`、`ui/components/empty_state.py`

---

## 7) 启动方式

```bash
python app.py
# 或
flet run app.py
```
