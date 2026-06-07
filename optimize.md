# 优化记录

本文档记录了针对 Cleaner To-Do with AI 项目的代码优化。

- 2026-05-21：基础优化（LLM 双重调用、NLP 回退、中文化、DB 连接、主题系统、聊天抽屉、设置页）
- 2026-05-27：日期/时间选择器重构、卡片状态标记、LLM 记忆持久化、聊天体验优化
- 2026-05-29：统计页面（flet-charts 环状图/柱状图、入场动画、今日待办、7 天趋势）
- 2026-05-30：AI 助手设置暴露、紧迫排序、日历视图、多语言支持（i18n）、LLM 配置管理器、重复任务（每期独立完成）、热力图+每日完成度评估、主题适配、项目清理、窗口位置记忆
- 2026-06-06：窗口状态修复（事件类型、多显示器、全屏记忆）、系统通知功能（winotify+DND+去重+调度器+设置页）、重复任务打卡实时更新、UI 冻结修复（减少 update 调用）、onboarding 教程重写（7 步+AI/任务/视图教程）、设置页教程入口、取消追踪 pyc/tasks.db
- 2026-06-07：UI 冻结彻底修复（_needs_resort 标志+card 级 update+fire-and-forget 动画+toast 优化）、onboarding 统一卡片高度+固定按钮位置、Flet 0.85 API 兼容修复

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
| `README.md` | 补充新功能列表、更新项目结构 |
| `FILE_CONTENTS.md` | 全面更新各模块文档 |

---

## 12. 统计页面

**问题：** 无数据可视化能力，用户无法直观了解任务完成情况和趋势。

**实现 `ui/views/stats_view.py`（全新）：**
- 使用 `flet-charts` 库（`PieChart` + `BarChart`），Flet 原生图表控件
- **概览卡片行**：4 张卡片（总任务、已完成、完成率、已过期），每张含图标+数字+标签
- **环状图**：`PieChart(center_space_radius=60)` 实现环状效果，4 段（已完成/进行中/已过期/未开始），中心叠加显示总任务数
- **今日待办列表**：展示今天日期包含的所有未完成任务，含名称、时间、状态标签（进行中/今日/待办），空态显示"今日无待办"
- **近 7 天趋势**：`BarChart` 每天 2 根柱子（新增/完成），带日期轴和数值轴，底部图例
- **入场动画**：概览卡片逐张 `animate_opacity`（300ms，延迟 80ms），环状图 `animate_scale`（0.85→1.0）+ `animate_opacity`（400ms），今日待办和趋势图 `animate_opacity`
- **刷新**：重置所有元素 opacity=0 后重新加载数据，逐个触发渐显动画
- **数据来源**：从 `TaskService.list_tasks("all")` 在 Python 中计算所有指标（无需新增 SQL 查询）

**改造 `ui/views/todo_view.py`：**
- 侧边栏新增统计按钮（`BAR_CHART_OUTLINED` 图标），位于聊天和日历之间
- `_sidebar_settings` 改为实例变量（便于切换 icon_color）
- `open_stats` 方法：关闭聊天和设置（互斥），切换统计视图可见性，触发动画
- `open_settings` / `_toggle_chat_drawer` 新增与统计的互斥逻辑

**依赖：** `flet-charts>=0.85`（同时将 flet 从 0.84.0 升级到 0.85.2）

---

## 修改文件清单（2026-05-29 更新）

| 文件 | 变更类型 |
|---|---|
| `ui/views/stats_view.py` | **新增**：统计页面（环状图、柱状图、概览卡片、今日待办、入场动画） |
| `ui/views/todo_view.py` | 侧边栏统计按钮 + 互斥逻辑 + settings 按钮实例化 |
| `requirements.txt` | 新增 `flet-charts>=0.85`，flet 版本升级 |

---

## 13. AI 助手设置暴露 + LLM 配置管理器

**问题：** API Key、Base URL、模型、聊天人设等配置硬编码在 `.env` 中，用户无法在应用内修改。

**实现 `services/llm_config_manager.py`（全新）：**
- `LLMConfigManager` 单例类，管理 `api_key`、`base_url`、`model`、`chat_prompt`
- 首次加载从 `.env` 读取默认值，之后通过 `SettingRepo` 持久化
- `set_api_key()` / `set_base_url()` / `set_model()` / `set_chat_prompt()` 方法自动保存 + 通知回调
- `test_connection()` 发送 trivial 请求验证配置
- `_on_changed` 回调触发 `LLMService.rebuild()` 运行时重配

**改造 `ui/views/settings_view.py`：**
- 助手设置区：API Key（密码字段）、Base URL、模型、聊天人设（多行文本 + 确认按钮）
- 测试连接按钮：异步调用 `test_connection()`，SnackBar 显示结果
- 聊天人设修改需手动确认（非自动保存）

**改造 `services/llm_service.py`：**
- 构造函数新增 `config_manager` 参数
- `_get_config()` 辅助方法：优先读配置管理器，回退到 `.env`
- `rebuild()` 方法重建 planner 和 chat model

**改造 `ui/views/todo_view.py`：**
- `TodoApp` 接收 `config_manager`，传递给 `LLMService`
- `config_manager._on_changed` 绑定 `llm_service.rebuild()`

---

## 14. 紧迫排序

**问题：** 默认排序（日期升序）无法反映任务紧迫程度。

**实现：**
- 新增 `"urgency_asc"` 排序模式作为默认
- 排序键：`(end_date or date).date() - today`，天数越小越靠前
- 已完成任务偏移 +10000 沉底
- 筛选标签和排序下拉框新增"紧迫程度"选项

---

## 15. 日历视图

**问题：** 侧边栏日历按钮为 placeholder（disabled），无日历功能。

**实现 `ui/views/calendar_view.py`（全新）：**
- 两卡片布局：日历网格卡 + 事件详情卡，圆角 16px + 阴影
- **月份导航**：`≪` `≫` 切换年份，`<` `>` 切换月份，"今天"按钮跳回当前
- **月网格**：7 列 × 5-6 行，单元格 48×62px，显示日期数字 + 任务圆点
- **任务圆点**：莫兰迪色系 6 色区分状态（灰蓝=完成、赭石=过期、赤金=今日、灰绿=进行中、淡紫=未来、燕麦=待办），最多 4 个圆点
- **日期选择**：点击日期刷新详情面板，显示当天任务列表（状态圆点 + 任务名 + 时间）
- **数据来源**：`task_service.list_tasks("all")`，按日期范围过滤

**改造 `ui/views/todo_view.py`：**
- 侧边栏日历按钮启用，新增 `open_calendar()` 方法
- `_sync_content_views` 扩展为四选一（main/stats/calendar/settings）
- `_rebuild_views()` 新增日历视图重建

---

## 16. 多语言支持（i18n）

**问题：** 所有 UI 字符串硬编码中文，语言设置无效。

**实现 `ui/i18n.py`（全新）：**
- 190+ 翻译键，覆盖设置、聊天、筛选、排序、统计、日历、LLM 消息等
- `t(key, *args)` 函数：读取 `ThemeManager.language`，返回对应语言字符串，支持 `format(*args)`
- 周期名、月份名使用 `picker.weekdays` / `picker.months` 逗号分隔格式

