# 优化记录

本文档记录了针对 Cleaner To-Do with AI 项目的代码优化。

- 2026-05-21：基础优化（LLM 双重调用、NLP 回退、中文化、DB 连接、主题系统、聊天抽屉、设置页）
- 2026-05-27：日期/时间选择器重构、卡片状态标记、LLM 记忆持久化、聊天体验优化

---

## 1. 修复 LLM 双重调用 Bug

**问题：** `todo_view.py:handle_user_message` 先调用 `llm_service.plan()` 判断是否为变更操作（用于决定是否推送 undo 快照），再调用 `llm_service.process()`。但 `process()` 内部会再次调用 `plan()`，导致每条用户消息触发 **2 次 LLM API 调用**，延迟翻倍且浪费 API 额度。

**修复：**
- `llm_service.py:process()` 新增可选参数 `intent: PlannedTaskIntent | None = None`，调用方可传入预计算的意图，跳过重复规划
- `todo_view.py:handle_user_message` 将首次 `plan()` 的结果直接传给 `process(intent=planned)`

**效果：** 每条用户消息从 2 次 LLM 调用降为 1 次，响应延迟减少约 50%。

---

## 2. 接入 NLP 回退解析器

**问题：** `nlp_task_parser.py` 实现了完整的中文正则/关键词解析器（411 行），但在整个代码流程中从未被调用。`LLMService.process()` 对未知意图直接走 `chat()` 自由对话，报告中声称的"离线可用"实际不成立。

**修复：**
- `llm_service.py` 新增 `from services.nlp_task_parser import parse_task_intent, ParsedTaskIntent`
- 新增 `_nlp_fallback()` 方法：调用 NLP 解析器并转换为 `PlannedTaskIntent`
- 新增 `_parsed_to_planned()` 方法：将 `ParsedTaskIntent` 转为 `PlannedTaskIntent`
- 修改 `plan()` 方法：LLM 不可用（无 API Key 或调用失败）时，使用 NLP 解析器作为主回退
- 修改 `process()` 方法：LLM 返回 UNKNOWN 时，先尝试 NLP 解析器（置信度 >= 0.6），再走 chat 回退

**效果：** 无 API Key 时自动使用 NLP 解析器，真正实现离线可用；LLM 识别失败时有二次机会。

---

## 3. 修复 UI 中英混用

**问题：** 界面存在大量英文文案，与中文优先的设计目标不一致：
- 输入框 hint: "What needs to be done?"
- 按钮: "Clear completed"、"Undo"
- 标题: "TO DO"
- 筛选标签: "all"、"active"、"completed"
- 计数: "0 items left"、"X active item(s) left"
- 工具提示: "Edit To-Do"、"Delete To-Do"、"Update To-Do"
- 设置页: "Settings"、"Back"

**修复（todo_view.py）：**
- "What needs to be done?" → "添加新任务"
- "Clear completed" → "清除已完成"
- "Undo" → "撤销"
- "TO DO" → "待办清单"
- 筛选标签使用中文显示（"全部"/"未完成"/"已完成"），内部状态保持英文 key，通过 `btn.data` 属性分离显示与逻辑
- "X items left" → "X 项未完成"
- "Settings" → "设置"、"Back" → "返回"

**修复（task_item.py）：**
- "Edit To-Do" → "编辑"
- "Delete To-Do" → "删除"
- "Update To-Do" → "确认"

**效果：** 界面语言统一为中文，消除中英混用的割裂感。

---

## 4. 优化 DB 连接管理

**问题：** `task_repo.py` 每个方法都调用 `get_connection()` 新建 SQLite 连接，操作完成后关闭。频繁读写时产生不必要的连接开销。

**修复（storage/db.py）：**
- 新增 `_connection_cache` 字典，按数据库路径缓存连接
- `get_connection()` 优先返回缓存连接（通过 `SELECT 1` 检测有效性），失效时重建
- 新增 `transaction()` 上下文管理器：自动 commit/rollback
- 新增 `close_all()` 函数：关闭所有缓存连接

**修复（storage/task_repo.py）：**
- 读操作（`list_tasks`、`get_task`、`find_tasks`）直接使用 `get_connection()` 获取缓存连接
- 写操作（`create_task`、`update_task`、`delete_task` 等）使用 `transaction()` 上下文管理器，自动管理事务

