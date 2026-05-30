# Flet 项目文件内容确认

更新时间：2026-05-30

## 项目描述

本项目是一个基于 Flet 的桌面待办管理应用，具备 AI 自然语言交互能力（中文优先）。系统采用 SQLite 本地持久化，以 core/storage/services/ui 四层架构实现界面、业务与数据解耦。当前版本已完整实现：任务增删改查、完成状态切换、条件筛选、日期颜色编码、AI 对话驱动的任务操作（通过 DeepSeek API）、删除二次确认、撤销（最多 20 步）、拖拽排序、任务持续时间（自动范围检测）、精确时间选择（小时/分钟）、任务描述、重复任务（每天/隔天/每N天，每期独立完成）、AI 任务规划、AI 对话记忆（持久化到数据库）、思考动画、Markdown 渲染回复、卡片状态标记（过期/完成/持续中）、自定义日历组件、自定义标题栏、VSCode 风格侧边栏、聊天侧边面板（首次打开问好、快捷气泡）、设置页面（外观/语言/助手设置、预设性格、API 配置管理）、主题跟随系统、多语言支持（中/英）、统计页面（环状图、柱状图、全年热力图+每日完成度评估+年份切换+午夜自动刷新）、日历视图、NLP 回退解析器、LLM 配置管理器（单例）。

---

## 1) 入口与配置

### app.py
- 应用唯一入口，调用 `ft.run(main)`。
- `main(page)` 设置标题、隐藏原生标题栏、窗口约束（min_width=780, min_height=400）、初始化 `SettingRepo` 实例，加载 ThemeManager，初始化 `LLMConfigManager` 和 `DailyAssessmentRepo`，恢复上次窗口位置/大小（`win.width`/`win.height`/`win.left`/`win.top`），注册 `on_event` 回调在窗口 resize/move 时持久化，将所有依赖传给 `TodoApp(tm, repo, llm_cfg, assessment_repo)`。

### requirements.txt
- `flet>=0.84.0`、`flet-charts>=0.85`
- `langchain>=0.2.14`、`langchain-openai>=0.1.22`、`python-dotenv>=1.0.1`
- `pydantic>=2.0`

### .env（不提交）
- `OPENAI_API_KEY`：DeepSeek API Key
- `OPENAI_MODEL=deepseek-chat`
- `OPENAI_BASE_URL=https://api.deepseek.com/`
- `OPENAI_TEMPERATURE=0.3`

---

## 2) core 层

### core/constants/enums.py
- `TaskActionType(str, Enum)`：CREATE / LIST / UPDATE / DELETE / COMPLETE / UNCOMPLETE / SEARCH / HELP / PLAN / UNKNOWN

### core/models/task.py
- `TaskRecord(dataclass, slots=True)`：`id`、`name`、`date: datetime`、`end_date: datetime | None`、`description`、`completed`
- `_parse_datetime(s)`：兼容 ISO 完整格式和纯日期格式（`YYYY-MM-DD`），返回 `datetime`
- `_fmt_db(dt)`：仅当 hour/minute 非零时写入完整 ISO，否则只写日期（`YYYY-MM-DD`）
- `from_row(row)`：支持 `sqlite3.Row` 和普通元组，用 `_parse_datetime` 解析日期
- `to_db_values()`：返回 `(name, date_iso, end_date_iso|None, description, completed_int)` 供 SQL 绑定

---

## 3) storage 层

### storage/db.py
- `get_connection(db_path)`：自动创建 `data/` 目录，设置 `row_factory=sqlite3.Row`，调用 `ensure_schema`。
- `ensure_schema(conn)`：建表 `tasks(id, name, date, completed)`（幂等），自动迁移添加 `end_date` 和 `description` 列。

### storage/task_repo.py
- `TaskRepository`：封装所有 SQLite CRUD。
- 方法：`list_tasks`（按 date DESC, id DESC）、`get_task`、`find_tasks`（LIKE 模糊搜索 name 和 description）、`create_task`、`update_task`、`delete_task`、`bulk_delete`、`delete_all`、`create_many`（批量插入，单次 commit）。
- 所有 INSERT/UPDATE 均包含 `end_date` 和 `description` 字段。

### storage/setting_repo.py
- `SettingRepo`：键值对设置存储（`settings` 表）。
- 方法：`get(key, default)`、`set(key, value)`。
- 用于持久化主题偏好（深色模式、主题色、语言）和 LLM 对话记忆（`"llm_memory"` key，JSON 格式）。