**改造所有 UI 文件：**
- `ui/views/settings_view.py`：~25 处替换
- `ui/views/todo_view.py`：~60 处替换（问候、筛选、排序、对话框、状态）
- `ui/views/stats_view.py`：~20 处替换
- `ui/views/calendar_view.py`：直接使用 `t()` 调用
- `ui/components/task_item.py`：~11 处替换
- `ui/components/date_picker.py`：~17 处替换
- `services/llm_service.py`：~30 处 UI 消息替换（LLM 系统 prompt 保持中文）
- `services/llm_config_manager.py`：4 处替换
- `ui/theme.py`：6 个主题色标签

**实时刷新：**
- `settings_view._on_lang_change` → `ThemeManager.set_language()` → `on_lang_change` 回调
- `TodoApp._rebuild_views()` 重建设置、统计、日历视图 + 更新筛选/排序/按钮标签
- 无需重启，切换语言即时生效

**变量名冲突修复：**
- `stats_view.py` 和 `todo_view.py` 中循环变量 `t`（TaskRecord）覆盖 i18n 函数 `t`，统一重命名为 `tk`

---

## 17. 窗口图标

**问题：** 任务栏和窗口使用 Flet 默认图标。

**实现：**
- `app.py` 新增 `page.window.icon = str(ROOT_DIR / "pic" / "cleaner.ico")`
- 使用绝对路径确保图标正确加载

---

## 修改文件清单（2026-05-30 更新）

| 文件 | 变更类型 |
|---|---|
| `ui/i18n.py` | **新增**：多语言翻译系统（190+ 键） |
| `services/llm_config_manager.py` | **新增**：LLM 配置管理器单例 |
| `ui/views/calendar_view.py` | **新增**：日历视图（月网格、任务圆点、年/月导航） |
| `core/constants/defaults.py` | 新增 `LLM_DEFAULTS` 默认配置字典 |
| `services/llm_service.py` | 配置管理器集成 + `rebuild()` + i18n |
| `ui/views/todo_view.py` | 日历视图集成 + 四视图切换 + 紧迫排序 + i18n |
| `ui/views/stats_view.py` | i18n + 变量名冲突修复 |
| `ui/views/settings_view.py` | 助手设置表单 + i18n |
| `ui/components/task_item.py` | i18n |
| `ui/components/date_picker.py` | i18n（周期/月份名改为函数） |
| `ui/theme.py` | i18n（主题色标签） |
| `app.py` | 窗口图标 + LLMConfigManager 初始化 |
| `README.md` | 补充新功能列表 |

---

## 18. 重复任务（每期独立完成）

**问题：** 持续任务（有 start_date 和 end_date）只支持"完成一次即视为完成"，无法表达"每天跑步""隔天吃药"等每期独立完成的需求。

**数据模型：**
- `repeat_days: int = 0`：重复间隔天数（0=不重复，1=每天，2=隔天，N=每N天）
- `repeat_mode: str = "once"`：完成模式。`"once"`=完成一次即整体完成，`"each"`=每期独立完成
- `completed_dates: list[str] = []`：JSON 数组，记录已完成的日期（ISO 格式）

**LLM 自动判断：**
- "每天跑步""每日打卡" → `repeat_days=1, repeat_mode="each"`
- "隔天吃药" → `repeat_days=2, repeat_mode="each"`
- "考试从6月1到3号" → `repeat_days=0, repeat_mode="once"`（或不设 repeat_days）

**实现：**

`core/models/task.py`：
- 新增 `is_recurring`、`repeat_occurrences`、`all_occurrences_done` 属性
- `mark_occurrence(d)` 标记某天完成，自动检查是否全部完成
- `occurrence_done(d)` 检查某天是否已完成

`services/llm_service.py`：
- `TaskPlan` / `PlannedTaskIntent` 新增 `repeat_days`、`repeat_mode` 字段
- 系统 prompt 新增 3 个示例（每天跑步、隔天吃药、持续考试）
- COMPLETE 分支："each" 模式调用 `mark_occurrence(today)` 而非 `mark_complete()`

`services/task_service.py`：
- `create_task()` / `create_tasks()` 新增 `repeat_days`、`repeat_mode` 参数

`storage/task_repo.py` / `storage/db.py`：
- 新增 `repeat_days`、`repeat_mode`、`completed_dates` 三列迁移
- INSERT/UPDATE SQL 更新为 8 字段

`ui/components/task_item.py`：
- 显示重复标签（"每天"、"每3天"）
- "each" 模式显示进度（如 "3/7 完成"）

`ui/views/calendar_view.py`：
- "each" 模式：在每个应完成的日期显示独立圆点，已完成用完成色
- `_tasks_for_date()` 和 `_task_dots_for_date()` 按重复计划迭代

`ui/views/stats_view.py`：
- 概览卡片：done/ongoing/expired 使用 `_is_done()` / `_is_ongoing()` / `_is_expired()` 辅助方法
- 今日待办："each" 模式检查今天是否在重复计划内且未完成
- 7 天趋势："each" 模式按 `all_occurrences_done` 判断完成

`ui/i18n.py`：
- 新增 `repeat.every_day`、`repeat.every_n_days`、`repeat.once_mode`、`repeat.each_mode`、`repeat.progress`

---

## 修改文件清单（2026-05-30 重复任务更新）

| 文件 | 变更类型 |
|---|---|
| `storage/db.py` | 新增 3 列迁移（repeat_days, repeat_mode, completed_dates） |
| `core/models/task.py` | 新增字段 + 重复任务属性/方法 |
| `services/llm_service.py` | TaskPlan/Intent 新增字段 + 系统 prompt 更新 |
| `services/task_service.py` | create_task/create_tasks 新增参数 |
| `storage/task_repo.py` | COLUMNS + INSERT/UPDATE SQL 更新 |
| `ui/components/task_item.py` | 重复标签 + 进度显示 |
| `ui/views/calendar_view.py` | each 模式多日显示 + 圆点颜色 |
| `ui/views/stats_view.py` | 重复任务完成/过期/今日判断 |
| `ui/i18n.py` | 5 个重复相关翻译键 |
| `README.md` | 新增重复任务功能 |

---

## 19. 重复任务编辑 + 日历/统计显示

**问题：** 重复任务只能通过 AI 对话创建，无法手动编辑；日历详情和统计今日待办不显示重复信息。

**实现：**

`services/task_service.py`：
- `update_task()` 新增 `repeat_days` 和 `repeat_mode` 参数，支持从 UI 保存重复设置

`ui/views/todo_view.py`：
- `save_task()` 传递 `repeat_days` 和 `repeat_mode` 到 `update_task()`

`ui/components/task_item.py`：
- 编辑视图新增重复设置行：间隔天数输入框 + 模式下拉选择（完成一次即可 / 每期独立）
- `edit_clicked()` 前置填入当前 repeat_days 和 repeat_mode
- `save_clicked()` 读取并更新 repeat 字段，刷新日期显示

`ui/views/calendar_view.py`：
- 详情面板每个任务行下方显示重复标签（如"每天 · 3/7"）
- 使用 `tk.repeat_occurrences` 计算总数

`ui/views/stats_view.py`：
- 今日待办每个任务名后追加重复标签和进度

`ui/i18n.py`：
- 新增 `task.repeat`（"重复"）、`task.repeat_days_unit`（"天"）

---

## 修改文件清单（2026-05-30 重复编辑更新）

