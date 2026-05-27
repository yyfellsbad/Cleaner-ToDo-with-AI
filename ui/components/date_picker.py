from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timedelta

import flet as ft

from ui.theme import AppColors

_WEEKDAY_LABELS = ["一", "二", "三", "四", "五", "六", "日"]
_MONTH_NAMES = [
    "", "1月", "2月", "3月", "4月", "5月", "6月",
    "7月", "8月", "9月", "10月", "11月", "12月",
]


def _has_time(dt: datetime) -> bool:
    return dt.hour != 0 or dt.minute != 0


class CustomDatePicker(ft.Column):
    """日历 + 时间选择器。自动检测范围（点第二个日期变持续）。"""

    def __init__(
        self,
        selected: date | datetime | None = None,
        on_change=None,
        show_time: bool = False,
    ):
        super().__init__()
        self.spacing = 4
        self.tight = True
        self.on_change = on_change
        self.show_time = show_time

        # 日期状态
        self._range_start: date | None = None
        self._range_end: date | None = None

        # 时间状态
        self._start_hour = 0
        self._start_minute = 0
        self._end_hour = 0
        self._end_minute = 0

        # 初始化
        if isinstance(selected, datetime):
            self._range_start = selected.date()
            self._start_hour = selected.hour
            self._start_minute = selected.minute
        elif isinstance(selected, date):
            self._range_start = selected

        if self._range_start:
            self._view_year = self._range_start.year
            self._view_month = self._range_start.month
        else:
            today = date.today()
            self._view_year = today.year
            self._view_month = today.month

        self._build()

    # ── 公开属性 ──

    @property
    def range_start(self) -> datetime | None:
        if not self._range_start:
            return None
        return datetime(self._range_start.year, self._range_start.month, self._range_start.day,
                        self._start_hour, self._start_minute)

    @property
    def range_end(self) -> datetime | None:
        if not self._range_end:
            return None
        return datetime(self._range_end.year, self._range_end.month, self._range_end.day,
                        self._end_hour, self._end_minute)

    @property
    def value(self) -> datetime:
        return self.range_start or datetime.now().replace(second=0, microsecond=0)

    @property
    def is_range(self) -> bool:
        return self._range_end is not None

    def set_range(self, start: datetime | date | None, end: datetime | date | None = None):
        """设置日期范围，前置填入。"""
        if isinstance(start, datetime):
            self._range_start = start.date()
            self._start_hour = start.hour
            self._start_minute = start.minute
        elif isinstance(start, date):
            self._range_start = start
            self._start_hour = 0
            self._start_minute = 0
        else:
            self._range_start = None

        if isinstance(end, datetime):
            self._range_end = end.date()
            self._end_hour = end.hour
            self._end_minute = end.minute
        elif isinstance(end, date):
            self._range_end = end
            self._end_hour = 0
            self._end_minute = 0
        else:
            self._range_end = None
            self._end_hour = 0
            self._end_minute = 0

        if self._range_start:
            self._view_year = self._range_start.year
            self._view_month = self._range_start.month

        self._sync_text()
        self._sync_time_controls()
        self._rebuild_time_row()
        self._rebuild_grid()

    def reset(self):
        """重置所有状态。"""
        today = date.today()
        self._range_start = today
        self._range_end = None
        self._start_hour = 0
        self._start_minute = 0
        self._end_hour = 0
        self._end_minute = 0
        self._view_year = today.year
        self._view_month = today.month
        self._sync_text()
        self._sync_time_controls()
        self._rebuild_time_row()
        self._rebuild_grid()

    # ── 构建 ──

    def _build(self):
        # 文本输入
        self._text_field = ft.TextField(
            value="",
            hint_text="YYYY-MM-DD / 今天 / 明天 / 527",
            text_size=13,
            content_padding=ft.Padding(10, 6, 10, 6),
            border_radius=8,
            expand=True,
            on_submit=self._on_text_submit,
        )

        # 提示
        self._hint_text = ft.Text(
            "点击选择日期，再点另一个变为持续",
            size=11,
            color=AppColors.TEXT_HINT,
        )

        # 月份导航
        self._month_label = ft.Text("", size=14, weight=ft.FontWeight.W_500)
        self._grid_column = ft.Column(spacing=2, tight=True)

        input_row = ft.Row(
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self._text_field,
                ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, icon_size=18,
                              on_click=self._prev_month, tooltip="上个月"),
                self._month_label,
                ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, icon_size=18,
                              on_click=self._next_month, tooltip="下个月"),
            ],
        )

        weekday_row = ft.Row(
            spacing=0,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            controls=[
                ft.Container(
                    width=36, alignment=ft.Alignment(0, 0),
                    content=ft.Text(d, size=11, color=AppColors.TEXT_HINT, weight=ft.FontWeight.W_500),
                ) for d in _WEEKDAY_LABELS
            ],
        )

        # 时间行（动态重建）
        self._time_container = ft.Column(spacing=4, tight=True)

        self._rebuild_grid()
        self._sync_text()
        self._rebuild_time_row()

        self.controls = [
            input_row,
            self._hint_text,
            ft.Container(
                padding=ft.Padding(4, 0, 4, 4),
                border_radius=8,
                bgcolor=AppColors.PANEL_BG,
                content=ft.Column(
                    spacing=2, tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[weekday_row, self._grid_column],
                ),
            ),
            self._time_container,
        ]

    def _build_hour_dd(self, value: int, on_select) -> ft.Dropdown:
        return ft.Dropdown(
            value=f"{value:02d}",
            options=[ft.dropdown.Option(key=f"{h:02d}", text=f"{h:02d}") for h in range(24)],
            width=110,
            text_size=13,
            content_padding=ft.Padding(8, 6, 8, 6),
            border_radius=6,
            on_select=on_select,
            dense=True,
        )

    def _build_minute_dd(self, value: int, on_select) -> ft.Dropdown:
        return ft.Dropdown(
            value=f"{value:02d}",
            options=[ft.dropdown.Option(key=f"{m:02d}", text=f"{m:02d}") for m in range(0, 60, 5)],
            width=110,
            text_size=13,
            content_padding=ft.Padding(8, 6, 8, 6),
            border_radius=6,
            on_select=on_select,
            dense=True,
        )

    def _rebuild_time_row(self):
        """根据当前状态重建时间行。"""
        self._time_container.controls.clear()

        if not self.show_time:
            self._time_container.visible = False
            return
        self._time_container.visible = True

        if not self._range_start:
            return

        if self.is_range and self._range_start == self._range_end:
            # 同天持续：两行（开始/结束）
            self._start_hh = self._build_hour_dd(self._start_hour, self._on_start_time)
            self._start_mm = self._build_minute_dd(self._start_minute, self._on_start_time)
            self._end_hh = self._build_hour_dd(self._end_hour, self._on_end_time)
            self._end_mm = self._build_minute_dd(self._end_minute, self._on_end_time)

            self._time_container.controls = [
                ft.Row(spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("开始", size=12, color=AppColors.TEXT_HINT, width=36),
                    self._start_hh, ft.Text(":", size=13, color=AppColors.TEXT_HINT), self._start_mm,
                ]),
                ft.Row(spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("结束", size=12, color=AppColors.TEXT_HINT, width=36),
                    self._end_hh, ft.Text(":", size=13, color=AppColors.TEXT_HINT), self._end_mm,
                ]),
            ]
        elif self.is_range:
            # 跨天持续：两行（日期+时间）
            self._start_hh = self._build_hour_dd(self._start_hour, self._on_start_time)
            self._start_mm = self._build_minute_dd(self._start_minute, self._on_start_time)
            self._end_hh = self._build_hour_dd(self._end_hour, self._on_end_time)
            self._end_mm = self._build_minute_dd(self._end_minute, self._on_end_time)

            start_label = self._range_start.strftime("%m-%d")
            end_label = self._range_end.strftime("%m-%d")
            self._time_container.controls = [
                ft.Row(spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(start_label, size=12, color=AppColors.TEXT_HINT, width=36),
                    self._start_hh, ft.Text(":", size=13, color=AppColors.TEXT_HINT), self._start_mm,
                ]),
                ft.Row(spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(end_label, size=12, color=AppColors.TEXT_HINT, width=36),
                    self._end_hh, ft.Text(":", size=13, color=AppColors.TEXT_HINT), self._end_mm,
                ]),
            ]
        else:
            # 单日期：一行
            self._start_hh = self._build_hour_dd(self._start_hour, self._on_start_time)
            self._start_mm = self._build_minute_dd(self._start_minute, self._on_start_time)
            self._time_input = ft.TextField(
                hint_text="HH:MM", width=110, text_size=13,
                content_padding=ft.Padding(8, 6, 8, 6), border_radius=6,
                on_submit=self._on_time_text_submit,
            )

            self._time_container.controls = [
                ft.Row(spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("时间", size=12, color=AppColors.TEXT_HINT, width=36),
                    self._start_hh, ft.Text(":", size=13, color=AppColors.TEXT_HINT), self._start_mm,
                    ft.Text("或", size=11, color=AppColors.TEXT_HINT),
                    self._time_input,
                    ft.IconButton(icon=ft.Icons.CHECK, icon_size=16, tooltip="确认",
                                  on_click=self._on_time_text_submit),
                ]),
            ]

    # ── 时间回调 ──

    def _on_start_time(self, e):
        try:
            self._start_hour = int(self._start_hh.value or "0")
            self._start_minute = int(self._start_mm.value or "0")
        except (ValueError, AttributeError):
            pass

    def _on_end_time(self, e):
        try:
            self._end_hour = int(self._end_hh.value or "0")
            self._end_minute = int(self._end_mm.value or "0")
        except (ValueError, AttributeError):
            pass

    def _on_time_text_submit(self, e):
        raw = (self._time_input.value or "").strip()
        m = re.match(r"^(\d{1,2}):(\d{2})$", raw)
        if m:
            h, mi = int(m.group(1)), int(m.group(2))
            if 0 <= h <= 23 and 0 <= mi <= 59:
                self._start_hour = h
                self._start_minute = mi
                self._start_hh.value = f"{h:02d}"
                self._start_mm.value = f"{mi:02d}"
                self._time_input.value = ""
                self._time_input.error_text = None
                self.update()
                return
        self._time_input.error_text = "格式：HH:MM"
        self.update()

    def _sync_time_controls(self):
        """同步时间下拉框值。"""
        try:
            if hasattr(self, '_start_hh') and self._start_hh:
                self._start_hh.value = f"{self._start_hour:02d}"
                self._start_mm.value = f"{self._start_minute:02d}"
            if hasattr(self, '_end_hh') and self._end_hh:
                self._end_hh.value = f"{self._end_hour:02d}"
                self._end_mm.value = f"{self._end_minute:02d}"
        except Exception:
            pass

    # ── 文本同步 ──

    def _sync_text(self):
        if self.is_range:
            self._text_field.value = f"{self._range_start.isoformat()} ~ {self._range_end.isoformat()}"
        elif self._range_start:
            self._text_field.value = self._range_start.isoformat()
        else:
            self._text_field.value = ""

    def _on_text_submit(self, e):
        raw = (self._text_field.value or "").strip()
        if "~" in raw:
            parts = [p.strip() for p in raw.split("~")]
            if len(parts) == 2:
                d1 = self._try_parse(parts[0])
                d2 = self._try_parse(parts[1])
                if d1 and d2 and d1 <= d2:
                    self._range_start = d1
                    self._range_end = d2
                    self._view_year = d1.year
                    self._view_month = d1.month
                    self._sync_text()
                    self._rebuild_time_row()
                    self._rebuild_grid()
                    self._text_field.error_text = None
                    self._fire_change()
                    self.update()
                    return
            self._text_field.error_text = "格式：开始日期 ~ 结束日期"
            self.update()
            return

        parsed = self._try_parse(raw)
        if parsed:
            self._range_start = parsed
            self._range_end = None
            self._view_year = parsed.year
            self._view_month = parsed.month
            self._sync_text()
            self._rebuild_time_row()
            self._rebuild_grid()
            self._text_field.error_text = None
            self._fire_change()
        else:
            self._text_field.error_text = "日期格式无效"
        self.update()

    # ── 日历网格 ──

    def _rebuild_grid(self):
        self._grid_column.controls.clear()
        self._month_label.value = f"{self._view_year}年 {_MONTH_NAMES[self._view_month]}"
        cal = calendar.monthcalendar(self._view_year, self._view_month)
        today = date.today()

        for week in cal:
            cells = []
            for day in week:
                if day == 0:
                    cells.append(ft.Container(width=36, height=30))
                else:
                    d = date(self._view_year, self._view_month, day)
                    is_start = d == self._range_start
                    is_end = self._range_end is not None and d == self._range_end
                    is_in_range = (
                        self._range_start and self._range_end
                        and self._range_start < d < self._range_end
                    )
                    is_today = d == today
                    is_endpoint = is_start or is_end

                    if is_endpoint:
                        bg = ft.Colors.PRIMARY
                    elif is_in_range:
                        bg = ft.Colors.with_opacity(0.18, ft.Colors.PRIMARY)
                    elif is_today:
                        bg = ft.Colors.with_opacity(0.1, ft.Colors.PRIMARY)
                    else:
                        bg = None

                    if is_endpoint:
                        fg = ft.Colors.ON_PRIMARY
                    elif is_in_range:
                        fg = ft.Colors.PRIMARY
                    elif is_today:
                        fg = ft.Colors.PRIMARY
                    else:
                        fg = None

                    weight = ft.FontWeight.W_700 if (is_endpoint or is_today) else ft.FontWeight.W_400

                    cells.append(
                        ft.Container(
                            width=36, height=30, border_radius=15,
                            bgcolor=bg, alignment=ft.Alignment(0, 0),
                            on_click=lambda e, dd=d: self._on_day_click(dd),
                            content=ft.Text(str(day), size=13, weight=weight, color=fg),
                        )
                    )
            self._grid_column.controls.append(
                ft.Row(spacing=0, alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=cells)
            )

    def _on_day_click(self, d: date):
        # 点击已选中的起点 → 取消起点（如果有终点则终点变起点）
        if d == self._range_start:
            if self._range_end:
                self._range_start = self._range_end
                self._range_end = None
                self._start_hour, self._end_hour = self._end_hour, 0
                self._start_minute, self._end_minute = self._end_minute, 0
            else:
                self._range_start = None
                self._start_hour = 0
                self._start_minute = 0
            self._sync_text()
            self._rebuild_time_row()
            self._rebuild_grid()
            self._fire_change()
            self.update()
            return

        # 点击已选中的终点 → 取消终点（回到单日期）
        if d == self._range_end:
            self._range_end = None
            self._end_hour = 0
            self._end_minute = 0
            self._sync_text()
            self._rebuild_time_row()
            self._rebuild_grid()
            self._fire_change()
            self.update()
            return

        # 点击范围中间 → 无操作
        if self._range_start and self._range_end and self._range_start < d < self._range_end:
            return

        # 无起点 → 设置起点
        if not self._range_start:
            self._range_start = d
            self._view_year = d.year
            self._view_month = d.month
        # 有起点无终点 → 设置终点（自动变持续）
        elif not self._range_end:
            if d > self._range_start:
                self._range_end = d
            elif d < self._range_start:
                # 点了更早的日期：交换
                self._range_end = self._range_start
                self._range_start = d
                self._end_hour, self._start_hour = self._start_hour, 0
                self._end_minute, self._start_minute = self._start_minute, 0
            else:
                # 同一天
                self._range_end = d
        # 有起点有终点 → 开始新的选择
        else:
            self._range_start = d
            self._range_end = None
            self._start_hour = 0
            self._start_minute = 0
            self._end_hour = 0
            self._end_minute = 0

        self._sync_text()
        self._rebuild_time_row()
        self._rebuild_grid()
        self._fire_change()
        self.update()

    def _fire_change(self):
        if self.on_change:
            self.on_change(self.range_start, self.range_end)

    # ── 月份导航 ──

    def _prev_month(self, e):
        if self._view_month == 1:
            self._view_month = 12
            self._view_year -= 1
        else:
            self._view_month -= 1
        self._rebuild_grid()
        self.update()

    def _next_month(self, e):
        if self._view_month == 12:
            self._view_month = 1
            self._view_year += 1
        else:
            self._view_month += 1
        self._rebuild_grid()
        self.update()

    # ── 日期解析 ──

    @staticmethod
    def _try_parse(value: str) -> date | None:
        if not value:
            return None
        today = date.today()
        low = value.lower()
        if low in ("今天", "today"):
            return today
        if low in ("明天", "tomorrow"):
            return today + timedelta(days=1)
        if low in ("后天",):
            return today + timedelta(days=2)

        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        # 无年份格式：手动解析避免 DeprecationWarning
        for sep in ("/", "-"):
            parts = value.split(sep)
            if len(parts) == 2:
                try:
                    m, d = int(parts[0]), int(parts[1])
                    return date(today.year, m, d)
                except ValueError:
                    continue

        if value.isdigit():
            if len(value) == 3:
                m, d = int(value[0]), int(value[1:])
                try:
                    return date(today.year, m, d)
                except ValueError:
                    pass
            elif len(value) == 4:
                m, d = int(value[:2]), int(value[2:])
                try:
                    return date(today.year, m, d)
                except ValueError:
                    pass
        return None
