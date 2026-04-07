# Flet 项目文件内容确认

更新时间：2026-04-07

## 项目描述

本项目面向“轻量化本地智能待办管理”场景，目标是构建可跨平台运行、可持续扩展的桌面任务系统。系统采用 Flet 实现图形界面，采用 SQLite 实现本地持久化，并以 core/storage/services/ui 的分层结构完成界面、业务与数据解耦。当前版本已实现任务新增、编辑、删除、完成状态切换、条件筛选与最近日期展示，支持从主界面进入设置中心，并提供双栏设置页框架。实验性运行结果表明，系统具备稳定的本地执行能力和良好的代码可维护性。该实现验证了“本地优先”方案在个人任务管理中的可行性，并为后续扩展日历联动、主题语言配置及大模型能力接入提供了工程基础。

## 1) 可运行入口与已实现模块

### app.py
- 作用：应用唯一入口文件。
- 当前内容：
  - 引入 `flet` 与 `TodoApp`。
  - 定义 `main(page)`：设置页面标题、滚动方式、内边距和根容器。
  - 包含 `if __name__ == "__main__": ft.run(main)`，可直接启动。

### requirements.txt
- 作用：运行环境版本锁定。
- 当前内容：
  - `Flet=0.84.0`
  - `Flutter=3.41.4`
  - `Pyodide=0.27.7`

### ui/views/todo_view.py
- 作用：主页面视图（待办 + 设置页占位）。
- 当前内容：
  - `TodoApp` 组件。
  - SQLite 本地存储：建表、读取、新增/更新、删除。
  - 任务筛选：all/active/completed。
  - 页面切换：主页面与设置页面之间切换。
  - 设置页面骨架：左列“设置列表（预留）”、右列“具体设置界面（预留）”。

### ui/components/task_item.py
- 作用：单个任务组件。
- 当前内容：
  - `Task` 组件。
  - 支持编辑、保存、删除、完成状态切换。
  - 状态变更后回写 SQLite（通过 `app.save_task(self)`）。

### data/tasks.db
- 作用：本地 SQLite 数据文件。
- 当前内容：
  - 二进制数据库文件，存储任务数据。

## 2) 已创建但暂为空的骨架文件

### core 层
- `core/__init__.py`：空。
- `core/models/__init__.py`：空。
- `core/models/task.py`：空（预留任务数据模型）。
- `core/models/setting.py`：空（预留设置数据模型）。
- `core/constants/__init__.py`：空。
- `core/constants/enums.py`：空（预留枚举定义）。
- `core/constants/defaults.py`：空（预留默认配置）。

### storage 层
- `storage/__init__.py`：空。
- `storage/db.py`：空（预留数据库连接与迁移）。
- `storage/task_repo.py`：空（预留任务仓储）。
- `storage/setting_repo.py`：空（预留设置仓储）。

### services 层
- `services/__init__.py`：空。
- `services/task_service.py`：空（预留任务业务逻辑）。
- `services/calendar_service.py`：空（预留日历查询逻辑）。
- `services/llm_service.py`：空（预留 LangChain/LLM 封装）。
- `services/nlp_task_parser.py`：空（预留自然语言任务解析）。

### ui 其他层
- `ui/__init__.py`：空。
- `ui/app_shell.py`：空（预留壳层路由）。
- `ui/i18n.py`：空（预留中英文文案）。
- `ui/state.py`：空（预留页面状态）。
- `ui/theme.py`：空（预留主题与字体）。

### ui/views
- `ui/views/__init__.py`：空。
- `ui/views/settings_view.py`：空（预留独立设置页实现）。
- `ui/views/calendar_view.py`：空（预留日历页实现）。

### ui/components
- `ui/components/__init__.py`：空。
- `ui/components/task_list.py`：空（预留任务列表组件）。
- `ui/components/settings_menu.py`：空（预留设置左侧菜单）。
- `ui/components/settings_panels.py`：空（预留设置右侧面板）。
- `ui/components/empty_state.py`：空（预留空状态组件）。


## 3) 当前启动方式

- 命令：`flet run app.py`