**效果：** 同一数据库路径复用同一连接，减少连接创建开销；写操作自动事务管理，异常时自动回滚。

---

## 5. 修复项目配置文件

**修复项：**

| 文件 | 修改内容 |
|---|---|
| `.gitignore` | 补充 `.env.local`、`core/data/*.db`、`*.py[cod]`、`.vscode/`、`.idea/`、`*.swp`、`.DS_Store`、`Thumbs.db`；移除自引用 `.gitignore` |
| `.env.example` | API Key 占位符从 `sk-` 改为 `your_deepseek_api_key_here`，避免误填 |
| `requirements.txt` | 移除非 pip 包（`Flutter`、`Pyodide`）；`Flet` 改为小写 `flet`；版本号 `=` 改为 `==`；补充 `pydantic>=2.0` |

---

## 修改文件清单

| 文件 | 变更类型 |
|---|---|
| `services/llm_service.py` | 修复双重调用 + 接入 NLP 回退 |
| `ui/views/todo_view.py` | 传参优化 + 中文化 |
| `ui/components/task_item.py` | 工具提示中文化 |
| `storage/db.py` | 连接缓存 + 事务管理器 |
| `storage/task_repo.py` | 使用缓存连接 + 事务 |
| `.gitignore` | 补充忽略规则 |
| `.env.example` | 修正占位符 |
| `requirements.txt` | 修正格式 + 补充依赖 |

---

## 6. UI 重构：主题系统 + 聊天抽屉 + 视觉美化

### 6.1 主题系统（ThemeManager）

**问题：** 无主题切换能力，splitter 颜色硬编码 hex 值（`"#3A3A3A"`/`"#BDBDBD"`），深色模式下不可用。

**实现：**
- `ui/theme.py` 新增 `ThemeManager` 单例类，管理 `dark_mode` 和 `seed_name` 两个状态
- 6 个预设主题色（蓝/靛/紫/青/橙/粉），基于 Flet 内置 `ft.Theme(color_scheme_seed=...)` 自动生成 Material 3 配色方案
- `apply(page)` 方法设置 `page.theme`/`page.dark_theme`/`page.theme_mode`
- `toggle_dark()` / `set_seed()` 方法实现运行时切换
- 主题偏好通过 `SettingRepo` 持久化到 SQLite `settings` 表

**AppColors 改造：**
- 移除硬编码 hex 值，全部改用 theme-aware 语义色
- splitter: `ft.Colors.OUTLINE_VARIANT` / `ft.Colors.OUTLINE`
- 面板背景: `ft.Colors.SURFACE_CONTAINER_LOW`
- 聊天气泡: `PRIMARY_CONTAINER`（用户）/ `SECONDARY_CONTAINER`（助手）
- 日期标签保持固定语义色（BLUE/ORANGE/GREY）

### 6.2 聊天抽屉

**问题：** 左侧聊天面板占用固定宽度，挤压任务列表空间；聊天以纯文本展示，无气泡样式。

**实现：**
- 使用自定义 Stack-based 抽屉（`ft.Container` + `animate_position`），从左侧滑出
- 主视图变为全宽任务列表，左侧浮动 `FAB` 按钮打开抽屉
- 打开动画：先渲染遮罩层（drawer 仍保持 `left=-width`），50ms 后设置 `left=0` 触发位置动画
- 关闭动画：设置 `left=-width` 触发动画，`asyncio.sleep(0.35)` 等待完成后隐藏遮罩
- 聊天气泡：用户消息右对齐（`PRIMARY_CONTAINER` 背景，右上圆角），助手消息左对齐（`SECONDARY_CONTAINER` 背景，左上圆角）
- 气泡宽度限制 360px，文字可选中
- 抽屉标题栏含关闭按钮
- 删除确认按钮移入抽屉内，使用 `ERROR` 色调

### 6.3 视觉美化

**布局：**
- 移除双面板 + 分割条布局，主视图改为单面板全宽
- 标题栏居中显示"待办清单"
- 任务输入 + 筛选 + 任务列表 + 状态栏垂直排列在同一面板内
- 筛选改用 `ft.Chip` 组件，选中状态高亮
- 底部操作按钮（清除已完成/撤销）改用 `ft.TextButton`

