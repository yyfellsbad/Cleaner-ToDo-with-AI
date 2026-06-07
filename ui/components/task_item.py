from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta

import flet as ft

from ui.components.date_picker import CustomDatePicker
from ui.i18n import t
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
        repeat_days=0,
        repeat_mode="once",
        completed_dates=None,
    ):
        super().__init__()
        self.border_radius = 12
        self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS
        self.app = app
        self.task_id = task_id
        self.task_name = task_name
        self.date = date or datetime.now().replace(second=0, microsecond=0)
        self.end_date = end_date
        self.description = description
        self.completed = completed
        self.task_delete = task_delete
        self.repeat_days = repeat_days
        self.repeat_mode = repeat_mode
        self.completed_dates = completed_dates or []
        self._is_new = False  # 标记是否为新添加的任务（入场动画用）

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

    @property
    def ongoing(self) -> bool:
        """当前时间在开始和结束之间（正在持续）。"""
        if not self.end_date or self.completed:
            return False
        now = datetime.now()
        return self.date <= now <= self.end_date

    @property
    def is_recurring(self) -> bool:
        return self.repeat_days > 0 and self.end_date is not None

    def mark_occurrence(self, d) -> bool:
        key = d.isoformat()
        if key in self.completed_dates:
            return False
        self.completed_dates.append(key)
        done, total = self._repeat_progress()
        if done >= total:
            self.completed = True
        return True

    def unmark_occurrence(self, d) -> bool:
        key = d.isoformat()
        if key not in self.completed_dates:
            return False
        self.completed_dates.remove(key)
        self.completed = False
        return True

    def _repeat_label(self) -> str:
        if self.repeat_days <= 0:
            return ""
        if self.repeat_days == 1:
            return t("repeat.every_day")
        return t("repeat.every_n_days", self.repeat_days)

    def _repeat_progress(self) -> tuple[int, int]:
        """返回 (已完成数, 总数) for each 模式。"""
        if not self.is_recurring or self.repeat_mode != "each":
            return 0, 0
        start = self.date.date()
        end = self.end_date.date()
        total = 0
        d = start
        while d <= end:
            total += 1
            d = date.fromordinal(d.toordinal() + self.repeat_days)
        done = len(self.completed_dates)
        return done, total

    def _is_default_end_date(self) -> bool:
        """判断 end_date 是否是系统默认的免打扰开始时间（用户未手动设置）"""
        if not self.end_date:
            return False
        from services.notification_service import NotificationService
        dnd_start = NotificationService.instance().dnd_start
        try:
            h, m = map(int, dnd_start.split(":"))
            return (
                self.end_date.hour == h
                and self.end_date.minute == m
                and self.end_date.date() == self.date.date()
            )
        except (ValueError, AttributeError):
            return False

    def _get_date_display(self):
        today = datetime.now().date()
        start_label = self._fmt_short(self.date)

        repeat_suffix = ""
        if self.is_recurring:
            repeat_suffix = f" · {self._repeat_label()}"
            if self.repeat_mode == "each":
                done, total = self._repeat_progress()
                repeat_suffix += f" · {t('repeat.progress', done, total)}"
            else:
                repeat_suffix += f" · {t('repeat.once_mode')}"

        # 如果 end_date 是默认值（免打扰开始时间），不显示到期时间
        if self.end_date and not self._is_default_end_date():
            end_label = self._fmt_short(self.end_date)
            if self.date.date() == self.end_date.date():
                # 同一天，只显示到期时间
                text = f"📅 {end_label}{repeat_suffix}"
                color = AppColors.DATE_ONGOING if self.ongoing else AppColors.DATE_FUTURE
                return text, color, 12
            text = f"📅 {start_label} ~ {end_label}{repeat_suffix}"
            color = AppColors.DATE_ONGOING if self.ongoing else AppColors.DATE_FUTURE
            return text, color, 12

        if self.date.date() > today:
            return f"📅 {start_label}{repeat_suffix}", AppColors.DATE_FUTURE, 13
        elif self.date.date() == today:
            return f"📅 {start_label}{repeat_suffix}", AppColors.DATE_TODAY, 13
        else:
            return f"📅 {start_label}{repeat_suffix}", AppColors.DATE_PAST, 12

    def build(self):
        self.display_task = ft.Checkbox(
            value=False, label=self.task_name, on_change=self.status_changed
        )
        self.edit_name = ft.TextField(expand=1)
        date_text, date_color, date_size = self._get_date_display()

        self._action_row = ft.Row(
            spacing=8,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.CREATE_OUTLINED,
                    tooltip=t("task.edit"),
                    icon_size=18,
                    on_click=self.edit_clicked,
                ),
                ft.IconButton(
                    ft.Icons.DELETE_OUTLINE,
                    tooltip=t("task.delete"),
                    icon_size=18,
                    on_click=self.delete_clicked,
                ),
                ft.Container(width=8),  # 与排序手柄保持距离
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
                            tooltip=t("task.confirm"),
                            icon_size=18,
                            on_click=self._save_date_edit,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            tooltip=t("task.cancel"),
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

        # 进度条：持续任务显示时间进度
        self._progress_bar = None
        if self.end_date and not self.completed:
            now = datetime.now()
            total_seconds = (self.end_date - self.date).total_seconds()
            if total_seconds > 0:
                elapsed_seconds = (now - self.date).total_seconds()
                progress = max(0.0, min(1.0, elapsed_seconds / total_seconds))
                if progress >= 0.9:
                    progress_color = ft.Colors.ERROR
                elif progress >= 0.75:
                    progress_color = ft.Colors.DEEP_ORANGE
                elif progress >= 0.6:
                    progress_color = ft.Colors.ORANGE
                elif progress >= 0.45:
                    progress_color = ft.Colors.AMBER
                elif progress >= 0.3:
                    progress_color = ft.Colors.TEAL
                else:
                    progress_color = ft.Colors.PRIMARY
                self._progress_bar = ft.ProgressBar(
                    value=progress,
                    height=3,
                    border_radius=2,
                    color=progress_color,
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
                )

        date_controls = [self._date_display_text, self._date_editor_row]
        if self._progress_bar:
            date_controls.append(ft.Container(
                padding=ft.Padding(0, 4, 0, 0),
                content=self._progress_bar,
            ))

        date_area = ft.Column(
            spacing=0,
            tight=True,
            controls=date_controls,
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
                padding=ft.Padding(8, 2, 8, 2),
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY),
                content=ft.Text(t("task.completed_tag"), size=10, color=ft.Colors.PRIMARY, weight=ft.FontWeight.W_500),
            )
        elif self.expired:
            card_bg = AppColors.PANEL_BG
            card_opacity = 0.5
            status_tag = ft.Container(
                padding=ft.Padding(8, 2, 8, 2),
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.ERROR),
                content=ft.Text(t("task.expired_tag"), size=10, color=ft.Colors.ERROR, weight=ft.FontWeight.W_500),
            )
        else:
            card_bg = AppColors.PANEL_BG
            card_opacity = 1.0
            status_tag = None

        # 新任务入场动画：初始透明
        if self._is_new:
            card_opacity = 0.0

        self._status_tag = status_tag

        self.display_view = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            content=ft.Container(
                border_radius=12,
                padding=ft.Padding(20, 12, 20, 12),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE_VARIANT)),
                bgcolor=card_bg,
                opacity=card_opacity,
                animate_opacity=250,
                animate_scale=250,
                scale=ft.Scale(1.0),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=0,
                    color=ft.Colors.with_opacity(0, ft.Colors.BLACK),
                    offset=ft.Offset(0, 0),
                ),
                on_hover=self._on_card_hover,
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
            hint_text=t("task.desc_hint"),
            expand=True,
            text_size=13,
            content_padding=ft.Padding(8, 4, 8, 4),
            border_radius=6,
            multiline=True,
            min_lines=1,
            max_lines=3,
        )

        # ── 重复设置编辑器：频率预设 Chip ──
        self._repeat_presets = [
            (0, t("repeat.not_repeat")),
            (1, t("repeat.every_day")),
            (2, t("repeat.every_2_days")),
            (3, t("repeat.every_3_days")),
            (7, t("repeat.every_7_days")),
            (-1, t("repeat.custom")),
        ]
        self._edit_freq_chips = ft.Row(
            spacing=4, wrap=True,
            controls=[
                ft.Chip(
                    label=ft.Text(label, size=11),
                    data=days,
                    selected=False,
                    on_select=lambda e, d=days: self._on_freq_chip_select(d),
                )
                for days, label in self._repeat_presets
            ],
        )
        self._edit_custom_days = ft.TextField(
            width=60, text_size=13,
            content_padding=ft.Padding(8, 4, 8, 4),
            border_radius=6,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="N",
            visible=False,
            on_change=self._on_custom_days_change,
        )
        self._edit_custom_row = ft.Row(
            spacing=6, visible=False,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(t("repeat.custom"), size=11, color=AppColors.TEXT_HINT),
                self._edit_custom_days,
                ft.Text(t("task.repeat_days_unit"), size=11),
            ],
        )
        self._repeat_edit_column = ft.Column(
            spacing=4, tight=True,
            controls=[
                ft.Text(t("task.repeat"), size=12, color=AppColors.TEXT_HINT),
                self._edit_freq_chips,
                self._edit_custom_row,
            ],
        )

        # ── 到期时间编辑器 ──
        self._end_time_edit = ft.Row(
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(t("task.end_time"), size=12, color=AppColors.TEXT_HINT),
                ft.Dropdown(
                    options=[ft.dropdown.Option(f"{h:02d}") for h in range(24)],
                    value=f"{self.end_date.hour:02d}" if self.end_date else "23",
                    width=90,
                    text_size=13,
                    border_radius=6,
                ),
                ft.Text(":", size=12),
                ft.Dropdown(
                    options=[ft.dropdown.Option(f"{m:02d}") for m in [0, 15, 30, 45]],
                    value=f"{self.end_date.minute:02d}" if self.end_date else "00",
                    width=90,
                    text_size=13,
                    border_radius=6,
                ),
            ],
        )

        self.edit_view = ft.Column(
            visible=False,
            spacing=4,
            controls=[
                self.edit_name,
                self.edit_desc,
                self._end_time_edit,
                self._repeat_edit_column,
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                            icon_color=AppColors.EDIT_CONFIRM_ICON,
                            tooltip=t("task.confirm"),
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
        # 更新到期时间选择器显示当前值
        hour_dd = self._end_time_edit.controls[1]
        minute_dd = self._end_time_edit.controls[3]
        if self.end_date:
            hour_dd.value = f"{self.end_date.hour:02d}"
            minute_dd.value = f"{self.end_date.minute:02d}"
        else:
            hour_dd.value = "23"
            minute_dd.value = "00"
        hour_dd.update()
        minute_dd.update()
        # 只在有持续（end_date）时显示重复设置
        has_range = self.end_date is not None
        self._repeat_edit_column.visible = has_range
        # 初始化频率 Chips
        self._edit_custom_days.value = ""
        self._edit_custom_row.visible = False
        preset_days = {d for d, _ in self._repeat_presets if d > 0}
        is_custom = self.repeat_days > 0 and self.repeat_days not in preset_days
        for chip in self._edit_freq_chips.controls:
            if chip.data == -1:
                chip.selected = is_custom
            elif self.repeat_days == 0:
                chip.selected = (chip.data == 0)
            else:
                chip.selected = (chip.data == self.repeat_days)
        if is_custom:
            self._edit_custom_row.visible = True
            self._edit_custom_days.value = str(self.repeat_days)
        self.display_view.visible = False
        self.edit_view.visible = True
        self.update()

    def _on_freq_chip_select(self, days: int):
        if days == -1:  # 自定义
            self._edit_custom_row.visible = not self._edit_custom_row.visible
            if self._edit_custom_row.visible:
                self._edit_custom_days.focus()
        else:
            self._edit_custom_row.visible = False
            self._edit_custom_days.value = ""
        for chip in self._edit_freq_chips.controls:
            chip.selected = (chip.data == days) if days != -1 else (chip.data == -1)
        self.update()

    def _on_custom_days_change(self, e):
        pass

    def _get_edit_repeat_days(self) -> int:
        for chip in self._edit_freq_chips.controls:
            if chip.selected and chip.data > 0:
                return chip.data
            if chip.selected and chip.data == -1:
                try:
                    return int(self._edit_custom_days.value or 0)
                except ValueError:
                    return 0
        return 0

    def save_clicked(self, e):
        self.task_name = self.edit_name.value
        self.description = self.edit_desc.value or ""
        # 保存到期时间 - 无论之前是否有到期时间，都保存用户编辑的值
        if self._end_time_edit.visible:
            hour = int(self._end_time_edit.controls[1].value)
            minute = int(self._end_time_edit.controls[3].value)
            if self.end_date:
                self.end_date = self.end_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            elif self.date:
                # 如果之前没有到期时间，基于任务日期创建
                self.end_date = self.date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        self.repeat_days = self._get_edit_repeat_days()
        self.repeat_mode = "each"
        self._desc_text.value = self.description
        self._desc_text.visible = bool(self.description)
        self._desc_display.mouse_cursor = (
            ft.MouseCursor.CLICK if self.description else ft.MouseCursor.BASIC
        )
        self._desc_expanded = False
        self._desc_text.max_lines = 1
        self._refresh_date_display()
        self._refresh_progress_bar()
        self.display_view.visible = True
        self.edit_view.visible = False
        self.app.save_task(self)
        self.update()

    # ── 状态变更 ──

    async def status_changed(self, e):
        self.completed = e.control.value
        # 重复任务 each 模式：打卡/取消打卡当天
        if self.is_recurring and self.repeat_mode == "each":
            from datetime import date as _date
            today = _date.today()
            if self.completed:
                self.mark_occurrence(today)
            else:
                self.unmark_occurrence(today)
        card = self.display_view.content
        # 完成时短暂高亮后变暗
        if self.completed:
            card.bgcolor = ft.Colors.with_opacity(0.15, ft.Colors.PRIMARY)
            card.update()
            await asyncio.sleep(0.3)
        self._refresh_card_style()
        self._refresh_date_display()
        self._refresh_progress_bar()
        self.app.save_task(self)
        self.update()

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
        # 只有当用户明确选择了结束日期时才更新，否则保留原来的结束日期
        if parsed_end:
            self.end_date = parsed_end
        # 如果之前没有结束日期，使用默认值
        elif not self.end_date:
            from services.task_service import _default_end_date
            self.end_date = _default_end_date(self.date)
        # 持续消失时清除重复设置
        if not parsed_end:
            self.repeat_days = 0
            self.repeat_mode = "once"
        self._refresh_date_display()
        self._refresh_progress_bar()
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

    def _refresh_progress_bar(self):
        """刷新进度条的状态。"""
        # 找到日期区域（第一个 tight Column）
        content_col = self.display_view.content.content
        if not hasattr(content_col, 'controls'):
            return
        date_area = None
        for ctrl in content_col.controls:
            if isinstance(ctrl, ft.Column) and ctrl.tight:
                date_area = ctrl
                break
        
        if not date_area:
            return
        
        # 如果需要进度条但没有
        if self.end_date and not self.completed:
            now = datetime.now()
            total_seconds = (self.end_date - self.date).total_seconds()
            if total_seconds > 0:
                elapsed_seconds = (now - self.date).total_seconds()
                progress = max(0.0, min(1.0, elapsed_seconds / total_seconds))
                
                # 确定进度条颜色
                if progress >= 0.9:
                    progress_color = ft.Colors.ERROR
                elif progress >= 0.75:
                    progress_color = ft.Colors.DEEP_ORANGE
                elif progress >= 0.6:
                    progress_color = ft.Colors.ORANGE
                elif progress >= 0.45:
                    progress_color = ft.Colors.AMBER
                elif progress >= 0.3:
                    progress_color = ft.Colors.TEAL
                else:
                    progress_color = ft.Colors.PRIMARY
                
                # 如果已有进度条，更新其值和颜色
                if self._progress_bar:
                    self._progress_bar.value = progress
                    self._progress_bar.color = progress_color
                    self._progress_bar.update()
                else:
                    # 创建新进度条
                    self._progress_bar = ft.ProgressBar(
                        value=progress,
                        height=3,
                        border_radius=2,
                        color=progress_color,
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
                    )
                    date_area.controls.append(ft.Container(
                        padding=ft.Padding(0, 4, 0, 0),
                        content=self._progress_bar,
                    ))
        else:
            # 不需要进度条，移除它
            if self._progress_bar:
                for i, ctrl in enumerate(date_area.controls):
                    if isinstance(ctrl, ft.Container) and ctrl.content == self._progress_bar:
                        date_area.controls.pop(i)
                        self._progress_bar = None
                        break

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

    async def animate_exit(self):
        """任务删除退出动画：淡出并缩小。"""
        card = self.display_view.content
        card.opacity = 0
        card.scale = ft.Scale(0.9)
        self.update()
        await asyncio.sleep(0.25)

    def _on_card_hover(self, e):
        """鼠标悬停时卡片轻微抬升。"""
        card = self.display_view.content
        if e.data == "true":
            card.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            )
        else:
            card.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=0,
                color=ft.Colors.with_opacity(0, ft.Colors.BLACK),
                offset=ft.Offset(0, 0),
            )
        card.update()
