from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

import flet as ft

from ui.i18n import t
from ui.theme import AppColors

if TYPE_CHECKING:
    from services.task_service import TaskService

# ── task status colors (莫兰迪色系) ─────────────────────────
DOT_COMPLETED = "#9FA8B8"   # 灰蓝
DOT_PENDING = "#C2B8A3"     # 燕麦
DOT_EXPIRED = "#C8907A"     # 赭石
DOT_ONGOING = "#8BAA8E"     # 灰绿
DOT_FUTURE = "#B5A8C8"      # 淡紫
DOT_TODAY = "#D4A876"       # 赤金


def _weekday_labels() -> list[str]:
    raw = t("picker.weekdays")
    return [ch for ch in raw]


class CalendarView(ft.Column):
    """Full-page calendar view: month grid + task detail panel."""

    def __init__(self, task_service: TaskService):
        super().__init__()
        self._task_service = task_service
        self.expand = True
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

        today = date.today()
        self._view_year = today.year
        self._view_month = today.month
        self._selected_date: date | None = today
        self._all_tasks: list = []

        self._build_ui()
        self._load_tasks()

    # ── public API ─────────────────────────────────────────

    def refresh(self):
        self._load_tasks()
        self._rebuild_grid()
        self._rebuild_detail()
        if self.page:
            self.update()

    # ── data ───────────────────────────────────────────────

    def _load_tasks(self):
        self._all_tasks = self._task_service.list_tasks("all")

    def _tasks_for_date(self, d: date) -> list:
        result = []
        for tk in self._all_tasks:
            start = tk.date.date()
            end = (tk.end_date or tk.date).date()
            # each 模式：只在重复日期显示
            if tk.repeat_days > 0 and tk.repeat_mode == "each" and tk.end_date:
                occ = start
                while occ <= end:
                    if occ == d:
                        result.append(tk)
                        break
                    occ = date.fromordinal(occ.toordinal() + tk.repeat_days)
            elif start <= d <= end:
                result.append(tk)
        return result

    def _task_dots_for_date(self, d: date) -> list[str]:
        """Return list of dot colors for tasks on this date."""
        today = date.today()
        colors = []
        for tk in self._all_tasks:
            start = tk.date.date()
            end = (tk.end_date or tk.date).date()

            # each 模式：检查是否在重复日期上
            in_range = False
            if tk.repeat_days > 0 and tk.repeat_mode == "each" and tk.end_date:
                occ = start
                while occ <= end:
                    if occ == d:
                        in_range = True
                        break
                    occ = date.fromordinal(occ.toordinal() + tk.repeat_days)
            elif start <= d <= end:
                in_range = True

            if not in_range:
                continue

            # each 模式：检查该日期是否已完成
            if tk.repeat_mode == "each" and tk.repeat_days > 0:
                if d.isoformat() in tk.completed_dates:
                    colors.append(DOT_COMPLETED)
                elif d < today:
                    colors.append(DOT_EXPIRED)
                elif d == today:
                    colors.append(DOT_TODAY)
                else:
                    colors.append(DOT_PENDING)
            else:
                if tk.completed:
                    colors.append(DOT_COMPLETED)
                elif end < today:
                    colors.append(DOT_EXPIRED)
                elif d == today:
                    colors.append(DOT_TODAY)
                elif tk.end_date and start <= today <= end:
                    colors.append(DOT_ONGOING)
                elif d > today:
                    colors.append(DOT_FUTURE)
                else:
                    colors.append(DOT_PENDING)
        return colors[:4]  # max 4 dots

    # ── build ──────────────────────────────────────────────

    def _build_ui(self):
        # header
        self._month_label = ft.Text(size=18, weight=ft.FontWeight.W_700)

        header = ft.Container(
            padding=ft.Padding(20, 16, 20, 8),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    ft.TextButton(
                        content=ft.Text(t("calendar.today")),
                        on_click=self._go_today,
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.FAST_REWIND_ROUNDED,
                        icon_size=20,
                        on_click=self._prev_year,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.KEYBOARD_ARROW_LEFT,
                        icon_size=24,
                        on_click=self._prev_month,
                    ),
                    self._month_label,
                    ft.IconButton(
                        icon=ft.Icons.KEYBOARD_ARROW_RIGHT,
                        icon_size=24,
                        on_click=self._next_month,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.FAST_FORWARD_ROUNDED,
                        icon_size=20,
                        on_click=self._next_year,
                    ),
                ],
            ),
        )

        # weekday header
        weekdays = _weekday_labels()
        weekday_row = ft.Container(
            padding=ft.Padding(20, 0, 20, 4),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                controls=[
                    ft.Container(
                        width=48,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(
                            ch, size=13, weight=ft.FontWeight.W_600,
                            color=AppColors.TEXT_HINT,
                        ),
                    )
                    for ch in weekdays
                ],
            ),
        )

        # grid placeholder
        self._grid_column = ft.Column(spacing=2)

        grid_container = ft.Container(
            padding=ft.Padding(12, 0, 12, 8),
            content=self._grid_column,
        )

        # divider
        divider = ft.Divider(height=1)

        # detail panel
        self._detail_header = ft.Text(size=15, weight=ft.FontWeight.W_700)
        self._detail_list = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)
        self._detail_panel = ft.Container(
            expand=True,
            padding=ft.Padding(24, 12, 24, 16),
            content=ft.Column(
                spacing=8,
                controls=[
                    self._detail_header,
                    self._detail_list,
                ],
            ),
        )

        # calendar grid card
        grid_card = ft.Container(
            margin=ft.Margin(16, 8, 16, 0),
            padding=ft.Padding(0, 30, 0, 30),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Column(
                spacing=0,
                controls=[
                    header,
                    weekday_row,
                    grid_container,
                ],
            ),
        )

        # detail card
        detail_card = ft.Container(
            expand=True,
            margin=ft.Margin(16, 12, 16, 8),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=self._detail_panel,
        )

        self.controls = [grid_card, detail_card]

        self._rebuild_grid()
        self._rebuild_detail()

    # ── grid ───────────────────────────────────────────────

    def _rebuild_grid(self):
        self._grid_column.controls.clear()
        month_names = _month_names()
        self._month_label.value = t(
            "picker.month_label", self._view_year,
            month_names[self._view_month - 1],
        )
        cal = calendar.monthcalendar(self._view_year, self._view_month)
        today = date.today()

        for week in cal:
            cells = []
            for day in week:
                if day == 0:
                    cells.append(ft.Container(width=48, height=62))
                else:
                    d = date(self._view_year, self._view_month, day)
                    is_today = d == today
                    is_selected = d == self._selected_date

                    # bg color
                    if is_selected:
                        bg = ft.Colors.PRIMARY
                    elif is_today:
                        bg = ft.Colors.with_opacity(0.1, ft.Colors.PRIMARY)
                    else:
                        bg = None

                    # text color
                    if is_selected:
                        fg = ft.Colors.ON_PRIMARY
                    elif is_today:
                        fg = ft.Colors.PRIMARY
                    else:
                        fg = None

                    weight = ft.FontWeight.W_700 if (is_selected or is_today) else ft.FontWeight.W_500

                    # task dots
                    dot_colors = self._task_dots_for_date(d)
                    dots = ft.Row(
                        spacing=2,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=6, height=6,
                                border_radius=3,
                                bgcolor=c,
                            )
                            for c in dot_colors
                        ],
                    ) if dot_colors else ft.Container()

                    cells.append(
                        ft.Container(
                            width=48, height=62,
                            border_radius=10,
                            bgcolor=bg,
                            alignment=ft.Alignment.CENTER,
                            on_click=lambda e, dd=d: self._on_day_click(dd),
                            content=ft.Column(
                                spacing=1,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        str(day), size=15, weight=weight, color=fg,
                                    ),
                                    dots,
                                ],
                            ),
                        )
                    )
            self._grid_column.controls.append(
                ft.Row(
                    spacing=0,
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    controls=cells,
                )
            )

    # ── detail panel ───────────────────────────────────────

    def _rebuild_detail(self):
        d = self._selected_date
        if not d:
            self._detail_header.value = ""
            self._detail_list.controls = []
            return

        # header label
        month_names = _month_names()
        weekdays = _weekday_labels()
        self._detail_header.value = f"{d.year} {month_names[d.month - 1]} {d.day} {weekdays[d.weekday()]}"

        tasks = self._tasks_for_date(d)
        if not tasks:
            self._detail_list.controls = [
                ft.Container(
                    padding=ft.Padding(0, 20, 0, 20),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text(
                        t("calendar.no_tasks"),
                        size=13,
                        color=AppColors.TEXT_HINT,
                    ),
                ),
            ]
            return

        items = []
        today = date.today()
        for tk in tasks:
            start = tk.date.date()
            end = (tk.end_date or tk.date).date()
            # each 模式：按单日完成状态着色
            if tk.repeat_mode == "each" and tk.repeat_days > 0:
                if d.isoformat() in tk.completed_dates:
                    dot_color = DOT_COMPLETED
                elif d < today:
                    dot_color = DOT_EXPIRED
                elif d == today:
                    dot_color = DOT_TODAY
                else:
                    dot_color = DOT_PENDING
            else:
                if tk.completed:
                    dot_color = DOT_COMPLETED
                elif end < today:
                    dot_color = DOT_EXPIRED
                elif d == today:
                    dot_color = DOT_TODAY
                elif tk.end_date and start <= today <= end:
                    dot_color = DOT_ONGOING
                elif d > today:
                    dot_color = DOT_FUTURE
                else:
                    dot_color = DOT_PENDING

            # time label
            time_str = ""
            if tk.date.hour or tk.date.minute:
                time_str = tk.date.strftime("%H:%M")

            end_str = ""
            if tk.end_date and (tk.end_date.hour or tk.end_date.minute):
                end_str = tk.end_date.strftime("%H:%M")

            time_label = ""
            if time_str and end_str:
                time_label = f"{time_str}-{end_str}"
            elif time_str:
                time_label = time_str

            name_style = ft.TextStyle(
                decoration=ft.TextDecoration.LINE_THROUGH if tk.completed else None,
            )

            # 重复信息
            repeat_label = ""
            if tk.repeat_days > 0:
                repeat_label = t("repeat.every_day") if tk.repeat_days == 1 else t("repeat.every_n_days", tk.repeat_days)
                if tk.repeat_mode == "each" and tk.is_recurring:
                    done = len(tk.completed_dates)
                    repeat_label += f" · {t('repeat.progress', done, len(tk.repeat_occurrences))}"
                else:
                    repeat_label += f" · {t('repeat.once_mode')}"

            name_col = ft.Column(
                spacing=1,
                tight=True,
                expand=True,
                controls=[
                    ft.Text(
                        tk.name,
                        size=14,
                        expand=True,
                        style=name_style,
                        opacity=0.5 if tk.completed else 1.0,
                    ),
                    *(
                        [ft.Text(repeat_label, size=11, color=AppColors.TEXT_HINT)]
                        if repeat_label
                        else []
                    ),
                ],
            )

            right_controls = []
            if time_label:
                right_controls.append(ft.Text(time_label, size=11, color=AppColors.TEXT_HINT))

            items.append(
                ft.Container(
                    padding=ft.Padding(10, 6, 10, 6),
                    border_radius=8,
                    bgcolor=AppColors.PANEL_BG,
                    content=ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=8, height=8,
                                border_radius=4,
                                bgcolor=dot_color,
                            ),
                            name_col,
                            *right_controls,
                        ],
                    ),
                )
            )

        self._detail_list.controls = items

    # ── navigation ─────────────────────────────────────────

    def _on_day_click(self, d: date):
        self._selected_date = d
        self._rebuild_grid()
        self._rebuild_detail()
        if self.page:
            self.update()

    def _prev_year(self, e):
        self._view_year -= 1
        self._selected_date = None
        self._rebuild_grid()
        self._rebuild_detail()
        if self.page:
            self.update()

    def _next_year(self, e):
        self._view_year += 1
        self._selected_date = None
        self._rebuild_grid()
        self._rebuild_detail()
        if self.page:
            self.update()

    def _prev_month(self, e):
        if self._view_month == 1:
            self._view_month = 12
            self._view_year -= 1
        else:
            self._view_month -= 1
        self._selected_date = None
        self._rebuild_grid()
        self._rebuild_detail()
        if self.page:
            self.update()

    def _next_month(self, e):
        if self._view_month == 12:
            self._view_month = 1
            self._view_year += 1
        else:
            self._view_month += 1
        self._selected_date = None
        self._rebuild_grid()
        self._rebuild_detail()
        if self.page:
            self.update()

    def _go_today(self, e):
        today = date.today()
        self._view_year = today.year
        self._view_month = today.month
        self._selected_date = today
        self._rebuild_grid()
        self._rebuild_detail()
        if self.page:
            self.update()


def _month_names() -> list[str]:
    return t("picker.months").split(",")