### storage/daily_assessment_repo.py
- `DailyAssessmentRepo`：每日完成度评估存储（`daily_assessments` 表）。
- 表结构：`date TEXT PRIMARY KEY, score INTEGER, manual INTEGER`。
- `score` 0-4（0=无活动, 1=1-25%, 2=26-50%, 3=51-75%, 4=76-100%）。
- `manual` 0=自动计算, 1=用户手动设定（自动回填不覆盖手动记录）。
- 方法：`get(date)`、`get_range(start, end)`、`upsert(date, score, manual)`。
- 遵循 `setting_repo.py` 模式：构造函数中 `_ensure_table()`，写操作用 `transaction()`。

---

## 4) services 层

### services/task_service.py
- `TaskService`：业务逻辑层，依赖 `TaskRepository`。
- 主要方法：
  - `list_tasks(status, keyword)`：支持 all/active/completed/ongoing 过滤 + 关键词过滤（ongoing=当前在 start~end 之间）
  - `create_task` / `create_tasks`（批量，自动加 `#1 #2 ...` 后缀，支持 `end_date` 和 `description`）
  - `update_task`（支持 `end_date`、`clear_end_date`、`description` 参数）
  - `delete_task`、`delete_tasks`、`delete_all_tasks`
  - `mark_complete` / `complete_task` / `uncomplete_task`
  - `replace_all_tasks`（用于 undo 恢复，保留 `end_date` 和 `description`）
  - `resolve_date(value)`：解析 今天/明天/后天/ISO/MM-DD/纯数字（527→5-27, 1225→12-25）等格式
  - `try_parse_date(value)`：严格日期解析，失败返回 None（供日期编辑器校验用，支持同样格式）

### services/llm_service.py
- 核心 AI 编排层，使用 LangChain `ChatOpenAI`（OpenAI 兼容接口）。通过 `LLMConfigManager` 读取配置（API 密钥、URL、模型、聊天人设），支持 `.env` 回退。
- **数据模型**：
  - `TaskPlan(BaseModel)`：LLM 结构化输出 schema（tool、action、task_name、target_text、new_text、date_text、end_date_text、status[含ongoing]、batch_count、delete_scope、complete_scope、confirmation_required、reply）
  - `PlannedTaskIntent(dataclass)`：内部意图对象（含 `end_date: datetime`）
  - `AssistantResult(dataclass)`：返回给 UI 的结果（message、action、tasks、pending_confirmation、confirmation_token、suggested_actions）
  - `PendingAction(dataclass)`：待确认删除操作，keyed by UUID token
- **主要方法**：
  - `plan(text) → PlannedTaskIntent`：调用 LLM planner（temperature=0.3），解析 JSON 输出
  - `process(text, confirmed, confirmation_token, current_status) → AssistantResult`：路由到对应操作
  - `confirm_delete(token) → AssistantResult`：执行已确认的删除
  - `plan_tasks() → AssistantResult`：读取活跃任务列表，按紧迫性排序，LLM 推荐下一步行动
  - `chat(text) → str`：自由对话（temperature=0.4），包含记忆上下文
- **记忆系统**：`_memory: list[tuple[str, str]]`（最多 10 轮），通过 `SettingRepo` 持久化到 `settings` 表（JSON，key=`"llm_memory"`）。`_load_memory()` 启动时加载，`_remember()` 每轮保存，`clear_memory()` 清空并持久化。
- **系统提示**：中文，要求只输出 JSON，含 few-shot 示例，支持持续时间、规划、ongoing 查询指令
- **删除流程**：先返回 `pending_confirmation=True` + token，UI 点击确认后调用 `confirm_delete`
- **规划流程**：`plan_tasks` 将任务按紧急程度排序（已过期 > 今天到期 > 明天 > 本周 > 更远），LLM 基于排序结果给出建议

### services/nlp_task_parser.py
- LLM 不可用时的正则/关键词回退解析器。
- `parse_task_intent(text) → ParsedTaskIntent`
- 支持：CREATE（含批量数量提取、日期/持续时间提取、核心名称提取）、DELETE（含 all/current/matched scope）、UPDATE（改名/改日期）、COMPLETE/UNCOMPLETE（含 scope）、LIST、PLAN、HELP、UNKNOWN
- `_parse_duration(text)`：解析"从X到Y"、"持续X天"等持续时间模式
- `_extract_create_name`：7 步渐进式清洗（移除前缀、日期词、数量词、通用词、"的"分割、虚词、截断）

### services/llm_config_manager.py
- `LLMConfigManager`（单例）：管理 LLM 配置（API 密钥、Base URL、模型名称、聊天人设）。
- 通过 `SettingRepo` 持久化，启动时从 `.env` 回退读取默认值。
- `test_connection()`：发送测试请求验证配置有效性。
- 属性：`api_key`、`base_url`、`model`、`chat_prompt`，均有 getter/setter。

---

## 5) ui 层