| 文件 | 变更类型 |
|---|---|
| `services/task_service.py` | `update_task()` 新增 repeat_days/repeat_mode 参数 |
| `ui/views/todo_view.py` | `save_task()` 传递 repeat 字段 |
| `ui/components/task_item.py` | 编辑 UI：重复间隔输入 + 模式选择 |
| `ui/views/calendar_view.py` | 详情面板显示重复标签 + 进度 |
| `ui/views/stats_view.py` | 今日待办显示重复标签 |
| `ui/i18n.py` | 2 个新翻译键 |
| `README.md` | 更新重复任务功能描述 |

---

## 21. 重复任务 UI 改进

**问题：** 重复任务的设置和显示不够直观——数字输入框不清晰，完成模式表述抽象，显示标签冗长混乱。

**实现：**

频率选择改为预设 Chip 行：
- "不重复" / "每天" / "隔天" / "每3天" / "每7天" / "自定义"
- 点击 Chip 自动设置 repeat_days，"自定义" 展开数字输入框

完成模式改为带说明的 Chip 选项：
- "只需一次"（once）— 说明："整个周期只需完成一次"
- "每次都要"（each）— 说明："每个实例独立完成"
- 只在 repeat_days > 0 时显示

显示标签改进：
- 卡片：`📅 06-01 ~ 06-07 · 每天 · 3/7 已打卡`
- 日历详情：`每天 · 3/7 已打卡`
- 统计今日：`每天 · 3/7 已打卡`

i18n 更新：新增 `repeat.not_repeat`、`repeat.every_2_days`、`repeat.every_3_days`、`repeat.every_7_days`、`repeat.custom`、`repeat.once_desc`、`repeat.each_desc`、`task.repeat_mode_label`；更新 `repeat.once_mode`（"只需一次"）、`repeat.each_mode`（"每次都要"）、`repeat.progress`（"已打卡"）

---

## 修改文件清单（2026-05-30 重复 UI 改进）

| 文件 | 变更类型 |
|---|---|
| `ui/components/task_item.py` | 编辑 UI：Chip 频率选择 + 带说明的模式选项 |
| `ui/views/todo_view.py` | 新建任务区同样改为 Chip + 模式选项 + i18n 刷新 |
| `ui/views/calendar_view.py` | 详情面板标签改进（已打卡/只需一次） |
| `ui/views/stats_view.py` | 今日待办标签改进 |
| `ui/i18n.py` | 新增/更新 8 个翻译键 |

---

## 20. 新建任务时设置重复

**问题：** 新建任务时无法设置重复间隔和模式，只能通过 AI 对话或事后编辑。

**实现 `ui/views/todo_view.py`：**
- 新增 `_new_repeat_days`（数字输入框）和 `_new_repeat_mode`（下拉选择）控件
- `_new_repeat_row` 行包含标签 + 输入框 + 单位 + 下拉，初始隐藏
- `_toggle_new_task_picker()` 打开/关闭时同步显示/隐藏重复行
- `add_clicked()` 读取 repeat 值传递给 `create_task()`，完成后重置
- `_rebuild_main_labels()` 更新重复设置标签（语言切换）

---

## 修改文件清单（2026-05-30 新建重复更新）

| 文件 | 变更类型 |
|---|---|
| `ui/views/todo_view.py` | 新建任务区新增重复设置行 + 传递参数 + 重置 + i18n |
| `optimize.md` | 追加本次优化记录 |

---

## 22. 聊天助手界面美化

**问题：**
1. drawer 底部 padding 导致内容偏上，与应用底部不齐
2. 聊天区域灰色背景 (`PANEL_BG`) 与 drawer 背景不一致，突兀
3. 打开聊天时无主动问好，用户缺少引导
4. drawer 阴影太重（`blur_radius=16, opacity=0.25`）
5. 无快捷操作入口，常用指令需手动输入
6. 助手设置无预设性格，用户需自行编写 prompt

**实现 `ui/views/todo_view.py`：**

*底部对齐 + 阴影 + 背景：*
- `padding`: `Padding(16, 12, 16, 16)` → `Padding(16, 12, 16, 0)` 底部不加 padding
- `shadow`: `blur_radius=16, opacity=0.25` → `blur_radius=8, opacity=0.1, offset=2`
- 聊天历史 `bgcolor`: `PANEL_BG` → `ft.Colors.SURFACE`

*首次打开问好：*
- 新增 `_chat_greeted: bool` 状态，标记是否已问好
- `_toggle_chat_drawer()` 打开时：若未问好，调用 `_append_chat_greeting()`
- `_append_chat_greeting()`：复用 `_get_greeting()` + 紧急任务摘要逻辑，以助手气泡追加到 chat_history
- 无紧急任务时显示 emoji 庆祝（移除 box-drawing ASCII art，避免中文/emoji 对齐问题）

*快捷气泡：*
- 输入框上方新增 `_quick_chips` Row，4 个 `ft.ActionChip`：
  - "最近七天计划" → 触发 plan_tasks
  - "我接下来该做什么" → 触发 plan_tasks
  - "查看所有待办" → 触发 list_tasks
  - "清除已完成" → 触发 clear completed
- `_on_quick_chip()` 设置输入值并触发 `handle_user_message`

**实现 `ui/views/settings_view.py`：**

*预设性格：*
- `PERSONA_PRESETS` 字典：阿喵（猫娘）、阿汪（柴犬）、砖家（学术专家）、小冰（温柔助手）、默认
- `_build_assistant()` 在聊天人设文本框上方新增 Chip 行
- `_on_preset_select()` 将对应 prompt 填入 `_chat_prompt_field.value`，标记 dirty 显示保存按钮

**实现 `services/llm_service.py`：**
- planner system prompt 新增"最近七天计划"示例，识别为 `plan_tasks` action

**实现 `ui/i18n.py`：**
- 新增 `chat.chip_7day_plan`、`chat.chip_what_next`、`chat.chip_all_tasks`、`chat.chip_clear_done`
- 新增 `settings.assistant.presets`

---

## 修改文件清单（2026-05-30 聊天美化更新）

| 文件 | 变更类型 |
|---|---|
| `ui/views/todo_view.py` | drawer 底部/阴影/背景 + 问好气泡 + 快捷 Chip |
| `ui/views/settings_view.py` | 预设性格 Chip 行 |
| `services/llm_service.py` | system prompt 新增七天计划示例 |
| `ui/i18n.py` | 新增 5 个翻译键 |
| `README.md` | 更新功能列表 |

---

## 23. GitHub 风格热力图 + 每日完成度判定

**问题：** 统计页"今日待办"列表信息密度低，无法直观看到历史任务完成情况。

**实现 `storage/daily_assessment_repo.py`（全新）：**
- `daily_assessments` 表：`date TEXT PRIMARY KEY, score INTEGER, manual INTEGER`
- `score`: 0-4（0=无活动, 1=1-25%, 2=26-50%, 3=51-75%, 4=76-100%）
- `manual`: 0=自动计算, 1=用户手动设定
- 方法：`get(date)`、`get_range(start, end)`、`upsert(date, score, manual)`
- 遵循 `setting_repo.py` 模式，构造函数中 `_ensure_table()`