**按钮：**
- 发送按钮改用 `ft.IconButton(icon=SEND_ROUNDED)` 替代 `ft.FilledButton`
- 聊天输入框圆角加大（`border_radius=20`）
- 添加任务 FAB 改为 `mini=True`

**TaskItem：**
- 操作按钮（编辑/删除）改为 hover 时才显示（`opacity` 动画，200ms）
- 移除所有冗余 `font_family="Microsoft YaHei"`（继承全局主题）
- 任务行添加 `ft.GestureDetector` + `on_hover` 控制操作按钮可见性
- 编辑确认图标改为 `CHECK_CIRCLE_OUTLINE`

### 6.4 设置页

**实现 `ui/views/settings_view.py`：**
- 两栏布局（左栏设置项，右栏说明）
- 深色模式开关（`ft.Switch`）
- 主题色选择（`ft.RadioGroup` + 6 个 `ft.Radio`，带颜色预览）
- 设置变更即时生效 + 自动保存

**实现 `storage/setting_repo.py`：**
- SQLite `settings` 表（`key TEXT PRIMARY KEY, value TEXT`）
- `get(key, default)` / `set(key, value)` 方法
- 独立于 `tasks` 表，复用同一数据库连接

---

## 修改文件清单（更新）

| 文件 | 变更类型 |
|---|---|
| `services/llm_service.py` | 修复双重调用 + 接入 NLP 回退 |
| `ui/views/todo_view.py` | 抽屉式聊天气泡 + 全宽任务面板 + 美化 |
| `ui/views/settings_view.py` | 新增：设置页实现 |
| `ui/components/task_item.py` | hover 操作按钮 + 移除冗余 font_family |
| `ui/theme.py` | 重写：ThemeManager + theme-aware AppColors |
| `app.py` | 接入 ThemeManager + 简化布局 |
| `storage/db.py` | 连接缓存 + 事务管理器 |
| `storage/task_repo.py` | 使用缓存连接 + 事务 |
| `storage/setting_repo.py` | 新增：设置持久化 |
| `.gitignore` | 补充忽略规则 |
| `.env.example` | 修正占位符 |
| `requirements.txt` | 修正格式 + 补充依赖 |

---

## 7. 日期/时间选择器重构

**问题：**
1. 时间下拉框太窄（width=68），内容被截断
2. "持续"按钮多余，应自动检测
3. 持续任务时间 UI 混乱（不知哪个时间对应哪天）
4. 任务卡片编辑器与新建不一致

**实现 `ui/components/date_picker.py`（全新）：**
- 替代原生 `ft.DatePicker`，完全自定义日历控件
- **自动范围检测**：无需显式"持续"开关。点第一个日期设为 start，点第二个自动设为 end，点击端点取消
- **自适应时间行**：单日期一行（时间输入+下拉），同天持续两行（开始/结束时间），跨天持续两行（各自日期+时间）
- **时间选择**：小时/分钟下拉框（width=110，00-23/00-59）+ 文本直接输入
- **月份切换动画**：`animate_position=200` 平滑过渡
- **选中样式**：start/end 用主题色圆角背景，范围中间用浅色背景
- `set_range(start, end)` / `reset()` 方法供外部调用

**改造 `ui/components/task_item.py`：**
- 删除独立的结束日期 TextField 和持续开关，日期编辑器完全复用 `CustomDatePicker`
- 点击日期文本展开编辑器时，自动调用 `set_range(self.date, self.end_date)` 前置已有数据
- 新增 `ongoing` 属性：`end_date and not completed and date <= now <= end_date`

**改造 `ui/views/todo_view.py`：**
- 删除 `_new_task_duration_toggle` 及相关逻辑
- 新任务日历面板使用 `CustomDatePicker(show_time=True)`
- 创建任务后自动调用 `picker.reset()` 并关闭面板

---

## 8. 时间精确到小时/分钟 + datetime 类型统一

**问题：** `TaskRecord.date` 和 `end_date` 是 `date` 类型，不支持时间；`strptime` 使用 `%m/%d` 格式触发 DeprecationWarning。

**改造 `core/models/task.py`：**
- `date` 和 `end_date` 类型从 `date` 改为 `datetime`
- 新增 `_parse_datetime(s)`：兼容 ISO 完整格式（`2026-05-27T14:30:00`）和纯日期格式（`2026-05-27`）
- 新增 `_fmt_db(dt)`：仅当 hour/minute 非零时写入完整 ISO，否则只写日期