### ui/theme.py
- `THEME_SEEDS` / `THEME_SEED_LABELS`：6 种主题色预设（蓝/靛蓝/紫/青/橙/粉）。
- `AppColors`：语义颜色常量（面板背景、分割条、聊天气泡、日期颜色[含 DATE_ONGOING 绿色]、编辑确认色、辅助文字色）。
- `ThemeManager`（单例）：
  - `theme_mode`（"light"/"dark"/"system"）、`seed_name`、`language` 属性
  - `dark_mode` 属性（只读，基于 theme_mode 判断）
  - `load(repo)`：从 `SettingRepo` 加载偏好，支持 "system" 模式
  - `apply(page)`：应用主题到页面（`ft.ThemeMode.SYSTEM` / `DARK` / `LIGHT`）
  - `set_theme_mode(page, mode)` / `set_seed(page, name)` / `set_language(lang)`：切换并持久化
  - `_build_theme(seed)`：构建 `ft.Theme`（Microsoft YaHei 字体、Compact 密度）

### ui/views/todo_view.py
- `TodoApp(ft.Column)`：主视图，持有所有状态。构造函数接收 `ThemeManager`、可选的 `SettingRepo`（传给 LLMService）、可选的 `LLMConfigManager` 和可选的 `DailyAssessmentRepo`（传给 StatsView）。
- **自定义标题栏**：`ft.WindowDragArea` 包含应用名 + 最小化/最大化/关闭按钮。
- **VSCode 风格侧边栏**：48px 宽，包含智能助手、统计、日历（预留/禁用）、设置四个图标按钮。聊天、统计、设置互斥。
- **聊天侧边面板**：`ft.Row` 布局（侧边栏 → 抽屉 → 内容），`animate_opacity` 过渡动画，`BorderRadius(12, 4, 4, 12)`。再次点击关闭，与设置互斥。助手气泡使用 `ft.Markdown`（GITHUB_WEB 扩展）渲染。用户气泡 `BorderRadius(16,16,16,4)`，助手气泡 `BorderRadius(4,16,16,16)`。
- **快捷气泡**：输入框上方 4 个 Chip（最近七天计划/接下来做什么/查看所有待办/清除已完成），使用 `_make_quick_chip_handler` 工厂函数生成异步处理器。
- **首次问好**：基于时间的问候 + 任务数量摘要 + 建议操作，区别于欢迎弹窗的完整任务列表。
- **任务面板**：输入行（TextField + 日历按钮 + 日期标签 + FAB）+ 筛选行（all/active/completed/expired）+ 排序下拉（140px 宽）+ 清除/撤销 + ReorderableListView。
- **新任务日期**：使用 `CustomDatePicker(show_time=True)`，支持自动范围检测，创建后调用 `picker.reset()` 并自动关闭面板。
- **排序**：6 种排序模式（日期↑/↓、名称A-Z/Z-A、持续时间↑/↓），`_apply_sort()` 在 `before_update` 中执行。
- **筛选**：`before_update` 中根据 filter 控制任务可见性（active 包含已过期），底部显示未完成数和过期数。
- **拖拽排序**：`ft.ReorderableListView` + `_on_task_reorder` 回调。
- **设置页面**：侧边栏按钮切换开/关，与聊天互斥。`SettingsView` 嵌入其中。
- **AI 交互流程**（`handle_user_message`）：
  1. 用户消息立即显示，同时创建思考中气泡（ProgressRing + "思考中"）
  2. 检测确认/取消关键词处理待删除操作
  3. 调用 `llm_service.plan` 判断是否为变更操作，提前 push undo 快照
  4. 调用 `llm_service.process`（通过 `asyncio.to_thread` 非阻塞），移除思考气泡，显示结果
- **Undo**：`push_undo_snapshot` 保存最多 20 个任务列表快照（含 end_date/description）；`undo_last` 调用 `replace_all_tasks` 恢复。

### ui/views/settings_view.py
- `SettingsView(ft.Column)`：设置页面，左侧导航栏 + 右侧内容区。
- **导航项**：外观（主题模式 + 主题色）、语言（中文/English）、助手设置（API 配置 + 预设性格）。
- `_on_nav_click`：切换导航高亮 + 重建右侧内容区。
- 外观：`ft.RadioGroup` 主题模式（浅色/深色/跟随系统）+ `ft.RadioGroup` 主题色。
- 语言：`ft.RadioGroup` 语言选择（zh/en），通过 `ThemeManager.set_language` 持久化。
- **助手设置**：API 密钥（密码字段）、Base URL、模型名称、聊天人设（多行文本 + 确认按钮）、测试连接按钮。配置通过 `LLMConfigManager` → `SettingRepo` 持久化。
- **预设性格**：`PERSONA_PRESETS` 字典（阿喵/阿汪/砖家/小冰/默认），Chip 点击填充聊天人设字段。

