# Cleaner — AI 待办管理

基于 Flet 的桌面待办应用，支持自然语言（中文）驱动的任务管理，本地 SQLite 持久化，接入 DeepSeek API。

## 功能

- **AI 对话操作**：用自然语言新增、修改、删除、完成、查询任务
- **删除二次确认**：删除操作需确认，防止误操作
- **撤销**：最多保留 20 步操作快照，随时回退
- **任务筛选**：all / active / completed 三档过滤
- **日期颜色编码**：今天（橙）、未来（蓝）、过期（灰）
- **可拖拽分栏**：左侧 AI 对话 + 右侧任务列表，宽度可拖拽调整
- **手动操作**：支持直接在右侧面板新增、编辑、删除任务

## 技术栈

| 层 | 技术 |
|---|---|
| UI | Flet 0.84 |
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

不配置 API Key 时，AI 对话不可用，手动任务操作仍正常运行。

## 项目结构

```
app.py                      # 入口
core/
  constants/enums.py        # TaskActionType 枚举
  models/task.py            # TaskRecord 数据模型
storage/
  db.py                     # SQLite 连接与建表
  task_repo.py              # CRUD 仓储层
services/
  task_service.py           # 业务逻辑、日期解析
  llm_service.py            # LangChain 编排、意图规划
  nlp_task_parser.py        # 正则回退解析器
ui/
  theme.py                  # 颜色常量、全局主题
  views/todo_view.py        # 主视图（TodoApp）
  components/task_item.py   # 单任务行组件
data/tasks.db               # 本地数据库（自动创建）
```

## 调试

```bash
# 测试 DeepSeek API 连通性
python scripts/test_model_connection.py
```