**改造 `ui/views/stats_view.py`：**
- 删除 `_build_today()` 方法，替换为 `_build_heatmap()`
- 热力图 + 今日评估合并为一张卡片
- 热力图显示全年 365 天（12×12px 方块），含未来日期（浅灰底色）
- 年份切换：`[◀] 2026 [▶]` 导航按钮
- 顶部月份标签，左侧星期标签（一~日），网格支持水平滚动
- 今日评估区域在热力图下方，直接点击 Chip 选择完成度
- 用户评估后热力图方格颜色即时更新（无需刷新）
- 历史日期点击弹出判定对话框，确认后方格颜色即时更新
- `_backfill_assessments()`: 打开统计页时自动回填当年未手动评估的历史日期
  - 统计每天应完成/已完成任务数，按比例映射 score
  - `manual=1` 的记录不覆盖
- `_schedule_midnight_refresh()`: 每天 0 点自动刷新进入下一天评估

**改造 `app.py`：**
- 实例化 `DailyAssessmentRepo()`，传给 `TodoApp`

**改造 `ui/views/todo_view.py`：**
- `TodoApp.__init__` 新增 `assessment_repo` 参数
- `StatsView` 构造传入 `assessment_repo`

**i18n 新增：**
- `stats.heatmap_title`、`stats.heatmap_weekdays`、`stats.heatmap_month`
- `stats.assess_title`、`stats.assess_hint`、`stats.assess_0`~`stats.assess_4`
- `stats.assess_today_title`、`stats.assess_today_hint`、`stats.assess_today_done`

---

## 修改文件清单（2026-05-30 热力图更新）

| 文件 | 变更类型 |
|---|---|
| `storage/daily_assessment_repo.py` | **新增**：每日完成度评估存储 |
| `ui/views/stats_view.py` | 删除今日待办，新增热力图 + 判定对话框 + 自动回填 |
| `app.py` | 实例化 DailyAssessmentRepo，传给 TodoApp |
| `ui/views/todo_view.py` | 接收 assessment_repo，传给 StatsView |
| `ui/i18n.py` | 新增 11 个热力图/判定翻译键 |
| `README.md` | 更新统计功能 + 项目结构 |
| `optimize.md` | 追加本次优化记录 |

---

## 24. 统计页主题适配

**问题：** 统计页图表和热力图颜色使用硬编码 hex 值（Morandi 色系），深色/浅色模式切换时颜色不协调。

**实现 `ui/views/stats_view.py`：**
- 环状图 4 段颜色：硬编码 hex → Material 3 语义色（`TERTIARY`/`SECONDARY`/`ERROR`/`OUTLINE`）
- 热力图方块颜色：5 级 `GREEN` 透明度（0.15/0.30/0.55/0.85），自动适配深色/浅色模式
- 概览卡片图标颜色：统一使用语义色（`PRIMARY`/`TERTIARY`/`SECONDARY`/`ERROR`）
- 柱状图颜色：`TERTIARY`（新增）/ `PRIMARY`（完成）
- 评估对话框 Chip 颜色：使用 `PRIMARY_CONTAINER`/`PRIMARY` 语义色

**效果：** 所有颜色随主题自动适配，深色/浅色模式下视觉一致。

---

## 25. 项目清理

**清理内容：**
- 删除 8 个空 Python 骨架文件：`core/models/setting.py`、`services/calendar_service.py`、`ui/app_shell.py`、`ui/state.py`、`ui/components/empty_state.py`、`ui/components/settings_menu.py`、`ui/components/settings_panels.py`、`ui/components/task_list.py`
- 删除重复数据库目录 `core/data/`
- 删除测试产物 `data/llm_complete_test.db`

**文档更新：**
- `FILE_CONTENTS.md`：删除第 6 节空骨架文件列表，更新各文件描述（stats_view 热力图、settings_view 预设性格、todo_view 聊天改进、app.py 依赖注入、新增 daily_assessment_repo 和 llm_config_manager）
- `README.md`：更新功能列表和项目结构

---

## 修改文件清单（2026-05-30 主题适配+清理）

| 文件 | 变更类型 |
|---|---|
| `ui/views/stats_view.py` | 颜色改为 Material 3 语义色 |
| `FILE_CONTENTS.md` | 删除空骨架节 + 更新文件描述 |
| `README.md` | 更新功能列表 + 项目结构 |
| 8 个空 .py 文件 | **删除** |
| `core/data/` | **删除**（重复数据库目录） |
| `data/llm_complete_test.db` | **删除**（测试产物） |

---

## 26. 窗口位置和大小记忆

**问题：** 每次启动应用窗口都回到固定位置（1100×800），用户需手动调整。

**实现 `app.py`：**
- 启动时从 `SettingRepo` 读取 `win.width`、`win.height`、`win.left`、`win.top`，恢复窗口几何
- 注册 `page.window.on_event` 回调，监听 `RESIZE` 和 `MOVE` 事件
- 每次 resize/move 时通过 `repo.set()` 持久化到 `settings` 表
- 无历史记录时使用默认值（1100×800，居中）

**效果：** 关闭后重新打开，窗口自动恢复到上次的位置和大小。

---

## 27. 人机交互动画与交互优化

**问题：** 任务操作缺乏视觉反馈，用户感知不到操作结果；聊天体验缺少动态感；侧边栏选中状态不明显；缺少快捷键支持。

**实现方案：**

### A1. 任务卡片添加/删除动画
**文件：** `ui/components/task_item.py`, `ui/views/todo_view.py`
- `Task` 类新增 `animate_entrance()` 方法：新任务淡入+缩放（opacity 0→1, scale 0.95→1.0, 250ms）
- `Task` 类新增 `animate_exit()` 方法：删除任务淡出+缩小（opacity 1→0, scale 1.0→0.9, 250ms）
- `add_clicked()` 添加任务后调用 `animate_entrance()`
- `task_delete()` 确认删除前调用 `animate_exit()`

### A5. 聊天气泡入场动画
**文件：** `ui/views/todo_view.py`
- `_append_bubble()` 方法添加 `animate_opacity=300` + `animate_scale=300`
- 气泡初始状态 opacity=0, scale=0.9，添加后 50ms 延迟后恢复为 opacity=1, scale=1.0

### A6. 任务完成勾选动画
**文件：** `ui/components/task_item.py`
- `status_changed()` 改为 async 方法
- 完成时卡片背景短暂变为 PRIMARY 高亮色（300ms），然后恢复为完成态样式

### B3. 任务卡片hover阴影
**文件：** `ui/components/task_item.py`
- `display_view` 容器添加 `on_hover` 回调
- 鼠标悬停时 `blur_radius=8, opacity=0.15, offset=2` 的阴影
- 鼠标离开时阴影恢复为 0

### A2. 侧边栏选中指示
**文件：** `ui/views/todo_view.py`
- 侧边栏图标按钮包装在 `ft.Container` 中（40×40, border_radius=8）
- 选中项添加 `bgcolor=with_opacity(0.15, PRIMARY)` 背景高亮
- 图标颜色同步变为 PRIMARY

### B2. Toast通知系统
**文件：** `ui/views/todo_view.py`, `ui/i18n.py`
- `_show_toast()` 方法：右下角弹出通知，300ms 淡入，2秒后 300ms 淡出
- 添加任务、删除任务、清除已完成任务后自动触发
- 新增 i18n 键：`toast.task_added`, `toast.task_deleted`, `toast.tasks_cleared`

### B1. 键盘快捷键
**文件：** `app.py`, `ui/views/todo_view.py`
- `app.py` 注册 `page.on_keyboard_event` 回调
- `todo_view.py` 新增 `_setup_keyboard_shortcuts()` 和 `_on_keyboard_event()` 方法
- 支持：Ctrl+Z（撤销）、Ctrl+N（聚焦新任务输入框）、Esc（关闭活动面板/抽屉）