### ui/views/stats_view.py
- `StatsView(ft.Column)`：数据统计页面，使用 `flet-charts` 库（`PieChart` + `BarChart`），构造函数接收 `TaskService` 和 `DailyAssessmentRepo`。
- **概览卡片行**：4 张卡片（总任务、已完成、完成率、已过期），每张含图标+数字+标签。
- **环状图**：`PieChart(center_space_radius=60)` 实现环状效果，4 段（已完成/进行中/已过期/未开始），中心叠加显示总任务数。颜色使用 Material 3 语义色（`TERTIARY`/`SECONDARY`/`ERROR`/`OUTLINE`）。
- **GitHub 风格热力图**：7 行（周一~日）× 52 列全年网格，左侧星期标签 + 顶部月份标签。方块 12×12px，间距 2px，圆角 3px。颜色 5 级（`GREEN` 透明度 0.15/0.30/0.55/0.85）。支持年份切换（`≪` `≫` 按钮）。
- **今日完成度评估**：热力图卡片底部，5 个 Chip（未完成/25%/50%/75%/全部完成），点击即时更新热力图颜色并持久化（`manual=1`）。
- **历史日期评估**：点击热力图方块弹出 `AlertDialog`，同样 5 个选项，确认后颜色即时更新。
- **自动回填**：`_backfill_assessments()` 在 `_load_data()` 开头调用，遍历 1 年内无记录的日期，按任务完成比例计算 score 并写入（`manual=0`），不覆盖手动记录。
- **午夜自动刷新**：`_schedule_midnight_refresh()` 计算距午夜秒数，sleep 后刷新进入下一天评估。
- **近 7 天趋势**：`BarChart` 每天 2 根柱子（新增/完成），带日期轴和数值轴，底部图例。
- **入场动画**：概览卡片逐张 `animate_opacity`（300ms，延迟 80ms），环状图 `animate_scale`（0.85→1.0）+ `animate_opacity`（400ms），热力图和趋势图 `animate_opacity`。
- **`animate_in()`**：触发入场动画（首次显示或切换回来时），重置 opacity=0 后逐个延迟渐显。
- **`refresh_data()`**：外部调用刷新（无动画重播）。
- **数据来源**：从 `TaskService.list_tasks("all")` 在 Python 中计算所有指标。

### ui/components/task_item.py
- `Task(ft.Column)`：卡片式任务组件，接收 `datetime` 类型的 `date` 和 `end_date`。
- **display_view**：卡片样式（圆角边框、面板背景，左/右 padding 为拖拽手柄留空间），包含任务名 + 状态标签 + 日期区域 + 描述 + 复选框 + 操作按钮（始终可见：编辑、删除）。
- **卡片状态**：已完成 → 加深背景 + "完成" 标签；已过期 → 0.5 透明度 + "过期" 标签；正常 → 无标记。
- **ongoing 属性**：`end_date and not completed and date <= now <= end_date`。
- **日期显示**：`_fmt_short()` 显示相对日期（今天/明天/后天）+ 时间（如有）；ongoing 任务显示绿色。
- **日期编辑器**：复用 `CustomDatePicker(show_time=True)`，点击日期文本 → 展开编辑器，自动调用 `set_range(date, end_date)` 填入已有数据，确认后保存。
- **描述显示**：小字单行，点击展开/收起（`_toggle_desc`）。
- **edit_view**：任务名 + 描述编辑 + 确认按钮。
- **expired 属性**：`(end_date or date).date() < today and not completed`。

### ui/components/date_picker.py
- `CustomDatePicker(ft.Column)`：自定义日历组件，替代原生 `ft.DatePicker`。
- **自动范围检测**：始终支持范围，无需显式开关。点击第一个日期设为 start，点击第二个自动设为 end（变持续），点击端点取消该端。
- **自适应时间行**：单日期 → 一行（时间输入 + 小时/分钟下拉）；同天持续 → 两行（开始/结束时间）；跨天持续 → 两行（各自日期+时间）。
- **时间选择**：小时/分钟下拉框（width=110，00-23/00-59）+ 文本直接输入（确认按钮验证）。
- **关键方法**：`set_range(start, end)` 前置数据、`reset()` 重置状态、`range_start`/`range_end` 属性读取结果。
- **回调**：`on_change(start: datetime, end: datetime | None)` 统一签名。
- **月份切换**：左右箭头切换月份，带平滑动画（`animate_position=200`）。
- **选中样式**：start/end 日期用主题色圆角背景，范围中间日期用浅色背景。

---

## 6) 启动方式

```bash
python app.py
# 或
flet run app.py
```
