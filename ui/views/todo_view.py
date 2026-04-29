import flet as ft

from core.constants.enums import TaskActionType
from core.models.task import TaskRecord
from services.llm_service import LLMService
from services.task_service import TaskService
from ui.components.task_item import Task
from ui.theme import AppColors


class TodoApp(ft.Column):
    def __init__(self):
        super().__init__()
        self.show_settings = False
        self.task_service = TaskService()
        self.llm_service = LLMService(self.task_service)
        self.pending_confirmation_token = None
        self.undo_stack: list[list[TaskRecord]] = []
        self._restoring = False
        self.tasks = ft.Column(expand=True, spacing=8)
        self._panel_min_width = 320
        self._splitter_width = 12
        self._left_panel_width = 520
        self.load_tasks()

    def load_tasks(self):
        self.tasks.controls.clear()
        for record in self.task_service.list_tasks():
            task = Task(
                record.name,
                self.task_delete,
                self,
                record.id,
                record.date,
                record.completed,
            )
            self.tasks.controls.append(task)

    def save_task(self, task):
        if task.task_id is not None:
            self.push_undo_snapshot()

        record = TaskRecord(
            id=task.task_id,
            name=task.task_name,
            date=task.date,
            completed=task.completed,
        )
        if record.id is None:
            saved = self.task_service.create_task(
                record.name, record.date, record.completed
            )
        else:
            saved = self.task_service.update_task(
                record.id,
                name=record.name,
                task_date=record.date,
                completed=record.completed,
            )
        task.task_id = saved.id

    def delete_task(self, task):
        if task.task_id:
            self.task_service.delete_task(task.task_id)

    def open_settings(self, e):
        self.show_settings = True
        self.main_view.visible = False
        self.settings_view.visible = True
        self.update()

    def close_settings(self, e):
        self.show_settings = False
        self.settings_view.visible = False
        self.main_view.visible = True
        self.update()

    def build(self):
        self.chat_history = ft.ListView(expand=True, spacing=8, auto_scroll=True)
        self.command_input = ft.TextField(
            hint_text="输入内容可聊天，也可执行任务指令",
            expand=True,
            on_submit=self.handle_user_message,
        )

        self.ai_result = ft.Text(value="", color=AppColors.TEXT_HINT, font_family="Microsoft YaHei")
        self.ai_confirm_button = ft.OutlinedButton(
            content="确认删除",
            height=42,
            visible=False,
            on_click=self.confirm_pending_delete,
        )

        self.new_task = ft.TextField(
            hint_text="What needs to be done?", on_submit=self.add_clicked, expand=True
        )

        self._filter_labels = ["all", "active", "completed"]
        self._current_filter = "all"
        self._filter_buttons = [
            ft.TextButton(
                content=label,
                on_click=lambda _, l=label: self._set_filter(l),
                style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=8, vertical=4)),
            )
            for label in self._filter_labels
        ]
        self.filter_row = ft.Row(controls=self._filter_buttons, spacing=0)

        self.items_left = ft.Text("0 items left", font_family="Microsoft YaHei")

        self.left_panel = ft.Container(
            padding=16,
            border_radius=12,
            bgcolor=AppColors.PANEL_BG,
            content=ft.ListView(
                expand=True,
                spacing=12,
                auto_scroll=False,
                controls=[
                    ft.Text("智能助手对话", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, font_family="Microsoft YaHei"),
                    ft.Container(
                        height=220,
                        border_radius=10,
                        padding=10,
                        bgcolor=AppColors.CHAT_INPUT_BG,
                        content=self.chat_history,
                    ),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                content=self.command_input, col={"xs": 12, "md": 8}
                            ),
                            ft.Container(
                                content=ft.FilledButton(
                                    content="发送",
                                    height=42,
                                    on_click=self.handle_user_message,
                                ),
                                col={"xs": 6, "md": 2},
                            ),
                            ft.Container(
                                content=self.ai_confirm_button,
                                col={"xs": 6, "md": 2},
                            ),
                        ],
                        columns=12,
                        run_spacing=8,
                    ),
                    self.ai_result,
                ],
            ),
        )

        self.right_panel = ft.Container(
            padding=16,
            border_radius=12,
            bgcolor=AppColors.PANEL_BG,
            content=ft.ListView(
                expand=True,
                spacing=12,
                auto_scroll=False,
                controls=[
                    ft.Text("待办列表", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, font_family="Microsoft YaHei"),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                content=self.new_task, col={"xs": 10, "md": 11}
                            ),
                            ft.Container(
                                content=ft.FloatingActionButton(
                                    icon=ft.Icons.ADD, on_click=self.add_clicked
                                ),
                                alignment=ft.Alignment(1, 0),
                                col={"xs": 2, "md": 1},
                            ),
                        ],
                        columns=12,
                        run_spacing=8,
                    ),
                    self.filter_row,
                    self.tasks,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.items_left,
                            ft.OutlinedButton(
                                content="Clear completed",
                                on_click=self.clear_clicked,
                            ),
                            ft.OutlinedButton(
                                content="Undo",
                                on_click=self.undo_last,
                            ),
                        ],
                    ),
                ],
            ),
        )

        splitter = ft.GestureDetector(
            content=ft.Container(
                width=self._splitter_width,
                border_radius=999,
                bgcolor=AppColors.SPLITTER_TRACK,
                alignment=ft.Alignment(0, 0),
                content=ft.Container(
                    width=3,
                    expand=True,
                    border_radius=999,
                    bgcolor=AppColors.SPLITTER_HANDLE,
                ),
            ),
            on_pan_update=self.resize_panels,            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
        )

        self.main_view = ft.Column(
            expand=True,
            spacing=16,
            visible=not self.show_settings,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS_OUTLINED,
                            tooltip="Settings",
                            on_click=self.open_settings,
                        ),
                        ft.Text(
                            value="TO DO",
                            theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                            font_family="Microsoft YaHei",
                        ),
                        ft.Container(width=40),
                    ],
                ),
                ft.Row(
                    expand=True,
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        self.left_panel,
                        splitter,
                        self.right_panel,
                    ],
                ),
            ],
        )

        self._sync_panel_widths()

        self.settings_view = ft.Column(
            expand=True,
            spacing=16,
            visible=self.show_settings,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            tooltip="Back",
                            on_click=self.close_settings,
                        ),
                        ft.Text(
                            value="Settings",
                            theme_style=ft.TextThemeStyle.HEADLINE_SMALL,
                            font_family="Microsoft YaHei",
                        ),
                    ],
                ),
                ft.ResponsiveRow(
                    columns=12,
                    run_spacing=12,
                    controls=[
                        ft.Container(
                            col={"xs": 12, "md": 4},
                            height=460,
                            border_radius=12,
                            padding=16,
                            bgcolor=ft.Colors.SURFACE,
                            content=ft.Text("设置列表（预留）", color=AppColors.TEXT_HINT, font_family="Microsoft YaHei"),
                        ),
                        ft.Container(
                            col={"xs": 12, "md": 8},
                            height=460,
                            border_radius=12,
                            padding=16,
                            bgcolor=ft.Colors.SURFACE,
                            content=ft.Text(
                                "具体设置界面（预留）", color=AppColors.TEXT_HINT, font_family="Microsoft YaHei"
                            ),
                        ),
                    ],
                ),
            ],
        )

        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.spacing = 0
        self.controls = [self.main_view, self.settings_view]

    async def add_clicked(self, e):
        if self.new_task.value:
            self.push_undo_snapshot()
            task_record = self.task_service.create_task(self.new_task.value)
            task = Task(
                task_record.name,
                self.task_delete,
                self,
                task_record.id,
                task_record.date,
                task_record.completed,
            )
            self.tasks.controls.append(task)
            self.new_task.value = ""
            await self.new_task.focus()
            self.update()

    def task_delete(self, task):
        self.push_undo_snapshot()
        self.tasks.controls.remove(task)
        self.delete_task(task)
        self.update()

    def clear_clicked(self, e):
        self.push_undo_snapshot()
        for task in self.tasks.controls[:]:
            if task.completed:
                self.tasks.controls.remove(task)
                self.delete_task(task)
        self.update()

    def before_update(self):
        self._sync_panel_widths()
        self._sync_filter_highlight()
        status = self._current_filter
        count = 0
        for task in self.tasks.controls:
            task.visible = (
                status == "all"
                or (status == "active" and not task.completed)
                or (status == "completed" and task.completed)
            )
            if not task.completed:
                count += 1
        self.items_left.value = f"{count} active item(s) left"

    def resize_panels(self, e: ft.DragUpdateEvent):
        delta_x = e.local_delta.x if e.local_delta else 0
        if delta_x:
            self._left_panel_width += delta_x
            self._sync_panel_widths()
            self.left_panel.update()
            self.right_panel.update()

    def _sync_panel_widths(self):
        page_width = getattr(self.page, "width", None) or 1200
        available_width = max(
            2 * self._panel_min_width + self._splitter_width,
            int(page_width) - 24,
        )
        max_left = available_width - self._panel_min_width - self._splitter_width
        self._left_panel_width = max(
            self._panel_min_width, min(self._left_panel_width, max_left)
        )
        right_width = available_width - self._left_panel_width - self._splitter_width
        self.left_panel.width = self._left_panel_width
        self.right_panel.width = right_width

    def handle_user_message(self, e):
        text = (self.command_input.value or "").strip()
        if not text:
            self.ai_result.value = "请输入一句自然语言指令。"
            self.ai_confirm_button.visible = False
            self.update()
            return

        self._append_chat_line(f"你: {text}", AppColors.CHAT_USER)

        confirm_words = {"确认", "是", "yes", "y", "ok", "好的", "行", "确认删除"}
        cancel_words = {"取消", "不用", "算了", "no", "n"}
        if self.pending_confirmation_token and text.lower() in {
            word.lower() for word in confirm_words
        }:
            self.confirm_pending_delete(e)
            self.command_input.value = ""
            self.update()
            return
        if self.pending_confirmation_token and text.lower() in {
            word.lower() for word in cancel_words
        }:
            self.pending_confirmation_token = None
            self.ai_confirm_button.visible = False
            self.ai_result.value = "已取消删除操作。"
            self._append_chat_line("助手: 已取消删除操作。", AppColors.CHAT_ASSISTANT)
            self.command_input.value = ""
            self.update()
            return

        planned = self.llm_service.plan(text)
        mutating_actions = {
            TaskActionType.CREATE,
            TaskActionType.UPDATE,
            TaskActionType.COMPLETE,
            TaskActionType.UNCOMPLETE,
        }
        if planned.action in mutating_actions:
            self.push_undo_snapshot()

        result = self.llm_service.process(
            text, current_status=self.current_filter_status()
        )
        self.ai_result.value = result.message
        self._append_chat_line(f"助手: {result.message}", AppColors.CHAT_ASSISTANT)
        self.ai_confirm_button.visible = result.pending_confirmation
        self.pending_confirmation_token = result.confirmation_token
        self.command_input.value = ""
        self.load_tasks()
        self.update()

    def confirm_pending_delete(self, e):
        if not self.pending_confirmation_token:
            self.ai_result.value = "没有待确认的删除操作。"
            self.ai_confirm_button.visible = False
            self.update()
            return

        self.push_undo_snapshot()
        result = self.llm_service.confirm_delete(self.pending_confirmation_token)
        self.pending_confirmation_token = None
        self.ai_confirm_button.visible = False
        self.ai_result.value = result.message
        self._append_chat_line(f"助手: {result.message}", AppColors.CHAT_ASSISTANT)
        self.load_tasks()
        self.update()

    def _append_chat_line(self, text: str, color):
        self.chat_history.controls.append(ft.Text(text, color=color, font_family="Microsoft YaHei"))
        try:
            self.chat_history.scroll_to(offset=-1, duration=120)
        except Exception:
            pass

    def current_filter_status(self) -> str:
        return self._current_filter

    def _set_filter(self, label: str):
        self._current_filter = label
        self.update()

    def _sync_filter_highlight(self):
        for btn in self._filter_buttons:
            btn.style = ft.ButtonStyle(
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                color=ft.Colors.PRIMARY if btn.content == self._current_filter else ft.Colors.ON_SURFACE_VARIANT,
                overlay_color=ft.Colors.with_opacity(0.08, ft.Colors.PRIMARY),
            )

    def push_undo_snapshot(self):
        if self._restoring:
            return
        current = self.task_service.list_tasks(status="all")
        snapshot = [
            TaskRecord(
                name=task.name,
                date=task.date,
                completed=task.completed,
            )
            for task in current
        ]
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def undo_last(self, e):
        if not self.undo_stack:
            self.ai_result.value = "没有可撤销的操作。"
            self.update()
            return

        snapshot = self.undo_stack.pop()
        self._restoring = True
        try:
            self.task_service.replace_all_tasks(snapshot)
        finally:
            self._restoring = False
        self.ai_result.value = "已撤销上一步操作。"
        self.load_tasks()
        self.update()