**效果：** 任务操作有明确的动画反馈和 Toast 提示；聊天体验更流畅；侧边栏选中状态一目了然；键盘用户可快速操作。

---

## 28. 热力图hover效果

**问题：** 热力图单元格缺乏交互反馈，用户无法直观感知可点击区域。

**实现 `ui/views/stats_view.py`：**
- 单元格添加 `on_hover` 回调
- 悬停时边框变为 PRIMARY 色（1.5px），离开时恢复透明
- 单元格 data 改为 dict 格式存储日期和背景色

**效果：** 鼠标悬停时单元格边框高亮，增强可交互感。

---

## 29. 页面切换过渡动画

**问题：** 视图切换时内容瞬间切换，缺乏过渡感。

**实现 `ui/views/todo_view.py`：**
- `_sync_content_views` 改为 async 方法
- 切换前内容区淡出（opacity 0, 150ms）
- 切换可见性后内容区淡入（opacity 1, 150ms）
- 所有调用方改为 async/await

**效果：** 视图切换有平滑的淡入淡出过渡。

---

## 30. 任务进度条

**问题：** 持续任务无法直观看到时间进度。

**实现 `ui/components/task_item.py`：**
- 有 end_date 且未完成的任务显示进度条
- 进度 = (当前时间 - 开始时间) / (结束时间 - 开始时间)
- 颜色随进度变化：<70% PRIMARY，70-90% ORANGE，≥90% ERROR
- 进度条高度 3px，圆角 2px

**效果：** 持续任务卡片下方显示时间进度条，临近截止时颜色变红。

---

## 31. 移除聊天抽屉透明度变化

**问题：** 打开聊天抽屉时内容区变半透明，视觉干扰大于帮助。

**实现 `ui/views/todo_view.py`：**
- 移除 `_toggle_chat_drawer` 中 `self._content_column.opacity = 0.5` 相关代码
- 抽屉开关仅控制抽屉自身透明度

**效果：** 打开聊天抽屉时内容区保持不变，减少视觉干扰。

---

## 32. 空状态插图

**问题：** 无任务时任务列表空白，用户不知道如何操作。

**实现 `ui/views/todo_view.py`, `ui/i18n.py`：**
- `_build_empty_state()` 方法：显示图标 + 引导文字
- 使用 `ft.Stack` 将空状态叠加在任务列表上方
- `before_update` 中根据可见任务数显示/隐藏空状态
- 新增 i18n 键：`empty.no_tasks`, `empty.add_hint`

**效果：** 无任务时显示"暂无待办任务"+"在上方输入框添加新任务"引导。

---

## 33. 任务列表加载动画

**问题：** 任务列表加载时瞬间显示所有任务，缺乏动态感。

**实现 `ui/views/todo_view.py`：**
- `load_tasks` 新增 `animate` 参数
- `_animate_task_list()` 方法：任务卡片依次淡入，30ms间隔
- `did_mount` 中触发动画

**效果：** 应用启动时任务卡片依次淡入，增强加载感。

---

## 34. 深浅模式适配

**问题：** Toast通知在浅色模式下背景和文字颜色相近，看不清。

**实现 `ui/views/todo_view.py`：**
- 背景色改为 `SURFACE_CONTAINER_HIGHEST`（深浅模式自适应）
- 添加 `OUTLINE_VARIANT` 边框增加层次感
- 文字色改为 `ON_SURFACE`（深浅模式自适应）

**效果：** Toast在深色/浅色模式下都有良好的可读性。

---

## 修改文件清单（2026-06-05 人机交互优化 完整）

| 文件 | 变更类型 |
|---|---|
| `ui/components/task_item.py` | 入场/退出动画、hover阴影、完成高亮、进度条 |
| `ui/views/todo_view.py` | Toast通知、侧边栏指示、键盘快捷键、气泡动画、页面过渡、空状态、列表加载动画 |
| `ui/views/stats_view.py` | 热力图hover效果 |
| `ui/i18n.py` | 新增 5 个键（3 toast + 2 empty state） |
| `app.py` | 注册键盘快捷键处理器 |
| `optimize.md` | 追加优化记录 |
| `人机交互技术体现.md` | **新增** — 人机交互技术分析文档 |

---

## 35. CustomDatePicker 两列布局

**问题：** 创建/修改任务时的日历选择器（CustomDatePicker）是单列布局，日历和时间选择、重复设置纵向排列，占用过多垂直空间。

**实现 `ui/components/date_picker.py`：**
- `_build()` 重构为两列布局：左侧 = 日历网格（expand=True），右侧 = 文本输入 + 提示 + 时间选择 + 额外控件（expand=True）
- 新增 `extra_controls` 构造参数，允许调用方注入额外控件到右列
- 月份导航移至日历列顶部居中
- 下拉框宽度从 110px 缩至 90px，适配右列空间

**实现 `ui/views/todo_view.py`：**
- 重复选项行（`_new_repeat_row`）通过 `extra_controls=[self._new_repeat_row]` 注入日期选择器右列
- 创建顺序调整：先构建重复行，再创建 CustomDatePicker

**效果：** 日历选择器左右分列，日历和设置并排显示，空间利用更高效。

---

## 36. 任务卡片拖动圆角修复

**问题：** 拖动任务卡片时，卡片本身是圆角，但拖拽代理的背景是方角，视觉违和。

**实现 `ui/components/task_item.py`：**
- `Task.__init__` 添加 `border_radius=12` 和 `clip_behavior=ft.ClipBehavior.ANTI_ALIAS`
- Flet 的 ReorderableListView 拖拽代理会继承控件的圆角和裁剪属性

**效果：** 拖动卡片时圆角边角不再露出方角背景。

---

## 37. 移除重复模式选择

**问题：** 重复任务需要选择模式（只需一次 / 每次都要），增加了不必要的复杂度。语义上"重复"本身就隐含"每次都要"，"不重复"隐含"只需一次"。

**实现 `ui/components/task_item.py`：**
- 删除所有模式选择 UI：`_edit_mode_once`、`_edit_mode_each`、`_edit_mode_desc`、`_edit_mode_row`
- 删除 `_on_mode_select`、`_sync_mode_ui`、`_get_edit_repeat_mode` 方法
- `save_clicked` 直接设置 `self.repeat_mode = "each"`

**实现 `ui/views/todo_view.py`：**
- 删除新建任务时的模式选择：`_new_mode_once`、`_new_mode_each`、`_new_mode_desc`、`_new_mode_row`
- 删除 `_on_new_mode_select` 方法
- `_get_new_repeat_mode()` 简化为始终返回 `"each"`
- `_rebuild_main_labels` 不再更新模式标签

**效果：** 选择重复后直接生效，无需再选模式，交互步骤减少。

---

## 38. 进度条恢复与六级色阶

**问题：** 进度条在之前的 git 回滚中丢失；原有三级色阶变化不够细腻。

**实现 `ui/components/task_item.py`：**
- 有 `end_date` 且未完成的任务显示进度条
- 进度 = (当前时间 - 开始时间) / (结束时间 - 开始时间)
- 六级色阶：
  - < 30%：PRIMARY（蓝）
  - 30-45%：TEAL（青）
  - 45-60%：AMBER（琥珀）
  - 60-75%：ORANGE（橙）
  - 75-90%：DEEP_ORANGE（深橙）
  - ≥ 90%：ERROR（红）
