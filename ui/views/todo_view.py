from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta

import flet as ft

from core.constants.enums import TaskActionType
from core.models.task import TaskRecord
from services.llm_service import LLMService
from services.task_service import TaskService
from ui.components.task_item import Task
from ui.theme import AppColors, ThemeManager


class TodoApp(ft.Column):
    def __init__(self, theme_manager: ThemeManager, repo=None):
        super().__init__()
        self.tm = theme_manager
        self.show_settings = False
        self.task_service = TaskService()
        self.llm_service = LLMService(self.task_service, setting_repo=repo)
        self.pending_confirmation_token = None
        self.undo_stack: list[list[TaskRecord]] = []
        self._restoring = False
        self.tasks = ft.ReorderableListView(
            expand=True,
            spacing=6,
            on_reorder=self._on_task_reorder,
        )
        self.load_tasks()

    # ── 数据操作 ──────────────────────────────────────────

    def load_tasks(self):
        self.tasks.controls.clear()
        for record in self.task_service.list_tasks():
            task = Task(
                record.name,
                self.task_delete,
                self,
                record.id,
                record.date,
                record.end_date,
                record.description,
                record.completed,
            )
            task.key = str(record.id) if record.id else str(id(task))
            self.tasks.controls.append(task)

    def save_task(self, task):
        if task.task_id is not None:
            self.push_undo_snapshot()

        if task.task_id is None:
            saved = self.task_service.create_task(
                task.task_name,
                task.date,
                task.completed,
                end_date=task.end_date,
                description=task.description,
            )
        else:
            saved = self.task_service.update_task(
                task.task_id,
                name=task.task_name,
                task_date=task.date,
                end_date=task.end_date,
                clear_end_date=(task.end_date is None),
                description=task.description,
                completed=task.completed,
            )
        task.task_id = saved.id

    def delete_task(self, task):
        if task.task_id:
            self.task_service.delete_task(task.task_id)

    # ── 页面切换 ──────────────────────────────────────────

    async def _close_window(self, e):
        await e.page.window.close()

    def open_settings(self, e):
        # 关闭聊天助手（互斥）
        if self._drawer_open:
            self._drawer.visible = False
            self._drawer_open = False
            self._sidebar_chat.icon_color = None
        # 切换设置
        self.show_settings = not self.show_settings
        self.main_view.visible = not self.show_settings
        self.settings_view.visible = self.show_settings
        self.update()

    _DRAWER_WIDTH = 400

    async def _toggle_chat_drawer(self, e):
        if self._drawer_open:
            self._drawer.opacity = 0
            self._content_column.opacity = 0.5
            self.update()
            await asyncio.sleep(0.3)
            self._drawer.visible = False
            self._drawer_open = False
            self._sidebar_chat.icon_color = None
            self._content_column.opacity = 1
        else:
            # 关闭设置（互斥）
            if self.show_settings:
                self.show_settings = False
                self.main_view.visible = True
                self.settings_view.visible = False
            self._content_column.opacity = 0.5
            self._drawer.visible = True
            self._drawer.opacity = 0
            self._drawer_open = True
            self._sidebar_chat.icon_color = ft.Colors.PRIMARY
            self.update()
            await asyncio.sleep(0.05)
            self._drawer.opacity = 1
            self._content_column.opacity = 1
        self.update()

    # ── 构建 UI ──────────────────────────────────────────

    def build(self):
        # ── 聊天抽屉内容 ──
        self.chat_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        self.command_input = ft.TextField(
            hint_text="输入内容可聊天，也可执行任务指令",
            expand=True,
            border_radius=20,
            content_padding=ft.Padding(16, 10, 16, 10),
            on_submit=self.handle_user_message,
        )
        self.ai_confirm_button = ft.FilledButton(
            content=ft.Text("确认删除"),
            visible=False,
            bgcolor=ft.Colors.ERROR,
            color=ft.Colors.ON_ERROR,
            on_click=self.confirm_pending_delete,
        )

        chat_input_row = ft.Row(
            spacing=8,
            controls=[
                self.command_input,
                ft.IconButton(
                    icon=ft.Icons.SEND_ROUNDED,
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    icon_color=ft.Colors.ON_PRIMARY_CONTAINER,
                    on_click=self.handle_user_message,
                ),
            ],
        )

        # 自定义抽屉面板
        self._drawer = ft.Container(
            width=self._DRAWER_WIDTH,
            visible=False,
            bgcolor=ft.Colors.SURFACE,
            border_radius=ft.BorderRadius(12, 4, 4, 12),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=16,
                color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
                offset=ft.Offset(4, 0),
            ),
            animate_opacity=300,
            padding=ft.Padding(16, 12, 16, 16),
            content=ft.Column(
                expand=True,
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                "智能助手",
                                weight=ft.FontWeight.W_600,
                                size=16,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=20,
                                on_click=self._toggle_chat_drawer,
                            ),
                        ],
                    ),
                    ft.Container(
                        expand=True,
                        border_radius=12,
                        bgcolor=AppColors.PANEL_BG,
                        padding=10,
                        content=self.chat_history,
                    ),
                    self.ai_confirm_button,
                    ft.Container(
                        padding=ft.Padding(0, 8, 0, 0),
                        content=chat_input_row,
                    ),
                ],
            ),
        )

        # ── 任务输入区 ──
        self.new_task = ft.TextField(
            hint_text="添加新任务",
            on_submit=self.add_clicked,
            expand=True,
            border_radius=10,
            content_padding=ft.Padding(16, 12, 16, 12),
        )

        # ── 新任务日期选择器（自定义，自动范围） ──
        from ui.components.date_picker import CustomDatePicker
        self._new_task_date_label = ft.Text(
            "",
            size=11,
            color=AppColors.TEXT_HINT,
            visible=False,
        )
        self._new_task_picker = CustomDatePicker(
            selected=date.today(),
            on_change=self._on_new_task_date_picked,
            show_time=True,
        )
        self._new_task_picker_panel = ft.Container(
            visible=False,
            padding=ft.Padding(0, 4, 0, 4),
            animate_opacity=250,
            animate_size=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=self._new_task_picker,
        )

        # ── 筛选按钮 ──
        self._filter_labels = ["all", "active", "completed", "expired"]
        self._filter_display = {
            "all": "全部",
            "active": "未完成",
            "completed": "已完成",
            "expired": "已过期",
        }
        self._current_filter = "all"
        self.filter_row = ft.Row(
            spacing=4,
            controls=[
                ft.Chip(
                    label=ft.Text(self._filter_display[label]),
                    data=label,
                    selected=(label == self._current_filter),
                    on_select=lambda e, l=label: self._set_filter(l),
                )
                for label in self._filter_labels
            ],
        )

        # ── 排序 ──
        self._sort_mode = "date_desc"
        self._sort_options = {
            "date_desc": "日期 ↓",
            "date_asc": "日期 ↑",
            "name_asc": "名称 A-Z",
            "name_desc": "名称 Z-A",
            "duration_desc": "持续时间 ↓",
            "duration_asc": "持续时间 ↑",
        }
        self._sort_dropdown = ft.Dropdown(
            value=self._sort_mode,
            options=[
                ft.dropdown.Option(key=k, text=v)
                for k, v in self._sort_options.items()
            ],
            text_size=13,
            content_padding=ft.Padding(8, 4, 8, 4),
            border_radius=6,
            width=140,
            on_select=self._on_sort_change,
        )

        self.items_left = ft.Text("0 项未完成", size=13, color=AppColors.TEXT_HINT)

        # ── 主任务面板 ──
        task_panel = ft.Container(
            expand=True,
            border_radius=12,
            padding=ft.Padding(16, 12, 16, 12),
            bgcolor=AppColors.PANEL_BG,
            content=ft.Column(
                expand=True,
                spacing=10,
                controls=[
                    # 顶部输入行
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                expand=True,
                                content=self.new_task,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CALENDAR_MONTH,
                                tooltip="设置日期",
                                icon_size=20,
                                on_click=self._toggle_new_task_picker,
                            ),
                            self._new_task_date_label,
                            ft.FloatingActionButton(
                                icon=ft.Icons.ADD,
                                mini=True,
                                on_click=self.add_clicked,
                            ),
                        ],
                    ),
                    # 日期选择面板（展开/收起）
                    self._new_task_picker_panel,
                    # 筛选行
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.filter_row,
                            ft.Row(
                                spacing=8,
                                controls=[
                                    self._sort_dropdown,
                                    ft.TextButton(
                                        content=ft.Text("清除已完成"),
                                        on_click=self.clear_clicked,
                                    ),
                                    ft.TextButton(
                                        content=ft.Text("撤销"),
                                        on_click=self.undo_last,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Divider(height=1),
                    # 任务列表
                    ft.Container(
                        expand=True,
                        content=self.tasks,
                    ),
                    # 底部状态栏
                    self.items_left,
                ],
            ),
        )

        # ── 左侧边栏（VSCode 风格）──
        self._sidebar_chat = ft.IconButton(
            icon=ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED,
            icon_size=22,
            tooltip="智能助手",
            on_click=self._toggle_chat_drawer,
        )
        sidebar = ft.Container(
            width=48,
            bgcolor=ft.Colors.SURFACE,
            padding=ft.Padding(0, 8, 0, 8),
            content=ft.Column(
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(expand=True),
                    self._sidebar_chat,
                    ft.IconButton(
                        icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
                        icon_size=22,
                        tooltip="日历（即将推出）",
                        disabled=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS_OUTLINED,
                        icon_size=22,
                        tooltip="设置",
                        on_click=self.open_settings,
                    ),
                ],
            ),
        )

        # ── 自定义标题栏（替代原生 Windows 标题栏）──
        title_bar = ft.WindowDragArea(
            content=ft.Container(
                bgcolor=ft.Colors.SURFACE,
                padding=ft.Padding(12, 6, 6, 6),
                content=ft.Row(
                    controls=[
                        ft.Text(
                            value="Cleaner",
                            size=14,
                            weight=ft.FontWeight.W_600,
                        ),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.REMOVE_ROUNDED,
                            icon_size=18,
                            on_click=lambda e: setattr(
                                e.page.window, "minimized", True
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CROP_SQUARE_ROUNDED,
                            icon_size=18,
                            on_click=lambda e: setattr(
                                e.page.window,
                                "maximized",
                                not e.page.window.maximized,
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE_ROUNDED,
                            icon_size=18,
                            on_click=self._close_window,
                        ),
                    ],
                ),
            ),
        )

        # ── 主视图 ──
        self.main_view = ft.Column(
            expand=True,
            spacing=12,
            visible=not self.show_settings,
            controls=[task_panel],
        )

        # ── 设置视图 ──
        from ui.views.settings_view import SettingsView

        self.settings_view = ft.Column(
            expand=True,
            spacing=12,
            visible=self.show_settings,
            controls=[SettingsView(self.tm)],
        )

        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.spacing = 0
        self._drawer_open = False
        self._content_column = ft.Column(
            expand=True,
            spacing=12,
            animate_opacity=200,
            controls=[
                self.main_view,
                self.settings_view,
            ],
        )
        self.controls = [
            title_bar,
            ft.Row(
                expand=True,
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    sidebar,
                    self._drawer,
                    self._content_column,
                ],
            ),
        ]

    # ── 生命周期 ──────────────────────────────────────────

    # ── 任务操作 ──────────────────────────────────────────

    async def add_clicked(self, e):
        if self.new_task.value:
            self.push_undo_snapshot()
            picker = self._new_task_picker
            task_record = self.task_service.create_task(
                self.new_task.value,
                task_date=picker.range_start,
                end_date=picker.range_end,
            )
            task = Task(
                task_record.name,
                self.task_delete,
                self,
                task_record.id,
                task_record.date,
                task_record.end_date,
                task_record.description,
                task_record.completed,
            )
            task.key = str(task_record.id)
            self.tasks.controls.append(task)
            self.new_task.value = ""
            self._new_task_date_label.visible = False
            self._new_task_picker_panel.visible = False
            picker.reset()
            await self.new_task.focus()
            self.update()

    async def _toggle_new_task_picker(self, e):
        panel = self._new_task_picker_panel
        if panel.visible:
            # 关闭：先淡出再隐藏
            panel.opacity = 0
            self.update()
            await asyncio.sleep(0.25)
            panel.visible = False
        else:
            # 打开：先显示再淡入
            panel.visible = True
            panel.opacity = 0
            self.update()
            await asyncio.sleep(0.05)
            panel.opacity = 1
        self.update()

    def _on_new_task_date_picked(self, start: datetime, end: datetime | None):
        self._update_new_task_date_label()
        self.update()

    def _update_new_task_date_label(self):
        picker = self._new_task_picker
        start = picker.range_start
        end = picker.range_end
        if start:
            label = self._format_date_label(start)
            if end:
                # 同天持续：只显示一次日期 + 时间范围
                if start.date() == end.date() and (end.hour or end.minute):
                    end_label = f"{end.hour:02d}:{end.minute:02d}"
                    label = f"{label} ~ {end_label}"
                else:
                    end_label = self._format_date_label(end)
                    label = f"{label} ~ {end_label}"
            self._new_task_date_label.value = label
            self._new_task_date_label.visible = True
        else:
            self._new_task_date_label.visible = False

    @staticmethod
    def _format_date_label(d) -> str:
        if isinstance(d, datetime):
            d_date = d.date()
            has_time = bool(d.hour or d.minute)
        else:
            d_date = d
            has_time = False

        today = date.today()
        if d_date == today:
            label = "今天"
        elif d_date == today + timedelta(days=1):
            label = "明天"
        elif d_date == today + timedelta(days=2):
            label = "后天"
        else:
            label = d_date.strftime("%m-%d")

        if has_time:
            label += f" {d.hour:02d}:{d.minute:02d}"
        return label

    def task_delete(self, task):
        self.push_undo_snapshot()
        self.tasks.controls.remove(task)
        self.delete_task(task)
        self.update()

    def _on_task_reorder(self, e):
        old_index = e.old_index
        new_index = e.new_index
        if old_index == new_index:
            return
        controls = self.tasks.controls
        item = controls.pop(old_index)
        controls.insert(new_index, item)
        self.update()

    def clear_clicked(self, e):
        self.push_undo_snapshot()
        for task in self.tasks.controls[:]:
            if task.completed:
                self.tasks.controls.remove(task)
                self.delete_task(task)
        self.update()

    # ── 生命周期 & 状态同步 ──────────────────────────────

    def before_update(self):
        if not hasattr(self, "items_left"):
            return
        self._sync_filter_highlight()
        self._apply_sort()
        status = self._current_filter
        count = 0
        expired_count = 0
        for task in self.tasks.controls:
            is_expired = task.expired
            try:
                task.visible = (
                    status == "all"
                    or (status == "active" and not task.completed)
                    or (status == "completed" and task.completed)
                    or (status == "expired" and is_expired)
                )
            except RuntimeError:
                pass
            if not task.completed:
                count += 1
            if is_expired:
                expired_count += 1
        self.items_left.value = f"{count} 项未完成" + (
            f"，{expired_count} 项已过期" if expired_count else ""
        )

    def _apply_sort(self):
        controls = self.tasks.controls
        if len(controls) <= 1:
            return
        mode = self._sort_mode

        def sort_key(task):
            if mode == "date_asc":
                return (task.date, task.task_id or 0)
            if mode == "date_desc":
                return (-task.date.toordinal(), -(task.task_id or 0))
            if mode == "name_asc":
                return (task.task_name.lower(), task.task_id or 0)
            if mode == "name_desc":
                return (task.task_name.lower(), -(task.task_id or 0))
            if mode == "duration_asc":
                dur = (task.end_date - task.date).days if task.end_date else 0
                return (dur, task.task_id or 0)
            if mode == "duration_desc":
                dur = (task.end_date - task.date).days if task.end_date else 0
                return (-dur, -(task.task_id or 0))
            return (-task.date.toordinal(), -(task.task_id or 0))

        controls.sort(key=sort_key)

    def _on_sort_change(self, e):
        self._sort_mode = e.control.value
        self.update()

    # ── 聊天交互 ──────────────────────────────────────────

    async def handle_user_message(self, e):
        text = (self.command_input.value or "").strip()
        if not text:
            return

        await self._append_bubble(text, is_user=True)
        self.command_input.value = ""
        self.update()

        # 思考中动画
        thinking_bubble = self._create_thinking_bubble()
        self.chat_history.controls.append(thinking_bubble)
        self.update()

        def _remove_thinking():
            if thinking_bubble in self.chat_history.controls:
                self.chat_history.controls.remove(thinking_bubble)

        confirm_words = {"确认", "是", "yes", "y", "ok", "好的", "行", "确认删除"}
        cancel_words = {"取消", "不用", "算了", "no", "n"}
        if self.pending_confirmation_token and text.lower() in {
            w.lower() for w in confirm_words
        }:
            _remove_thinking()
            await self.confirm_pending_delete(e)
            return
        if self.pending_confirmation_token and text.lower() in {
            w.lower() for w in cancel_words
        }:
            _remove_thinking()
            self.pending_confirmation_token = None
            self.ai_confirm_button.visible = False
            await self._append_bubble("已取消删除操作。", is_user=False)
            self.command_input.value = ""
            self.update()
            return

        # 后台执行 LLM
        planned = await asyncio.to_thread(self.llm_service.plan, text)
        mutating_actions = {
            TaskActionType.CREATE,
            TaskActionType.UPDATE,
            TaskActionType.COMPLETE,
            TaskActionType.UNCOMPLETE,
        }
        if planned.action in mutating_actions:
            self.push_undo_snapshot()

        result = await asyncio.to_thread(
            self.llm_service.process,
            text, current_status=self.current_filter_status(), intent=planned
        )

        _remove_thinking()
        await self._append_bubble(result.message, is_user=False)
        self.ai_confirm_button.visible = result.pending_confirmation
        self.pending_confirmation_token = result.confirmation_token
        self.load_tasks()
        self.update()

    def _create_thinking_bubble(self) -> ft.Container:
        return ft.Container(
            alignment=ft.Alignment(-1.0, 0),
            padding=ft.Padding(8, 0, 40, 0),
            content=ft.Container(
                padding=ft.Padding(14, 10, 14, 10),
                border_radius=ft.BorderRadius(16, 16, 16, 4),
                bgcolor=AppColors.BUBBLE_ASSISTANT,
                content=ft.Row(
                    spacing=4,
                    controls=[
                        ft.ProgressRing(width=14, height=14, stroke_width=2),
                        ft.Text("思考中", size=13, color=AppColors.TEXT_HINT),
                    ],
                ),
            ),
        )

    async def confirm_pending_delete(self, e):
        if not self.pending_confirmation_token:
            await self._append_bubble("没有待确认的删除操作。", is_user=False)
            self.ai_confirm_button.visible = False
            self.update()
            return

        self.push_undo_snapshot()
        result = self.llm_service.confirm_delete(self.pending_confirmation_token)
        self.pending_confirmation_token = None
        self.ai_confirm_button.visible = False
        await self._append_bubble(result.message, is_user=False)
        self.load_tasks()
        self.update()

    async def _append_bubble(self, text: str, is_user: bool):
        bubble = ft.Container(
            alignment=ft.Alignment(1.0 if is_user else -1.0, 0),
            padding=ft.Padding(40 if is_user else 8, 0, 8 if is_user else 40, 0),
            content=ft.Container(
                padding=ft.Padding(14, 10, 14, 10),
                border_radius=ft.BorderRadius(16, 16, 4, 16)
                if is_user
                else ft.BorderRadius(16, 16, 16, 4),
                bgcolor=AppColors.BUBBLE_USER
                if is_user
                else AppColors.BUBBLE_ASSISTANT,
                content=ft.Text(
                    text,
                    color=AppColors.BUBBLE_USER_TEXT,
                    size=14,
                    selectable=True,
                ) if is_user else ft.Markdown(
                    text,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                ),
            ),
        )
        self.chat_history.controls.append(bubble)

    # ── 筛选 & 撤销 ──────────────────────────────────────

    def current_filter_status(self) -> str:
        return self._current_filter

    def _set_filter(self, label: str):
        self._current_filter = label
        self.update()

    def _sync_filter_highlight(self):
        for chip in self.filter_row.controls:
            chip.selected = chip.data == self._current_filter

    def push_undo_snapshot(self):
        if self._restoring:
            return
        current = self.task_service.list_tasks(status="all")
        snapshot = [
            TaskRecord(name=t.name, date=t.date, completed=t.completed)
            for t in current
        ]
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def undo_last(self, e):
        if not self.undo_stack:
            return

        snapshot = self.undo_stack.pop()
        self._restoring = True
        try:
            self.task_service.replace_all_tasks(snapshot)
        finally:
            self._restoring = False
        self.load_tasks()
        self.update()
