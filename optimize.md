# 优化记录

本文档记录了针对 Cleaner To-Do with AI 项目的代码优化，日期：2026-05-21。

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