- 进度条高度 3px，圆角 2px

**效果：** 持续任务显示时间进度条，颜色随进度平滑过渡，临近截止时变红。

---

## 39. taste-skill 设计原则优化

**问题：** 应用视觉细节（阴影、圆角、标签样式、间距）不够精致，参照 taste-skill 设计系统进行选择性优化。

**实现方案（仅改视觉样式，不改功能逻辑）：**

### A. 阴影扩散化
- **task_item.py**：hover 阴影 `blur_radius=8, opacity=0.1, offset=2` → `blur_radius=20, opacity=0.06, offset=Offset(0, 4)`
- **calendar_view.py**：grid_card / detail_card `blur_radius=20, opacity=0.04, offset=Offset(0, 4)`
- **todo_view.py**：聊天抽屉 `blur_radius=8, opacity=0.1` → `blur_radius=16, opacity=0.06`

### B. 圆角统一 12px
- **task_item.py**：卡片 border_radius 10→12
- **calendar_view.py**：grid_card / detail_card border_radius 16→12

### C. 状态标签 pill 化
- **task_item.py**：completed_tag / expired_tag `border_radius=4` → `border_radius=10`，padding 对称化

### D. 卡片内间距优化
- **task_item.py**：`padding=Padding(28, 8, 40, 8)` → `Padding(20, 12, 20, 12)`（对称、舒适）

### E. 边框 whisper 化
- **task_item.py**：卡片边框改为 `ft.Border.all(1, with_opacity(0.5, OUTLINE_VARIANT))`

**效果：** 阴影更柔和扩散，圆角统一，标签胶囊化，间距对称，边框若有若无——整体视觉更精致。

---

## 40. .agents/ 加入 .gitignore

**问题：** `npx skills` 安装的 skill 文件存放在 `.agents/` 目录，不应提交到版本控制。

**实现 `.gitignore`：** 添加 `.agents/` 和 `skills-lock.json`

**效果：** skill 安装产物不被 git 跟踪。

---

## 修改文件清单（2026-06-05 UI优化 完整）

| 文件 | 变更类型 |
|---|---|
| `ui/components/date_picker.py` | 两列布局 + extra_controls 参数 |
| `ui/components/task_item.py` | 拖动圆角修复、模式选择移除、进度条恢复+六级色阶、taste-skill 样式优化 |
| `ui/views/todo_view.py` | 模式选择移除、重复选项注入 picker 右列、抽屉阴影优化 |
| `ui/views/calendar_view.py` | 阴影+圆角优化 |
| `.gitignore` | 添加 .agents/、skills-lock.json |

---

## 41. 窗口状态记忆修复 + 多显示器支持

**问题：**
1. 窗口位置/大小不记忆 — 数据库中 `win.*` 全为 `None`
2. 启动时黑屏闪烁 — 默认大小窗口先出现再跳变为正确大小
3. 不支持多显示器 — 窗口可能恢复到已断开的显示器上
4. 不记忆最大化/全屏状态

**根因分析：**
- `app.py` 监听 `ft.WindowEventType.RESIZE` / `MOVE`，但 Flet 0.85.2 实际触发的是 `RESIZED` / `MOVED`（过去时态），事件类型不匹配导致回调从未执行
- Flet 原生窗口在 Python 代码执行前就已创建并可见，`main()` 中设置尺寸有延迟

**修复 `app.py`：**
- 事件类型：`RESIZE` → `RESIZED`，`MOVE` → `MOVED`
- 新增 `before_main()` 回调：在 `main()` 之前恢复窗口尺寸/位置，减少跳变
- 新增 `_get_screens()`：通过 Win32 API `EnumDisplayMonitors` 获取所有显示器工作区域
- 新增 `_pos_on_screen()`：判断窗口位置是否有 30% 以上面积落在可见屏幕内，否则居中到主屏幕
- 新增 `MAXIMIZE`/`UNMAXIMIZE`/`ENTER_FULL_SCREEN`/`LEAVE_FULL_SCREEN` 事件监听，持久化 `win.maximized` 和 `win.full_screen`
- 启动时优先恢复全屏，其次最大化

**效果：** 窗口状态正确记忆和恢复，多显示器场景下窗口始终出现在可见屏幕上。

---

## 42. 系统通知功能

**问题：** 无 OS 级通知能力，用户无法在任务到期、需要打卡时收到系统弹窗提醒。

**新增 `services/notification_service.py`：**
- `NotificationService` 单例，基于 `winotify` 库发送 Windows 原生 toast 通知
- `send(title, body, tag)`：发送通知，自动跳过免打扰时段，按 tag 去重（每任务每天一次）
- `send_test()`：开发者测试接口，绕过 DND 和去重
- 免打扰逻辑：支持跨午夜时段（如 23:00–08:00 → now >= 23:00 OR < 08:00）
- 去重：`_sent_tags: set[str]` 存储已发 tag，每天自动清空
- 设置通过 `SettingRepo` 持久化：`notif.enabled`、`notif.advance_min`、`notif.dnd_enabled`、`notif.dnd_start`、`notif.dnd_end`

**新增 `services/notification_scheduler.py`：**
- `NotificationScheduler` 静态类，`start()` 启动 asyncio 后台循环（60 秒间隔）
- 检查逻辑：
  - 重复 "each"：今日是打卡日且未打卡 → "打卡提醒"
  - 重复 "once"：今日在范围内且未完成 → "进行中"
  - 单次 + end_date：距截止 ≤ advance_min → "即将过期"
  - 已过期（截止日 < 今天，未完成）→ "已过期"
- tag 格式：`task_{id}_{date}_{type}`，确保每任务每天每种类型只通知一次

**改造 `ui/views/settings_view.py`：**
- 新增 "通知" 导航项（`NOTIFICATIONS_OUTLINED` 图标）
- `_build_notifications()`：启用开关、提前提醒时间下拉（5/15/30/60 分钟）、免打扰开关 + 时间范围下拉（30 分钟间隔）、测试通知按钮

**改造 `app.py`：**
- 初始化 `NotificationService.instance().load(repo)`
- 创建 `TaskRepository` 并启动 `NotificationScheduler.start()`
- 将 `notif_svc` 传递给 `TodoApp`

**新增 `winotify>=1.1.0` 依赖。**

---

## 43. 重复任务打卡实时更新

**问题：** 重复任务 "each" 模式下，勾选/取消勾选卡片后 "n/m 已打卡" 不更新。

**根因分析：**
- `task_item.py:status_changed()` 只设置 `self.completed = e.control.value`，从未调用 `mark_occurrence()`
- `todo_view.py:save_task()` 调用 `update_task()` 时未传递 `completed_dates`
- `task_service.py:update_task()` 无 `completed_dates` 参数
- `Task`（UI widget）与 `TaskRecord`（数据模型）是独立类，`Task` 缺少 `mark_occurrence`/`unmark_occurrence` 方法

**修复 `ui/components/task_item.py`：**
- `Task` 类新增 `mark_occurrence(d)` 和 `unmark_occurrence(d)` 方法
- `status_changed()` 改为：重复 each 模式下，勾选 → `mark_occurrence(today)`，取消 → `unmark_occurrence(today)`
- 打卡后调用 `_refresh_date_display()` 实时更新显示

