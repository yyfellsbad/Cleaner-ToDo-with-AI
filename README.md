# Cleaner — AI 待办管理

基于 Flet 的桌面待办应用，支持自然语言（中文）驱动的任务管理，本地 SQLite 持久化，接入 DeepSeek API。

## 功能

- **AI 对话操作**：用自然语言新增、修改、删除、完成、查询、规划任务，支持 Markdown 渲染回复
- **AI 记忆系统**：记住最近 10 轮对话，重启不丢失（持久化到 SQLite）
- **任务规划**：AI 根据任务紧迫性推荐下一步行动
- **持续时间**：支持设置任务的开始和结束日期，自动范围检测（点第二个日期即变持续）
- **时间选择**：精确到小时/分钟，自适应布局（单日期/同天持续/跨天持续）
- **任务描述**：可选描述字段，点击展开查看详情
- **拖拽排序**：任务卡片可直接拖动调整顺序
- **任务排序**：默认按紧迫程度排序（过期 → 今日 → 近期 → 远期，已完成沉底），也支持按日期、名称、持续时间升降序排列
- **任务筛选**：全部 / 未完成 / 已完成 / 已过期 四档过滤
- **卡片状态标记**：已过期（半透明 + 过期标签）、已完成（加深 + 完成标签）、正在持续（绿色时间戳）
- **日期编辑**：点击任务日期可内联编辑（复用日历组件，自动填入已有日期/时间/范围）
- **删除二次确认**：删除操作需确认，防止误操作
- **撤销**：最多保留 20 步操作快照，随时回退
- **思考动画**：AI 处理时显示 ProgressRing + "思考中"提示
- **自定义标题栏**：替代原生 Windows 标题栏，与主题适配
- **数据统计**：环状图（任务分布）、概览卡片（总数/完成/完成率/过期）、GitHub 风格热力图（26 周任务活动，可手动评估每日完成度）、近 7 天趋势柱状图，入场动画
- **日历视图**：月网格展示任务圆点（莫兰迪色系），支持年/月切换，点击日期查看当天任务详情
- **重复任务**：支持"每天""隔天""每N天"重复模式，两种完成方式——一次即完成（如持续考试）和每期独立完成（如每天跑步），LLM 自动判断类型，卡片编辑器可手动设置重复间隔和模式，日历/统计视图显示重复进度
- **多语言支持**：中文/英文界面切换，实时刷新无需重启
- **VSCode 风格侧边栏**：智能助手、统计、日历、设置图标按钮
- **聊天侧边面板**：AI 助手从左侧弹出，内容自动让出空间，带动画效果。首次打开自动问好（含任务摘要），输入框上方快捷气泡（七天计划/接下来做什么/查看待办/清除已完成）
- **设置页面**：外观（浅色/深色/跟随系统 + 主题色）、语言、助手设置（API 密钥、Base URL、模型、预设性格阿喵/阿汪/砖家/小冰/默认、聊天人设、测试连接）
- **日期颜色编码**：今天（橙）、未来（蓝）、过期（灰）、正在持续（绿）
- **手动操作**：支持直接在右侧面板新增、编辑、删除任务

## 技术栈

| 层 | 技术 |
|---|---|
| UI | Flet 0.85 + flet-charts |
| AI | LangChain + DeepSeek（OpenAI 兼容接口） |
| 存储 | SQLite（本地，`data/tasks.db`） |
| 语言 | Python 3.12+ |

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API（复制后填入 DeepSeek Key）
cp .env.example .env

# 启动
python app.py
```

## 环境变量

在项目根目录创建 `.env`：

```
OPENAI_API_KEY=<your_deepseek_key>
OPENAI_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com/
OPENAI_TEMPERATURE=0.3
```

不配置 API Key 时，AI 对话不可用，手动任务操作仍正常运行。API 密钥、URL、模型、聊天人设也可在应用内「设置 → 助手设置」中配置，会自动保存。

## 项目结构

```
app.py                      # 入口（隐藏标题栏、窗口约束、主题初始化）
core/
  constants/enums.py        # TaskActionType 枚举（含 PLAN）
  constants/defaults.py     # LLM 默认配置值
  models/task.py            # TaskRecord（含 end_date、description）
storage/
  db.py                     # SQLite 连接、建表、自动迁移
  task_repo.py              # CRUD 仓储层
  setting_repo.py           # 键值设置存储
  daily_assessment_repo.py  # 每日完成度评估存储
services/
  task_service.py           # 业务逻辑、日期解析、try_parse_date
  llm_service.py            # LangChain 编排、意图规划、plan_tasks 工具
  llm_config_manager.py     # LLM 配置管理（API 密钥、URL、模型、人设）
  nlp_task_parser.py        # 正则回退解析器、持续时间解析
ui/
  theme.py                  # ThemeManager（浅色/深色/跟随系统、主题色、语言）、AppColors
  i18n.py                   # 多语言翻译系统（中/英，190+ 翻译键）
  views/todo_view.py        # 主视图（侧边栏、聊天面板、拖拽排序、筛选、排序）
  views/stats_view.py       # 统计页（环状图、柱状图、概览卡片、今日待办）
  views/calendar_view.py    # 日历页（月网格、任务圆点、年/月切换、日期任务详情）
  views/settings_view.py    # 设置页（外观/语言/助手设置，LLM 配置表单）
  components/task_item.py   # 卡片式任务（日期编辑器、描述、编辑/删除按钮、状态标记）
  components/date_picker.py # 自定义日历组件（自动范围、自适应时间、小时/分钟选择）
data/tasks.db               # 本地数据库（自动创建）
```

## 调试

```bash
# 测试 DeepSeek API 连通性
python scripts/test_model_connection.py
```
