from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta

import flet as ft

from core.constants.enums import TaskActionType
from core.models.task import TaskRecord
from services.llm_service import LLMService
from services.task_service import TaskService
from ui.components.task_item import Task
from ui.i18n import t
from ui.theme import AppColors, ThemeManager


class TodoApp(ft.Column):
    def __init__(self, theme_manager: ThemeManager, repo=None, config_manager=None,
                 assessment_repo=None, notification_service=None):
        super().__init__()
        self.tm = theme_manager
        self._config_manager = config_manager
        self._assessment_repo = assessment_repo
        self._notif = notification_service
        self.show_settings = False
        self.show_stats = False
        self.show_calendar = False
        self.task_service = TaskService()
        self.llm_service = LLMService(self.task_service, setting_repo=repo, config_manager=config_manager)
        if config_manager:
            config_manager._on_changed = lambda: self.llm_service.rebuild()
        self.pending_confirmation_token = None
        self.undo_stack: list[list[TaskRecord]] = []
        self._restoring = False
        self._needs_resort = True  # needs sort/filter on next before_update()
        self._toast_fade_task = None
        self._current_toast = None
        self.tasks = ft.ReorderableListView(
            expand=True,
            spacing=10,
            on_reorder=self._on_task_reorder,
        )
        self.load_tasks()

    # ── 数据操作 ──────────────────────────────────────────

    def load_tasks(self):
        self._needs_resort = True
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
                record.repeat_days,
                record.repeat_mode,
                record.completed_dates,
            )
            task.remind_time = getattr(record, 'remind_time', '')
            task.key = str(record.id) if record.id else str(id(task))
            self.tasks.controls.append(task)

    def _show_toast(self, message: str, duration: int = 2000):
        """显示右下角 Toast 通知。仅一次 page.update()，淡出后静默移除。"""
        if self._toast_fade_task and not self._toast_fade_task.done():
            self._toast_fade_task.cancel()
            # 清理上一个 toast
            if self._current_toast and self._current_toast in self.page.overlay:
                self.page.overlay.remove(self._current_toast)

        toast = ft.Container(
            padding=ft.Padding(16, 10, 16, 10),
            border_radius=8,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            animate_opacity=300,
            opacity=1,
            content=ft.Text(message, color=ft.Colors.ON_SURFACE, size=13),
        )
        # Column 控制垂直（底部），Row 控制水平（右侧）
        wrapper = ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.END,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.Container(
                            padding=ft.Padding(0, 0, 20, 20),
                            content=toast,
                        ),
                    ],
                ),
            ],
        )
        self._current_toast = wrapper
        self.page.overlay.append(wrapper)
        self.page.update()  # 唯一一次 page.update

        async def _fade_out():
            await asyncio.sleep(duration / 1000)
            toast.opacity = 0
            self.page.update()  # 触发动画
            await asyncio.sleep(0.3)
            if wrapper in self.page.overlay:
                self.page.overlay.remove(wrapper)
            # 不再调用 page.update()，静默移除

        self._toast_fade_task = asyncio.ensure_future(_fade_out())

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
                remind_time=getattr(task, 'remind_time', ''),
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
                repeat_days=task.repeat_days,
                repeat_mode=task.repeat_mode,
                completed_dates=task.completed_dates,
                remind_time=getattr(task, 'remind_time', ''),
            )
        task.task_id = saved.id

    def delete_task(self, task):
        if task.task_id:
            self.task_service.delete_task(task.task_id)

    # ── 页面切换 ──────────────────────────────────────────

    def _rebuild_views(self):
        from ui.views.settings_view import SettingsView
        from ui.views.stats_view import StatsView
        from ui.views.calendar_view import CalendarView

        def _close_view(e):
            self._sync_content_views("main")
            self.update()

        # 重建设置视图
        self.settings_view.controls = [
            SettingsView(self.tm, self._config_manager, on_lang_change=self._rebuild_views, notification_service=self._notif, on_close=_close_view)
        ]
        # 重建统计视图
        new_stats = StatsView(self.task_service, self._assessment_repo, on_close=_close_view)
        new_stats.visible = self.show_stats
        self._content_column.controls.remove(self.stats_view)
        self.stats_view = new_stats
        self._content_column.controls.append(self.stats_view)
        # 重建日历视图
        new_cal = CalendarView(task_service=self.task_service, on_close=_close_view)
        new_cal.visible = self.show_calendar
        self._content_column.controls.remove(self.calendar_view)
        self.calendar_view = new_cal
        self._content_column.controls.append(self.calendar_view)
        # 重建主视图中的 UI 元素（筛选、排序、状态栏等）
        self._rebuild_main_labels()
        self.update()

    def _rebuild_main_labels(self):
        # 更新筛选按钮文字
        self._filter_display = {
            "all": t("filter.all"),
            "active": t("filter.active"),
            "completed": t("filter.completed"),
            "expired": t("filter.expired"),
        }
        for chip in self.filter_row.controls:
            key = chip.data
            chip.label = ft.Text(self._filter_display[key])
        # 更新排序下拉框选项
        self._sort_options = {
            "urgency_asc": t("sort.urgency"),
            "date_desc": t("sort.date_desc"),
            "date_asc": t("sort.date_asc"),
            "name_asc": t("sort.name_asc"),
            "name_desc": t("sort.name_desc"),
            "duration_desc": t("sort.duration_desc"),
            "duration_asc": t("sort.duration_asc"),
        }
        self._sort_dropdown.options = [
            ft.dropdown.Option(key=k, text=v) for k, v in self._sort_options.items()
        ]
        # 更新按钮文字
        self._clear_btn.content = ft.Text(t("btn.clear_completed"))
        self._undo_btn.content = ft.Text(t("btn.undo"))
        # 更新侧边栏 tooltips
        self._sidebar_chat.content.tooltip = t("sidebar.chat")
        self._sidebar_stats.content.tooltip = t("sidebar.stats")
        self._sidebar_calendar.content.tooltip = t("sidebar.calendar")
        self._sidebar_settings.content.tooltip = t("sidebar.settings")
        # 更新输入框 hint
        self.command_input.hint_text = t("chat.input_hint")
        self.new_task.hint_text = t("task.add_hint")
        # 更新重复设置标签
        new_labels = [
            t("repeat.not_repeat"), t("repeat.every_day"),
            t("repeat.every_2_days"), t("repeat.every_3_days"),
            t("repeat.every_7_days"), t("repeat.custom"),
        ]
        for i, chip in enumerate(self._new_freq_chips.controls):
            chip.label = ft.Text(new_labels[i], size=11)
        self._new_repeat_row.controls[0] = ft.Text(t("task.repeat"), size=12, color=AppColors.TEXT_HINT)
        # 更新快捷气泡
        chip_keys = ["chat.chip_7day_plan", "chat.chip_what_next", "chat.chip_all_tasks", "chat.chip_clear_done"]
        for i, chip in enumerate(self._quick_chips.controls):
            chip.label = ft.Text(t(chip_keys[i]), size=11)

    async def _close_window(self, e):
        await e.page.window.close()

    def _sync_content_views(self, active: str):
        """统一切换内容视图：main / stats / calendar / settings 四选一。"""
        self.show_stats = active == "stats"
        self.show_calendar = active == "calendar"
        self.show_settings = active == "settings"
        self.main_view.visible = active == "main"
        self.stats_view.visible = active == "stats"
        self.calendar_view.visible = active == "calendar"
        self.settings_view.visible = active == "settings"
        # 更新侧边栏选中状态
        self._sidebar_stats.bgcolor = ft.Colors.with_opacity(0.15, ft.Colors.PRIMARY) if self.show_stats else None
        self._sidebar_calendar.bgcolor = ft.Colors.with_opacity(0.15, ft.Colors.PRIMARY) if self.show_calendar else None
        self._sidebar_settings.bgcolor = ft.Colors.with_opacity(0.15, ft.Colors.PRIMARY) if self.show_settings else None
        self._sidebar_stats.content.icon_color = ft.Colors.PRIMARY if self.show_stats else None
        self._sidebar_calendar.content.icon_color = ft.Colors.PRIMARY if self.show_calendar else None
        self._sidebar_settings.content.icon_color = ft.Colors.PRIMARY if self.show_settings else None

    def open_settings(self, e):
        self._sync_content_views("settings" if not self.show_settings else "main")
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
            self._sidebar_chat.bgcolor = None
            self._sidebar_chat.content.icon_color = None
            self._content_column.opacity = 1
        else:
            self._content_column.opacity = 0.5
            self._drawer.visible = True
            self._drawer.opacity = 0
            self._drawer_open = True
            self._sidebar_chat.bgcolor = ft.Colors.with_opacity(0.15, ft.Colors.PRIMARY)
            self._sidebar_chat.content.icon_color = ft.Colors.PRIMARY
            self.update()
            await asyncio.sleep(0.05)
            self._drawer.opacity = 1
            self._content_column.opacity = 1
            # 首次打开时问好
            if not self._chat_greeted:
                self._chat_greeted = True
                await self._append_chat_greeting()
        self.update()

    def _make_quick_chip_handler(self, message: str):
        async def handler(e):
            self.command_input.value = message
            self.update()
            await self.handle_user_message(None)
        return handler

    def open_stats(self, e):
        if not self.show_stats:
            self._sync_content_views("stats")
            self.stats_view.animate_in()
        else:
            self._sync_content_views("main")
        self.update()

    def open_calendar(self, e):
        if not self.show_calendar:
            self._sync_content_views("calendar")
            self.calendar_view.refresh()
        else:
            self._sync_content_views("main")
        self.update()

    # ── 构建 UI ──────────────────────────────────────────

    def build(self):
        # ── 聊天抽屉内容 ──
        self.chat_history = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        self.command_input = ft.TextField(
            hint_text=t("chat.input_hint"),
            expand=True,
            border_radius=20,
            content_padding=ft.Padding(16, 10, 16, 10),
            on_submit=self.handle_user_message,
        )
        self.ai_confirm_button = ft.FilledButton(
            content=ft.Text(t("chat.confirm_delete")),
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

        # 快捷气泡
        quick_chip_data = [
            ("chat.chip_7day_plan", "帮我看看最近七天的计划"),
            ("chat.chip_what_next", "我接下来该做什么"),
            ("chat.chip_all_tasks", "查看所有待办"),
            ("chat.chip_clear_done", "清除已完成的任务"),
        ]
        self._quick_chips = ft.Row(
            spacing=6, wrap=True,
            controls=[
                ft.Chip(
                    label=ft.Text(t(key), size=11),
                    data=msg,
                    on_click=self._make_quick_chip_handler(msg),
                )
                for key, msg in quick_chip_data
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
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(2, 0),
            ),
            animate_opacity=300,
            padding=ft.Padding(16, 12, 16, 0),
            content=ft.Column(
                expand=True,
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                t("chat.title"),
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
                        bgcolor=ft.Colors.SURFACE,
                        padding=10,
                        content=self.chat_history,
                    ),
                    self.ai_confirm_button,
                    self._quick_chips,
                    ft.Container(
                        padding=ft.Padding(0, 8, 0, 8),
                        content=chat_input_row,
                    ),
                ],
            ),
        )

        # ── 任务输入区 ──
        self.new_task = ft.TextField(
            hint_text=t("task.add_hint"),
            on_submit=self.add_clicked,
            on_focus=self._on_new_task_focus,
            expand=True,
            border_radius=10,
            content_padding=ft.Padding(16, 12, 16, 12),
        )

        # ── 新任务重复设置：频率 Chips（先建，再传给 picker） ──
        self._new_repeat_presets = [
            (0, t("repeat.not_repeat")),
            (1, t("repeat.every_day")),
            (2, t("repeat.every_2_days")),
            (3, t("repeat.every_3_days")),
            (7, t("repeat.every_7_days")),
            (-1, t("repeat.custom")),
        ]
        self._new_freq_chips = ft.Row(
            spacing=4, wrap=True,
            controls=[
                ft.Chip(
                    label=ft.Text(label, size=11),
                    data=days,
                    selected=(days == 0),
                    on_select=lambda e, d=days: self._on_new_freq_select(d),
                )
                for days, label in self._new_repeat_presets
            ],
        )
        self._new_custom_days = ft.TextField(
            width=60, text_size=13,
            content_padding=ft.Padding(8, 4, 8, 4),
            border_radius=6,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="N",
            visible=False,
        )
        self._new_custom_row = ft.Row(
            spacing=6, visible=False,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(t("repeat.custom"), size=11, color=AppColors.TEXT_HINT),
                self._new_custom_days,
                ft.Text(t("task.repeat_days_unit"), size=11),
            ],
        )
        self._new_repeat_row = ft.Column(
            spacing=4, visible=False, tight=True,
            controls=[
                ft.Text(t("task.repeat"), size=12, color=AppColors.TEXT_HINT),
                self._new_freq_chips,
                self._new_custom_row,
            ],
        )

        # ── 新任务日期选择器（重复选项传入右列） ──
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
            extra_controls=[self._new_repeat_row],
        )
        self._new_task_picker_panel = ft.Container(
            visible=False,
            padding=ft.Padding(0, 4, 0, 4),
            animate_opacity=250,
            animate_size=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(
                spacing=0,
                tight=True,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.CLOSE_ROUNDED,
                                icon_size=16,
                                tooltip=t("task.close"),
                                on_click=self._close_picker,
                            ),
                        ],
                    ),
                    self._new_task_picker,
                ],
            ),
        )

        self._new_task_desc = ft.TextField(
            hint_text=t("task.desc_hint"),
            text_size=13,
            content_padding=ft.Padding(8, 6, 8, 6),
            border_radius=8,
            multiline=True,
            min_lines=1,
            max_lines=3,
            visible=False,
        )

        # ── 筛选按钮 ──
        self._filter_labels = ["all", "active", "completed", "expired"]
        self._filter_display = {
            "all": t("filter.all"),
            "active": t("filter.active"),
            "completed": t("filter.completed"),
            "expired": t("filter.expired"),
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
        self._sort_mode = "urgency_asc"
        self._sort_options = {
            "urgency_asc": t("sort.urgency"),
            "date_desc": t("sort.date_desc"),
            "date_asc": t("sort.date_asc"),
            "name_asc": t("sort.name_asc"),
            "name_desc": t("sort.name_desc"),
            "duration_desc": t("sort.duration_desc"),
            "duration_asc": t("sort.duration_asc"),
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

        self._clear_btn = ft.TextButton(
            content=ft.Text(t("btn.clear_completed")),
            on_click=self.clear_clicked,
        )
        self._undo_btn = ft.TextButton(
            content=ft.Text(t("btn.undo")),
            on_click=self.undo_last,
        )
        self.items_left = ft.Text(t("status.items_left", 0), size=13, color=AppColors.TEXT_HINT)

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
                            ft.FloatingActionButton(
                                icon=ft.Icons.ADD,
                                mini=True,
                                on_click=self.add_clicked,
                            ),
                            ft.Container(
                                expand=True,
                                content=self.new_task,
                            ),
                            self._new_task_date_label,
                        ],
                    ),
                    # 日期选择面板（展开/收起）
                    self._new_task_picker_panel,
                    # 描述输入
                    self._new_task_desc,
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
                                    self._clear_btn,
                                    self._undo_btn,
                                ],
                            ),
                        ],
                    ),
                    ft.Divider(height=1),
                    # 任务列表
                    ft.Container(
                        expand=True,
                        padding=ft.Padding(0, 0, 8, 0),
                        content=self.tasks,
                    ),
                    # 底部状态栏
                    self.items_left,
                ],
            ),
        )

        # ── 左侧边栏（VSCode 风格）──
        self._sidebar_chat = ft.Container(
            width=40,
            height=40,
            border_radius=8,
            content=ft.IconButton(
                icon=ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED,
                icon_size=22,
                tooltip=t("sidebar.chat"),
                on_click=self._toggle_chat_drawer,
            ),
        )
        self._sidebar_stats = ft.Container(
            width=40,
            height=40,
            border_radius=8,
            content=ft.IconButton(
                icon=ft.Icons.BAR_CHART_OUTLINED,
                icon_size=22,
                tooltip=t("sidebar.stats"),
                on_click=self.open_stats,
            ),
        )
        self._sidebar_calendar = ft.Container(
            width=40,
            height=40,
            border_radius=8,
            content=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
                icon_size=22,
                tooltip=t("sidebar.calendar"),
                on_click=self.open_calendar,
            ),
        )
        self._sidebar_settings = ft.Container(
            width=40,
            height=40,
            border_radius=8,
            content=ft.IconButton(
                icon=ft.Icons.SETTINGS_OUTLINED,
                icon_size=22,
                tooltip=t("sidebar.settings"),
                on_click=self.open_settings,
            ),
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
                    self._sidebar_stats,
                    self._sidebar_calendar,
                    self._sidebar_settings,
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
            visible=not self.show_settings and not self.show_stats and not self.show_calendar,
            controls=[task_panel],
        )

        # ── 关闭视图回调 ──
        def _close_view(e):
            self._sync_content_views("main")
            self.update()

        # ── 设置视图 ──
        from ui.views.settings_view import SettingsView

        self.settings_view = ft.Column(
            expand=True,
            spacing=12,
            visible=self.show_settings,
            controls=[SettingsView(self.tm, self._config_manager, on_lang_change=self._rebuild_views, notification_service=self._notif, on_close=_close_view)],
        )

        # ── 统计视图 ──
        from ui.views.stats_view import StatsView

        self.stats_view = StatsView(self.task_service, self._assessment_repo, on_close=_close_view)
        self.stats_view.visible = self.show_stats

        # ── 日历视图 ──
        from ui.views.calendar_view import CalendarView

        self.calendar_view = CalendarView(task_service=self.task_service, on_close=_close_view)
        self.calendar_view.visible = self.show_calendar

        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.spacing = 0
        self._drawer_open = False
        self._chat_greeted = False

        # 键盘快捷键
        self._setup_keyboard_shortcuts()

        self._content_column = ft.Column(
            expand=True,
            spacing=12,
            animate_opacity=200,
            controls=[
                self.main_view,
                self.settings_view,
                self.stats_view,
                self.calendar_view,
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

    def did_mount(self):
        self._show_welcome_dialog()

    def _setup_keyboard_shortcuts(self):
        """设置键盘快捷键。"""
        self._keyboard_handler = self._on_keyboard_event

    def _on_keyboard_event(self, e: ft.KeyboardEvent):
        """处理键盘快捷键。"""
        # Ctrl+Z: 撤销
        if e.ctrl and e.key == "z" and not e.shift:
            self.undo_last(None)
            return
        # Ctrl+N: 聚焦到新任务输入框
        if e.ctrl and e.key == "n":
            self.new_task.focus()
            return
        # Esc: 关闭聊天抽屉或其他面板
        if e.key == "Escape":
            if self._drawer_open:
                import asyncio
                asyncio.ensure_future(self._toggle_chat_drawer(None))
            elif self.show_settings:
                self.open_settings(None)
            elif self.show_stats:
                self.open_stats(None)
            elif self.show_calendar:
                self.open_calendar(None)

    def _get_greeting(self) -> str:
        now = datetime.now()
        h = now.hour
        m = now.month
        d = now.day
        weekday = now.weekday()  # 0=Mon

        # 时间段问候
        if 5 <= h < 9:
            base = t("greet.morning")
        elif 9 <= h < 12:
            base = t("greet.late_morning")
        elif 11 <= h < 13:
            base = t("greet.noon_eat")
        elif 13 <= h < 14:
            base = t("greet.noon_rest")
        elif 14 <= h < 18:
            base = t("greet.afternoon")
        elif 18 <= h < 22:
            base = t("greet.evening")
        elif 22 <= h or h < 2:
            base = t("greet.night")
        else:
            base = t("greet.hello")

        # 节日彩蛋
        holidays = {
            (1, 1): t("holiday.new_year"),
            (2, 14): t("holiday.valentine"),
            (3, 8): t("holiday.womens_day"),
            (4, 1): t("holiday.april_fool"),
            (5, 1): t("holiday.labor_day"),
            (5, 4): t("holiday.youth_day"),
            (6, 1): t("holiday.children_day"),
            (8, 15): t("holiday.mid_autumn"),
            (9, 10): t("holiday.teacher_day"),
            (10, 1): t("holiday.national_day"),
            (12, 25): t("holiday.christmas"),
            (12, 31): t("holiday.new_year_eve"),
        }
        lunar_holidays = {
            (1, 1): t("holiday.spring_festival"),
            (1, 15): t("holiday.lantern"),
            (5, 5): t("holiday.dragon_boat"),
            (7, 7): t("holiday.qixi"),
            (7, 15): t("holiday.ghost"),
            (9, 9): t("holiday.chongyang"),
        }

        holiday = holidays.get((m, d))
        if holiday:
            return holiday

        # 周末
        if weekday >= 5:
            return t("holiday.weekend")

        return base

    def _show_welcome_dialog(self):
        tasks = self.task_service.list_tasks("all")
        now = datetime.now()
        today = now.date()

        # 紧要任务：今天到期或已过期且未完成
        urgent = [
            tk for tk in tasks
            if not tk.completed
            and (tk.end_date or tk.date).date() <= today
        ]
        # 过期任务
        expired = [
            tk for tk in tasks
            if not tk.completed
            and (tk.end_date or tk.date).date() < today
        ]

        greeting = self._get_greeting()

        if not urgent:
            # 无紧要任务 — 恭喜
            body = (
                f"✨ {t('welcome.no_urgent')} ✨\n\n"
                f"🎉🎉🎉  {t('welcome.all_done')}  🎉🎉🎉\n\n"
                f"\\(^o^)/  {t('welcome.nice')}\n\n"
                f"♪ ♪ ♪  {t('welcome.go')}  ♪ ♪ ♪"
            )
        else:
            lines = []
            show_count = min(3, len(urgent))
            for tk in urgent[:show_count]:
                deadline = (tk.end_date or tk.date).date()
                if deadline < today:
                    days_over = (today - deadline).days
                    lines.append(f"  ⚠️ {tk.name}{t('welcome.expired_days', days_over)}")
                else:
                    lines.append(f"  🔥 {tk.name}{t('welcome.due_today')}")

            remaining = len(urgent) - show_count
            if remaining > 0:
                lines.append(f"  …等 {remaining} 条")

            body = t("welcome.header") + "\n\n" + "\n".join(lines)
            if expired:
                body += f"\n\n{t('welcome.expired_footer', len(expired))} 📋"

        content_text = ft.Text(
            body,
            size=14,
            selectable=True,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"{greeting} 👋", size=20, weight=ft.FontWeight.W_600),
            content=content_text,
            actions=[
                ft.TextButton(t("welcome.got_it"), on_click=lambda e: self.page.pop_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    # ── 任务操作 ──────────────────────────────────────────

    def _on_new_freq_select(self, days: int):
        if days == -1:
            self._new_custom_row.visible = not self._new_custom_row.visible
        else:
            self._new_custom_row.visible = False
            self._new_custom_days.value = ""
        for chip in self._new_freq_chips.controls:
            chip.selected = (chip.data == days)
        self.update()

    def _get_new_repeat_days(self) -> int:
        for chip in self._new_freq_chips.controls:
            if chip.selected and chip.data > 0:
                return chip.data
            if chip.selected and chip.data == -1:
                try:
                    return int(self._new_custom_days.value or 0)
                except ValueError:
                    return 0
        return 0

    def _get_new_repeat_mode(self) -> str:
        return "each"

    async def add_clicked(self, e):
        if self.new_task.value:
            self._needs_resort = True
            self.push_undo_snapshot()
            picker = self._new_task_picker
            desc = (self._new_task_desc.value or "").strip()
            repeat_days = self._get_new_repeat_days()
            repeat_mode = self._get_new_repeat_mode()
            task_record = self.task_service.create_task(
                self.new_task.value,
                task_date=picker.range_start,
                end_date=picker.range_end,
                description=desc,
                repeat_days=repeat_days,
                repeat_mode=repeat_mode,
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
                task_record.repeat_days,
                task_record.repeat_mode,
                task_record.completed_dates,
            )
            task.key = str(task_record.id)
            task._is_new = True
            self.tasks.controls.append(task)
            self.new_task.value = ""
            self._new_task_desc.value = ""
            self._new_task_desc.visible = False
            for chip in self._new_freq_chips.controls:
                chip.selected = (chip.data == 0)
            self._new_custom_days.value = ""
            self._new_custom_row.visible = False
            self._new_repeat_row.visible = False
            self._new_task_date_label.visible = False
            self._new_task_picker_panel.visible = False
            picker.reset()
            # build() 看到 _is_new=True → card.opacity=0，首帧不可见
            # 一次 update 完成：排序 + 任务列表 + toast
            self._show_toast(t("toast.task_added", task_record.name))
            task._is_new = False
            # 入场动画：fire-and-forget，不阻塞
            async def _entrance():
                await asyncio.sleep(0.05)
                card = task.display_view.content
                card.opacity = 1
                card.scale = ft.Scale(1.0)
                task.update()
            asyncio.ensure_future(_entrance())
            await self.new_task.focus()

    async def _on_new_task_focus(self, e):
        if not self._new_task_picker_panel.visible:
            await self._toggle_new_task_picker(e)

    async def _close_picker(self, e):
        if self._new_task_picker_panel.visible:
            await self._toggle_new_task_picker(e)

    async def _toggle_new_task_picker(self, e):
        panel = self._new_task_picker_panel
        if panel.visible:
            # 关闭：先淡出再隐藏
            panel.opacity = 0
            self._new_task_desc.visible = False
            self._new_repeat_row.visible = False
            self.update()
            await asyncio.sleep(0.25)
            panel.visible = False
        else:
            # 打开：先显示再淡入
            panel.visible = True
            panel.opacity = 0
            self._new_task_desc.visible = True
            # 重复行不自动显示，等选了持续日期后才出现
            self.update()
            await asyncio.sleep(0.05)
            panel.opacity = 1
        self.update()

    def _on_new_task_date_picked(self, start: datetime, end: datetime | None):
        self._update_new_task_date_label()
        # 只在有持续（end_date）时显示重复设置
        has_range = end is not None and end != start
        self._new_repeat_row.visible = has_range
        if not has_range:
            # 无持续时重置重复设置
            for chip in self._new_freq_chips.controls:
                chip.selected = (chip.data == 0)
            self._new_custom_days.value = ""
            self._new_custom_row.visible = False
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
            label = t("date.today")
        elif d_date == today + timedelta(days=1):
            label = t("date.tomorrow")
        elif d_date == today + timedelta(days=2):
            label = t("date.day_after")
        else:
            label = d_date.strftime("%m-%d")

        if has_time:
            label += f" {d.hour:02d}:{d.minute:02d}"
        return label

    def task_delete(self, task):
        async def _confirm(e):
            self.page.pop_dialog()
            self.push_undo_snapshot()
            self._needs_resort = False  # 动画期间不触发排序
            await task.animate_exit()
            self.tasks.controls.remove(task)
            self.delete_task(task)
            self._needs_resort = True
            self._show_toast(t("toast.task_deleted", task.task_name))

        def _cancel(e):
            self.page.pop_dialog()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(t("dialog.delete_title")),
            content=ft.Text(t("dialog.delete_content", task.task_name)),
            actions=[
                ft.TextButton(t("dialog.cancel"), on_click=_cancel),
                ft.TextButton(t("dialog.delete"), on_click=_confirm, style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

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
        self._needs_resort = True
        self.push_undo_snapshot()
        count = 0
        for task in self.tasks.controls[:]:
            if task.completed:
                self.tasks.controls.remove(task)
                self.delete_task(task)
                count += 1
        if count > 0:
            self._show_toast(t("toast.tasks_cleared", count))
        else:
            self.update()

    # ── 生命周期 & 状态同步 ──────────────────────────────

    def before_update(self):
        if not hasattr(self, "items_left"):
            return
        if not self._needs_resort:
            return
        self._needs_resort = False
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
        self.items_left.value = t("status.items_left", count) + (
            t("status.expired_count", expired_count) if expired_count else ""
        )

    def _apply_sort(self):
        controls = self.tasks.controls
        if len(controls) <= 1:
            return
        mode = self._sort_mode
        today = date.today()

        def sort_key(task):
            if mode == "urgency_asc":
                deadline = (task.end_date or task.date).date()
                days_left = (deadline - today).days
                completed_offset = 10000 if task.completed else 0
                return (days_left + completed_offset, task.task_id or 0)
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
            # fallback = urgency
            deadline = (task.end_date or task.date).date()
            days_left = (deadline - today).days
            completed_offset = 10000 if task.completed else 0
            return (days_left + completed_offset, task.task_id or 0)

        controls.sort(key=sort_key)

    def _on_sort_change(self, e):
        self._sort_mode = e.control.value
        self._needs_resort = True
        self.update()

    # ── 聊天交互 ──────────────────────────────────────────

    async def handle_user_message(self, e):
        self._needs_resort = True
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
            await self._append_bubble(t("chat.cancelled"), is_user=False)
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
                border_radius=ft.BorderRadius(4, 16, 16, 16),
                bgcolor=AppColors.BUBBLE_ASSISTANT,
                content=ft.Row(
                    spacing=4,
                    controls=[
                        ft.ProgressRing(width=14, height=14, stroke_width=2),
                        ft.Text(t("chat.thinking"), size=13, color=AppColors.TEXT_HINT),
                    ],
                ),
            ),
        )

    async def confirm_pending_delete(self, e):
        if not self.pending_confirmation_token:
            await self._append_bubble(t("chat.no_pending"), is_user=False)
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

    async def _append_chat_greeting(self):
        """首次打开聊天 drawer 时显示问候气泡（区别于 welcome dialog）。"""
        tasks = self.task_service.list_tasks("all")
        now = datetime.now()
        today = now.date()
        greeting = self._get_greeting()

        active = [tk for tk in tasks if not tk.completed]
        overdue = [tk for tk in active if (tk.end_date or tk.date).date() < today]
        due_today = [tk for tk in active if (tk.end_date or tk.date).date() == today]

        # 聊天问候：简短 + 统计概要 + 行动建议，不重复 welcome dialog 的任务列表
        parts = [f"{greeting}！"]

        if not active:
            parts.append(t("welcome.all_done"))
            parts.append("想聊点什么随时找我~")
        else:
            summary_items = []
            if overdue:
                summary_items.append(f"{len(overdue)} 条已过期")
            if due_today:
                summary_items.append(f"{len(due_today)} 条今日到期")
            other = len(active) - len(overdue) - len(due_today)
            if other > 0:
                summary_items.append(f"{other} 条进行中")
            parts.append("当前有 " + "、".join(summary_items) + "。")

            if overdue:
                parts.append("过期任务需要优先处理，要我帮你梳理一下吗？")
            elif due_today:
                parts.append("今天的任务还来得及，加油！")
            else:
                parts.append("有什么需要帮忙的，随时告诉我。")

        body = "\n\n".join(parts)
        await self._append_bubble(body, is_user=False)
        self.update()

    async def _append_bubble(self, text: str, is_user: bool):
        bubble = ft.Container(
            alignment=ft.Alignment(1.0 if is_user else -1.0, 0),
            padding=ft.Padding(40 if is_user else 8, 0, 8 if is_user else 40, 0),
            animate_opacity=300,
            animate_scale=300,
            opacity=0,
            scale=ft.Scale(0.9),
            content=ft.Container(
                padding=ft.Padding(14, 10, 14, 10),
                border_radius=ft.BorderRadius(16, 16, 16, 4)
                if is_user
                else ft.BorderRadius(4, 16, 16, 16),
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
        self.update()
        await asyncio.sleep(0.05)
        bubble.opacity = 1
        bubble.scale = ft.Scale(1.0)
        self.update()

    # ── 筛选 & 撤销 ──────────────────────────────────────

    def current_filter_status(self) -> str:
        return self._current_filter

    def _set_filter(self, label: str):
        self._current_filter = label
        self._needs_resort = True
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