**修复 `core/models/task.py`：**
- 新增 `unmark_occurrence(d)` 方法：从 `completed_dates` 移除日期，重置 `completed = False`

**修复 `services/task_service.py`：**
- `update_task()` 新增 `completed_dates: list[str] | None` 参数

**修复 `ui/views/todo_view.py`：**
- `save_task()` 传递 `task.completed_dates` 到 `update_task()`

**效果：** 勾选/取消勾选重复任务后，"n/m 已打卡" 实时更新。

---

## 修改文件清单（2026-06-06 通知+修复）

| 文件 | 变更类型 |
|---|---|
| `services/notification_service.py` | **新增**：系统通知服务（winotify、DND、去重） |
| `services/notification_scheduler.py` | **新增**：通知调度器（异步循环，任务检查） |
| `app.py` | 窗口状态修复（事件类型、多显示器、全屏）+ 通知系统初始化 |
| `ui/views/settings_view.py` | 新增"通知"设置分区 |
| `ui/views/todo_view.py` | 传递 notification_service + completed_dates |
| `ui/components/task_item.py` | 新增 mark/unmark_occurrence + 打卡实时更新 |
| `core/models/task.py` | 新增 unmark_occurrence |
| `services/task_service.py` | update_task 新增 completed_dates 参数 |
| `ui/i18n.py` | 新增 20 个通知相关翻译键 |
| `requirements.txt` | 新增 winotify>=1.1.0 |
| `README.md` | 新增系统通知功能、更新项目结构 |
| `optimize.md` | 追加本次优化记录 |

---

## 16. Onboarding 教程重写 + 设置页教程入口

**问题：**
1. `ElevatedButton` 在 Flet 0.80+ 已弃用，产生 DeprecationWarning
2. 原 onboarding 仅 4 步，功能介绍过于简略，缺少使用教程
3. 完成后无法再次查看教程

**修复 `ui/views/onboarding_view.py`：**
- 全部 `ft.ElevatedButton` → `ft.Button`
- 从 4 步扩展为 7 步：
  - Step 0：欢迎（大图标 + 描述 + 跳过按钮）
  - Step 1：功能概览（2×2 网格卡片，彩色背景）
  - Step 2：AI 助手教程（模拟聊天气泡展示 3 组对话示例）
  - Step 3：任务管理教程（6 项操作：添加/编辑/完成/拖拽/筛选/快捷键，两列网格）
  - Step 4：视图与通知教程（日历/统计/通知/重复任务 4 张卡片）
  - Step 5：API 设置（保留原有功能）
  - Step 6：完成（大图标 + 开始使用按钮）
- 视觉改进：步骤图标用 `border_radius=14` 的彩色容器，聊天气泡用 `PRIMARY_CONTAINER`/`SECONDARY_CONTAINER` 背景
- 新增 `is_revisit` 参数支持从设置页重新打开
- 导航按钮自动生成（有上一步时显示"上一步"，最后一步不显示"下一步"）

**修复 `ui/views/settings_view.py`：**
- 新增 `"tutorial"` 导航项（`SCHOOL_OUTLINED` 图标）
- 新增 `_build_tutorial()` 方法：标题 + 描述 + "查看教程" 按钮
- `_launch_tutorial()` 清除页面，显示 OnboardingView；完成后通过 `page._todo_app_ref` 恢复主应用

**修复 `app.py`：**
- `_show_main_app` 保存 `page._todo_app_ref = todo_app` 供教程返回时使用

**修复 `ui/i18n.py`：**
- 新增 `nav.tutorial`、AI 教程 7 个键、任务管理教程 7 个键、视图教程 5 个键、设置教程 3 个键，共 23 个翻译键

**效果：** 7 步交互式教程涵盖 AI 对话、任务管理、视图导航、快捷键；设置页可随时重新查看；无 DeprecationWarning。

---

## 修改文件清单（2026-06-06 Onboarding 重写）

| 文件 | 变更类型 |
|---|---|
| `ui/views/onboarding_view.py` | 全面重写：7 步教程、ft.Button、聊天气泡、网格卡片 |
| `ui/views/settings_view.py` | 新增"教程"导航项 + 教程启动/关闭逻辑 |
| `app.py` | 保存 `_todo_app_ref` 引用 |
| `ui/i18n.py` | 新增 23 个教程翻译键 + `nav.tutorial` |

---

## 44. UI 冻结彻底修复

**问题：** 任务创建或删除后 ~1 秒内所有控件无法交互。此前的 `_dirty` 标志优化（#43 前半部分）减少了不必要的排序，但冻结仍然存在。

**根因分析：**
每次 `update()` 调用都是同步 IPC 往返（Python → Flutter 引擎），包含控制树 diff 计算、序列化和传输。`TodoApp` 包含 50+ 任务控件，每次 `self.update()` 都要序列化整个子树。

| 流程 | 原始 update 次数 | 瓶颈 |
|------|------------------|------|
| 创建 | 3（self.update + task.update + page.update for toast） | 3 次 IPC |
| 删除 | 2（card.update + page.update for toast） | 2 次 IPC + 250ms sleep |

**修复方案：**

### A. `_needs_resort` 标志（todo_view.py）
- `before_update()` 中检查 `_needs_resort`，为 False 时直接返回，跳过排序+可见性循环
- 仅在任务列表真正变化时设置为 True（load_tasks, add_clicked, task_delete, clear_clicked, _on_sort_change, handle_user_message, _set_filter）
- `_dirty` 重命名为 `_needs_resort`（避免与 Flet 内部 `_dirty` dict 冲突）

### B. Card 级 update（task_item.py）
- `_on_card_hover`：`self.update()` → `card.update()`（仅更新卡片容器，不触发父级 before_update）
- `status_changed` 完成高亮：`self.update()` → `card.update()`

### C. 入场动画 fire-and-forget（todo_view.py）
- `add_clicked`：entrance 动画改为 `asyncio.ensure_future(_entrance())`，不阻塞主流程
- 一次 `self.update()` 完成：排序 + 任务列表 + toast

### D. 删除动画优化（todo_view.py）
- `task_delete._confirm`：动画前设置 `_needs_resort = False`，动画期间 `task.update()` 不触发排序
- 动画后恢复 `_needs_resort = True`，一次 `self.update()` 完成：排序 + 移除 + toast

### E. Toast 优化（todo_view.py）
- `_show_toast` 使用 `page.overlay` + Column(expand=True) + Row(alignment=END) 定位右下角
- 淡出后静默移除（不再调用最终的 `page.update()`）
- `_toast_fade_task` 管理：新 toast 自动取消上一个

**效果：**
| 流程 | 修复后 update 次数 | 说明 |
|------|-------------------|------|
| 创建 | 1（self.update 含 toast）+ fire-and-forget 动画 | 1 次 IPC |
| 删除 | 1（self.update 含 toast）+ 1 card.update（动画） | card.update 不触发父级排序 |

---

## 45. Onboarding 统一卡片高度 + 固定按钮位置

**问题：**
1. 各步骤内容高度不一，卡片大小不同
2. 导航按钮（上一步/下一步）位置随内容变化，交互不一致
3. 步骤 2（AI 教程 3 组聊天气泡）和步骤 4（视图教程垂直列表）超出视口

**修复 `ui/views/onboarding_view.py`：**

