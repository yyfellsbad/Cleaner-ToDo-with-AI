from __future__ import annotations

from datetime import date, datetime, timedelta

import flet as ft

from ui.components.date_picker import CustomDatePicker
from ui.theme import AppColors


def _has_time_component(dt: datetime) -> bool:
    return dt.hour != 0 or dt.minute != 0


class Task(ft.Column):
    def __init__(
        self,
        task_name,
        task_delete,
        app,
        task_id=None,
        date=None,
        end_date=None,
        description="",
        completed=False,
    ):
        super().__init__()
        self.app = app
        self.task_id = task_id
        self.task_name = task_name
        self.date = date or datetime.now().replace(second=0, microsecond=0)
        self.end_date = end_date
        self.description = description
        self.completed = completed
        self.task_delete = task_delete

    @property
    def expired(self) -> bool:
        if self.completed:
            return False
        deadline = self.end_date or self.date
        return deadline.date() < datetime.now().date()

    def _fmt_short(self, d: datetime) -> str:
        today = datetime.now().date()
        d_date = d.date() if isinstance(d, datetime) else d
        has_time = _has_time_component(d)

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

    @property
    def ongoing(self) -> bool:
        """当前时间在开始和结束之间（正在持续）。"""
        if not self.end_date or self.completed:
            return False
        now = datetime.now()
        return self.date <= now <= self.end_date

    def _get_date_display(self):
        today = datetime.now().date()
        start_label = self._fmt_short(self.date)

        if self.end_date:
            end_label = self._fmt_short(self.end_date)
            if self.date.date() == self.end_date.date() and _has_time_component(self.date) and _has_time_component(self.end_date):
                end_label = f"{self.end_date.hour:02d}:{self.end_date.minute:02d}"
            text = f"📅 {start_label} ~ {end_label}"
            color = AppColors.DATE_ONGOING if self.ongoing else AppColors.DATE_FUTURE
            return text, color, 12

        if self.date.date() > today:
            return f"📅 {start_label}", AppColors.DATE_FUTURE, 13
        elif self.date.date() == today:
            return f"📅 {start_label}", AppColors.DATE_TODAY, 13
        else:
            return f"📅 {start_label}", AppColors.DATE_PAST, 12

    def build(self):
        self.display_task = ft.Checkbox(
            value=False, label=self.task_name, on_change=self.status_changed
        )
        self.edit_name = ft.TextField(expand=1)
        date_text, date_color, date_size = self._get_date_display()

        self._action_row = ft.Row(
            spacing=0,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.CREATE_OUTLINED,
                    tooltip="编辑",
                    icon_size=18,
                    on_click=self.edit_clicked,
                ),
                ft.IconButton(
                    ft.Icons.DELETE_OUTLINE,
                    tooltip="删除",
                    icon_size=18,
                    on_click=self.delete_clicked,
                ),
            ],
        )

        # ── 日期编辑器（复用 CustomDatePicker，自动范围） ──
        self._custom_picker = CustomDatePicker(
            selected=self.date,
            show_time=True,
        )

        self._date_editor_row = ft.Column(
            visible=False,
            spacing=6,
            tight=True,
            controls=[
                self._custom_picker,
                ft.Row(
                    spacing=4,
                    alignment=ft.MainAxisAlignment.END,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                            icon_color=AppColors.EDIT_CONFIRM_ICON,
                            tooltip="确认",
                            icon_size=18,
                            on_click=self._save_date_edit,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            tooltip="取消",
                            icon_size=18,
                            on_click=self._cancel_date_edit,
                        ),
                    ],
                ),
            ],
        )

        # ── 可点击的日期显示 ──
        self._date_display_text = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=self._date_text_clicked,
            content=ft.Container(
                border_radius=4,
                padding=ft.Padding(4, 2, 4, 2),
                content=ft.Text(
                    date_text,
                    size=date_size,
                    color=date_color,
                ),
            ),
        )

        date_area = ft.Column(
            spacing=0,
            tight=True,
            controls=[
                self._date_display_text,
                self._date_editor_row,
            ],
        )

        # ── 描述显示 ──
        self._desc_expanded = False
        self._desc_text = ft.Text(
            self.description,
            size=12,
            color=AppColors.TEXT_HINT,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            no_wrap=False,
            visible=bool(self.description),
        )
        self._desc_display = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK if self.description else ft.MouseCursor.BASIC,
            on_tap=self._toggle_desc,
            content=ft.Container(
                padding=ft.Padding(0, 2, 0, 0),
                content=self._desc_text,
            ),
        )

        # 卡片样式：过期变浅+标记，已完成加深+标记
        if self.completed:
            card_bg = ft.Colors.with_opacity(0.92, AppColors.PANEL_BG)
            card_opacity = 1.0
            status_tag = ft.Container(
                padding=ft.Padding(6, 2, 6, 2),
                border_radius=4,
                bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.PRIMARY),
                content=ft.Text("完成", size=10, color=ft.Colors.PRIMARY, weight=ft.FontWeight.W_500),
            )
        elif self.expired:
            card_bg = AppColors.PANEL_BG
            card_opacity = 0.5
            status_tag = ft.Container(
                padding=ft.Padding(6, 2, 6, 2),
                border_radius=4,
                bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.ERROR),
                content=ft.Text("过期", size=10, color=ft.Colors.ERROR, weight=ft.FontWeight.W_500),
            )
        else:
            card_bg = AppColors.PANEL_BG
            card_opacity = 1.0
            status_tag = None

        self._status_tag = status_tag

        self.display_view = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            content=ft.Container(
                border_radius=10,
                padding=ft.Padding(28, 8, 40, 8),
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                bgcolor=card_bg,
                opacity=card_opacity,
                content=ft.Row(
                    expand=True,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            expand=True,
                            padding=ft.Padding.only(right=8),
                            content=ft.Column(
                                spacing=2,
                                tight=True,
                                controls=[
                                    ft.Row(
                                        spacing=8,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text(
                                                self.task_name,
                                                size=15,
                                                weight=ft.FontWeight.W_500,
                                                no_wrap=False,
                                                overflow=ft.TextOverflow.VISIBLE,
                                            ),
                                            *([status_tag] if status_tag else []),
                                        ],
                                    ),
                                    date_area,
                                    self._desc_display,
                                ],
                            ),
                        ),
                        ft.Checkbox(
                            value=self.completed,
                            on_change=self.status_changed,
                        ),
                        self._action_row,
                    ],
                ),
            ),
        )

        self.edit_desc = ft.TextField(
            hint_text="添加描述（可选）",
            expand=True,
            text_size=13,
            content_padding=ft.Padding(8, 4, 8, 4),
            border_radius=6,
            multiline=True,
            min_lines=1,
            max_lines=3,
        )

        self.edit_view = ft.Column(
            visible=False,
            spacing=4,
            controls=[
                self.edit_name,
                self.edit_desc,
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                            icon_color=AppColors.EDIT_CONFIRM_ICON,
                            tooltip="确认",
                            on_click=self.save_clicked,
                        ),
                    ],
                ),
            ],
        )
        self.controls = [self.display_view, self.edit_view]

    # ── 名称编辑 ──

    def edit_clicked(self, e):
        if self._date_editor_row.visible:
            self._cancel_date_edit(e)
        self.edit_name.value = self.display_task.label
        self.edit_desc.value = self.description
        self.display_view.visible = False
        self.edit_view.visible = True
        self.update()

    def save_clicked(self, e):
        self.task_name = self.edit_name.value
        self.description = self.edit_desc.value or ""
        self._desc_text.value = self.description
        self._desc_text.visible = bool(self.description)
        self._desc_display.mouse_cursor = (
            ft.MouseCursor.CLICK if self.description else ft.MouseCursor.BASIC
        )
        self._desc_expanded = False
        self._desc_text.max_lines = 1
        self.display_view.visible = True
        self.edit_view.visible = False
        self.app.save_task(self)

    # ── 状态变更 ──

    def status_changed(self, e):
        self.completed = e.control.value
        self._refresh_card_style()
        self.app.save_task(self)

    def delete_clicked(self, e):
        self.task_delete(self)

    # ── 描述展开/收起 ──

    def _toggle_desc(self, e):
        if not self.description:
            return
        self._desc_expanded = not self._desc_expanded
        self._desc_text.max_lines = None if self._desc_expanded else 1
        self._desc_text.update()

    # ── 日期编辑 ──

    def _date_text_clicked(self, e):
        if self.edit_view.visible:
            return
        # 前置填入当前日期/时间/范围
        self._custom_picker.set_range(self.date, self.end_date)
        self._date_display_text.visible = False
        self._date_editor_row.visible = True
        self.update()

    def _save_date_edit(self, e):
        parsed_start = self._custom_picker.range_start
        if not parsed_start:
            return

        parsed_end = self._custom_picker.range_end

        self.date = parsed_start
        self.end_date = parsed_end
        self._refresh_date_display()
        self._date_display_text.visible = True
        self._date_editor_row.visible = False
        self.app.save_task(self)
        self.update()

    def _cancel_date_edit(self, e):
        self._date_display_text.visible = True
        self._date_editor_row.visible = False
        self.update()

    def _refresh_date_display(self):
        text, color, size = self._get_date_display()
        self._date_display_text.content.content.value = text
        self._date_display_text.content.content.color = color
        self._date_display_text.content.content.size = size

    def _refresh_card_style(self):
        card = self.display_view.content
        if self.completed:
            card.bgcolor = ft.Colors.with_opacity(0.92, AppColors.PANEL_BG)
            card.opacity = 1.0
        elif self.expired:
            card.bgcolor = AppColors.PANEL_BG
            card.opacity = 0.5
        else:
            card.bgcolor = AppColors.PANEL_BG
            card.opacity = 1.0
        # 标记由 build() 静态生成，状态变更后通过 load_tasks 重建