**改造 `services/task_service.py`：**
- `resolve_date()` / `try_parse_date()` 返回 `datetime`
- 新增 `_try_parse_time()` / `_extract_time()` 解析 HH:MM 时间
- 无年份日期格式（`%m/%d`、`%m-%d`）改为手动解析，消除 DeprecationWarning
- 所有 `create_task`/`update_task` 参数改为 `datetime | None`

---

## 9. 卡片状态标记

**问题：** 过期/完成/持续中的任务在视觉上无区分。

**实现：**
- **已完成**：加深背景（`opacity(0.92, PANEL_BG)`）+ "完成" 标签（蓝色调）
- **已过期**：0.5 透明度 + "过期" 标签（红色调）
- **正在持续**：时间戳显示绿色（`DATE_ONGOING = ft.Colors.GREEN`）
- `_refresh_card_style()` 方法在状态变更后更新卡片外观

**`AppColors` 新增：** `DATE_ONGOING = ft.Colors.GREEN`

---

## 10. LLM 交互体验优化

### 10.1 思考动画 + 异步调用

**问题：** LLM 处理期间 UI 无反馈，用户不知道是否在工作。

**实现：**
- 用户消息立即显示，同时创建思考气泡（`ProgressRing` + "思考中"文字）
- LLM 调用通过 `asyncio.to_thread` 非阻塞执行
- 调用完成后移除思考气泡，显示结果

### 10.2 Markdown 渲染

**问题：** LLM 回复中的 Markdown 格式（列表、加粗等）显示为纯文本。

**实现：** 助手气泡改用 `ft.Markdown`（`GITHUB_WEB` 扩展集），文字可选中。

### 10.3 LLM 记忆系统

**问题：** 对话无上下文连续性，每条消息独立处理。

**实现 `services/llm_service.py`：**
- `_memory: list[tuple[str, str]]` 存储最近 10 轮对话
- `_get_memory_context()` 将记忆格式化为上下文字符串，注入聊天系统提示
- `_remember()` 每轮对话后追加并持久化
- `clear_memory()` 清空并持久化

**持久化：** 通过 `SettingRepo` 序列化为 JSON 存储在 `settings` 表（key=`"llm_memory"`），启动时自动加载，重启不丢失。

### 10.4 聊天自动滚动

**问题：** 对话超出一屏后，新消息不自动滚动到可见区域。

**实现：** `ft.ListView(auto_scroll=True)` 自动滚动到最新消息，移除不可靠的 `scroll_to(offset=-1)` 调用。

---

## 11. 查询增强：ongoing 状态过滤

**问题：** 用户问"正在持续的任务有哪些"时，LLM 无法正确过滤。

**实现：**
- `TaskService.list_tasks()` 新增 `"ongoing"` status 过滤：`end_date is not None and not completed and date <= now <= end_date`
- LLM 系统 prompt 增加 ongoing 示例和状态说明
- `TaskPlan.status` 字段描述更新为包含 ongoing

---

## 修改文件清单（2026-05-27 更新）

| 文件 | 变更类型 |
|---|---|
| `ui/components/date_picker.py` | **新增**：自定义日历组件（自动范围、自适应时间、小时/分钟选择） |
| `core/models/task.py` | date→datetime 类型、`_parse_datetime`/`_fmt_db` 辅助函数 |
| `services/task_service.py` | 新增 ongoing 过滤、时间解析、datetime 返回类型 |
| `services/llm_service.py` | 记忆系统（持久化）、思考动画支持、ongoing 示例 |
| `ui/components/task_item.py` | 复用 CustomDatePicker、卡片状态标记、ongoing 绿色时间戳 |
| `ui/views/todo_view.py` | 去除持续开关、思考动画、Markdown 气泡、async LLM、自动滚动 |
| `ui/theme.py` | 新增 `DATE_ONGOING` 颜色 |
| `app.py` | `SettingRepo` 实例传递给 `TodoApp` |
| `CLAUDE.md` | 更新架构说明、UI 约定、文件描述 |
| `README.md` | 补充新功能列表、更新项目结构 |
| `FILE_CONTENTS.md` | 全面更新各模块文档 |