### A. 统一卡片结构
- `_build_step()` 重构：步骤构建器只返回内容 Column，dots + 按钮由 `_build_step()` 统一添加
- 内容区使用 `ft.Column(height=540, alignment=CENTER)` 包裹，所有步骤统一高度 + 垂直居中
- 底部导航固定在内容区下方，所有步骤位置一致

### B. 步骤内容优化
- Step 2（AI 教程）：3 组聊天气泡 → 2 组，气泡 padding 缩小 `(14,10)` → `(10,8)`
- Step 4（视图教程）：垂直列表 → 2×2 网格布局，图标缩小 44→36px

### C. 外层容器
- 卡片 padding `(48,36)` → `(40,24)`
- 各步骤 spacer 统一：dots 前 16px，dots 后 20px

---

## 46. Flet 0.85 API 兼容修复

**问题：**
1. `ft.Button(text=...)` → TypeError：Flet 0.85 Button 不接受 `text=` 关键字参数
2. `ft.OutlinedButton(text=...)` → 同上
3. `Task` 对象 `display_view` 在 `__init__` 时不存在（`build()` 懒创建）
4. `_dirty` 属性名与 Flet 内部 `_dirty` dict 冲突

**修复：**
- `ft.Button(text=X)` → `ft.Button(content=ft.Text(X))`（onboarding_view.py 5 处、settings_view.py 1 处）
- `ft.OutlinedButton(text=X)` → `ft.OutlinedButton(X)`（位置参数）
- `animate_entrance()` 移除，改用 `_is_new` 标志 + `build()` 设置 `opacity=0` + `add_clicked` fire-and-forget 动画
- `_dirty` 重命名为 `_needs_resort`

---

## 修改文件清单（2026-06-07 UI 冻结+Onboarding）

| 文件 | 变更类型 |
|---|---|
| `ui/views/todo_view.py` | `_needs_resort` 标志、toast 改用 page.overlay、add_clicked fire-and-forget、task_delete 动画前禁用排序、`_current_toast`/`_toast_fade_task` 管理 |
| `ui/components/task_item.py` | `_on_card_hover`/`status_changed` 改用 `card.update()`、`_is_new` 标志 |
| `ui/views/onboarding_view.py` | 统一卡片高度（540px Column）、固定按钮位置、2 组聊天气泡、Step 4 网格布局、Flet API 修复 |
| `ui/views/settings_view.py` | `ft.Button` API 修复 |
| `README.md` | 更新教程功能描述 |
| `optimize.md` | 追加本次优化记录 |

---

## 47. 子视图右上角关闭按钮

**问题：** 点击日历、设置、统计等子视图后，新界面覆盖主界面，用户需要再次点击侧边栏按钮才能返回主界面，操作不直观，用户找不到返回方式。

**实现：**

### A. 日历视图（calendar_view.py）
- 新增 `on_close` 回调参数
- 在 header 右上角添加关闭按钮（`ft.Icons.CLOSE`），位于年快进按钮右侧
- 点击关闭按钮触发 `on_close` 回调返回主界面

### B. 设置视图（settings_view.py）
- 新增 `on_close` 回调参数
- 新增顶部导航栏，包含"设置"标题 + 右上角关闭按钮
- 点击关闭按钮触发 `on_close` 回调返回主界面

### C. 统计视图（stats_view.py）
- 新增 `on_close` 回调参数
- 在标题行右上角添加关闭按钮，位于刷新按钮右侧
- 点击关闭按钮触发 `on_close` 回调返回主界面

### D. 主视图（todo_view.py）
- 创建各子视图时传入 `_close_view` 回调函数
- `_close_view` 调用 `_sync_content_views("main")` 返回主界面

### E. 国际化（i18n.py）
- 新增 `"settings.title"` 翻译（zh: "设置", en: "Settings")
- 新增 `"nav.settings"` 翻译（zh: "设置", en: "Settings")

---

## 修改文件清单（2026-06-07 关闭按钮）

| 文件 | 变更类型 |
|---|---|
| `ui/views/calendar_view.py` | 新增 `on_close` 参数 + 右上角关闭按钮 |
| `ui/views/settings_view.py` | 新增 `on_close` 参数 + 顶部导航栏 + 右上角关闭按钮 |
| `ui/views/stats_view.py` | 新增 `on_close` 参数 + 右上角关闭按钮 |
| `ui/views/todo_view.py` | 传入 `_close_view` 回调给各子视图 |
| `ui/i18n.py` | 新增 `settings.title`、`nav.settings` 翻译 |

---

## 48. 任务卡片操作按钮间距调整

**问题：** 任务卡片右侧的删除按钮与 ReorderableListView 的排序手柄（≡）靠得太近，不美观且容易误触。

**修复（task_item.py）：**
- 操作按钮行间距从 `spacing=0` 增加到 `spacing=8`
- 在删除按钮后面添加 `8px` 空白容器，与排序手柄保持距离

---

## 修改文件清单（2026-06-07 按钮间距）

| 文件 | 变更类型 |
|---|---|
| `ui/components/task_item.py` | 操作按钮间距调整（0→8）+ 删除按钮后添加空白间距 |

---

## 49. 定时提醒功能

**功能描述：** 为每个任务添加独立的定时提醒功能，用户可以设置具体的提醒时间，系统会在指定时间发送系统通知。

**实现：**

### A. 任务模型（task.py）
- 新增 `remind_time` 字段（"HH:MM" 格式）
- 更新 `from_row` 和 `to_db_values` 方法支持新字段

### B. 任务仓库（task_repo.py）
- 更新 `_COLUMNS` 和 `_INSERT_COLS` 包含 `remind_time`
- 更新 INSERT 和 UPDATE SQL 语句

### C. 数据库迁移（db.py）
- 新增 `remind_time` 列（TEXT 类型，默认空字符串）

### D. 任务服务（task_service.py）
- `create_task`、`create_tasks`、`update_task` 方法新增 `remind_time` 参数

### E. 任务编辑组件（task_item.py）
- 添加提醒时间开关和时间选择器（小时/分钟下拉框）
- 添加 `_on_remind_time_switch`、`_get_remind_time`、`_set_remind_time` 方法
- 在编辑界面显示提醒时间设置区域

### F. 通知调度器（notification_scheduler.py）
- 新增任务级别定时提醒检查逻辑
- 每分钟检查一次，在设置的提醒时间前后1分钟内发送通知

### G. 国际化（i18n.py）
- 新增 `task.remind_time`、`task.remind_time_label` 翻译
- 新增 `notif.scheduled`、`notif.body.scheduled` 翻译

### H. 主视图（todo_view.py）
- `load_tasks` 时加载 `remind_time` 字段
- `save_task` 时保存 `remind_time` 字段

---

## 修改文件清单（2026-06-07 定时提醒）

| 文件 | 变更类型 |
|---|---|
| `core/models/task.py` | 新增 `remind_time` 字段 |
| `storage/task_repo.py` | 更新数据库列和 SQL 语句 |
| `storage/db.py` | 新增数据库迁移 |
| `services/task_service.py` | 新增 `remind_time` 参数支持 |
| `services/notification_scheduler.py` | 新增定时提醒检查逻辑 |
| `ui/components/task_item.py` | 添加提醒时间选择器 UI |
| `ui/views/todo_view.py` | 加载和保存 `remind_time` |
| `ui/i18n.py` | 新增相关翻译 |
