from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import flet as ft
from ui.i18n import t
from flet_charts import (
    BarChart,
    BarChartGroup,
    BarChartRod,
    ChartAxis,
    ChartAxisLabel,
    PieChart,
    PieChartSection,
)

if TYPE_CHECKING:
    from services.task_service import TaskService

# ── 颜色常量（莫兰迪色系）────────────────────────────────
COLOR_DONE = "#8E9AAF"       # 灰蓝
COLOR_ONGOING = "#A7B5A0"    # 灰绿
COLOR_EXPIRED = "#C4A882"    # 灰棕
COLOR_PENDING = "#B8B8B8"    # 中灰
COLOR_NEW_TREND = "#B5C4D5"     # 浅灰蓝
COLOR_DONE_TREND = "#B8C9B3"    # 浅灰绿
COLOR_EXPIRED_TREND = "#D4BFA8"  # 浅灰棕

_ANIM_DURATION = 0.75  # 翻滚动画总时长（秒）
_ANIM_STEPS = 25       # 动画帧数


class StatsView(ft.Column):
    """数据统计页面：概览卡片 + 环状图 + 今日待办 + 7 天趋势。"""

    def __init__(self, task_service: TaskService):
        super().__init__()
        self._task_service = task_service
        self.expand = True
        self.spacing = 0
        self.scroll = ft.ScrollMode.AUTO
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

        self._animated_items: list[ft.Control] = []
        self._number_targets: list[tuple[ft.Text, int, str]] = []

        self._build_ui()

    # ── 构建 ─────────────────────────────────────────────

    def _build_ui(self):
        self._animated_items.clear()
        self._number_targets.clear()

        # 标题行
        header = ft.Row(
            controls=[
                ft.Text(t("stats.title"), size=22, weight=ft.FontWeight.W_600),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.REFRESH_ROUNDED,
                    tooltip=t("stats.refresh"),
                    on_click=self._on_refresh,
                ),
            ],
        )

        # 概览卡片
        self._cards_row = ft.Row(
            spacing=12,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            wrap=False,
        )

        # 环状图 + 图例容器
        self._donut_stack = ft.Stack(alignment=ft.Alignment.CENTER)
        self._donut_with_legend = ft.Row(
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._donut_panel = ft.Container(
            content=self._donut_with_legend,
            padding=ft.Padding(16, 12, 16, 12),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            height=240,
            opacity=0,
            animate_opacity=200,
            animate_scale=200,
            scale=ft.Scale(0.85),
        )
        self._animated_items.append(self._donut_panel)

        # 柱状图容器
        self._trend_chart = ft.Container(
            padding=ft.Padding(16, 12, 16, 12),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            expand=True,
            height=240,
            opacity=0,
            animate_opacity=200,
        )
        self._animated_items.append(self._trend_chart)

        # 环状图 + 柱状图 同一行
        self._charts_row = ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                self._donut_panel,
                self._trend_chart,
            ],
        )

        # 今日待办
        self._today_list = ft.Column(spacing=6)
        self._today_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(t("stats.today_tasks"), size=16, weight=ft.FontWeight.W_500),
                    self._today_list,
                ],
                spacing=8,
            ),
            padding=ft.Padding(16, 12, 16, 12),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            opacity=0,
            animate_opacity=150,
        )
        self._animated_items.append(self._today_container)

        self.controls = [
            ft.Container(
                expand=True,
                padding=ft.Padding(24, 16, 48, 16),
                content=ft.Column(
                    spacing=20,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        header,
                        self._cards_row,
                        self._charts_row,
                        self._today_container,
                    ],
                ),
            ),
        ]

        self._load_data()

    # ── 数据加载 ─────────────────────────────────────────

    def _load_data(self):
        tasks = self._task_service.list_tasks("all")
        now = datetime.now()
        today = now.date()

        total = len(tasks)
        done = sum(1 for tk in tasks if self._is_done(tk))
        ongoing = sum(1 for tk in tasks if self._is_ongoing(tk, now))
        expired = sum(1 for tk in tasks if self._is_expired(tk, today))
        pending = total - done - ongoing - expired
        if pending < 0:
            pending = 0
        rate = round(done / total * 100) if total > 0 else 0

        self._build_cards(total, done, rate, expired)
        self._build_donut(done, ongoing, expired, pending, total)
        self._build_today(tasks, now, today)
        self._build_trend(tasks, today)

    # ── 重复任务状态判断 ───────────────────────────────────

    @staticmethod
    def _is_done(tk) -> bool:
        if tk.repeat_mode == "each" and tk.is_recurring:
            return tk.all_occurrences_done
        return tk.completed

    @staticmethod
    def _is_expired(tk, today) -> bool:
        if StatsView._is_done(tk):
            return False
        deadline = (tk.end_date or tk.date).date()
        if deadline >= today:
            return False
        if tk.repeat_mode == "each" and tk.is_recurring:
            return True
        return not tk.completed

    @staticmethod
    def _is_ongoing(tk, now) -> bool:
        if not tk.end_date or StatsView._is_done(tk):
            return False
        return tk.date <= now <= tk.end_date

    # ── 概览卡片 ─────────────────────────────────────────

    def _build_cards(self, total, done, rate, expired):
        cards_data = [
            (ft.Icons.LIST_ALT_ROUNDED, total, t("stats.total"), "#9DA5B4", ""),
            (ft.Icons.CHECK_CIRCLE_OUTLINE, done, t("stats.completed"), COLOR_DONE, ""),
            (ft.Icons.PIE_CHART_OUTLINE, rate, t("stats.rate"), COLOR_ONGOING, "%"),
            (ft.Icons.WARNING_AMBER_ROUNDED, expired, t("stats.expired"), COLOR_EXPIRED, ""),
        ]
        cards = []
        for i, (icon, value, label, color, suffix) in enumerate(cards_data):
            num_text = ft.Text("0" + suffix, size=24, weight=ft.FontWeight.W_700)
            self._number_targets.append((num_text, value, suffix))
            card = ft.Container(
                expand=True,
                padding=ft.Padding(12, 14, 12, 14),
                border_radius=12,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                opacity=0,
                animate_opacity=150,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.Icon(icon, color=color, size=24),
                        num_text,
                        ft.Text(label, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                ),
            )
            cards.append(card)
            self._animated_items.append(card)
        self._cards_row.controls = cards

    # ── 环状图 ───────────────────────────────────────────

    def _build_donut(self, done, ongoing, expired, pending, total):
        sections = []
        legend_items = []
        legend_data = [
            (done, COLOR_DONE, t("stats.completed")),
            (ongoing, COLOR_ONGOING, t("stats.in_progress")),
            (expired, COLOR_EXPIRED, t("stats.expired")),
            (pending, COLOR_PENDING, t("stats.not_started")),
        ]
        for count, color, label in legend_data:
            if count > 0:
                sections.append(PieChartSection(value=count, color=color))
            num_text = ft.Text("0", size=12)
            self._number_targets.append((num_text, count, ""))
            legend_items.append(
                ft.Row(
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(width=10, height=10, border_radius=5, bgcolor=color),
                        ft.Text(f"{label}  ", size=12),
                        num_text,
                    ],
                )
            )

        if not sections:
            sections.append(PieChartSection(value=1, color=COLOR_PENDING))

        pie = PieChart(
            sections=sections,
            sections_space=2,
            center_space_radius=60,
            animation=True,
            width=200,
            height=200,
        )

        # 中心总数
        self._center_total = ft.Text("0", size=24, weight=ft.FontWeight.W_700)
        self._number_targets.append((self._center_total, total, ""))

        center_text = ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0,
                controls=[
                    self._center_total,
                    ft.Text(t("stats.sum"), size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
            ),
            alignment=ft.Alignment.CENTER,
            width=200,
            height=200,
        )

        legend = ft.Column(
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=legend_items,
        )

        self._donut_stack.controls = [pie, center_text]
        self._donut_with_legend.controls = [
            ft.Container(content=self._donut_stack, width=200, height=200),
            legend,
        ]
        self._donut_panel.content = self._donut_with_legend

    # ── 今日待办 ─────────────────────────────────────────

    def _build_today(self, tasks, now, today):
        today_tasks = []
        for tk in tasks:
            if tk.repeat_mode == "each" and tk.is_recurring:
                start = tk.date.date()
                end = tk.end_date.date()
                if start <= today <= end:
                    diff = (today - start).days
                    if diff % tk.repeat_days == 0 and not tk.occurrence_done(today):
                        today_tasks.append(tk)
            elif not tk.completed:
                if tk.date.date() == today or (
                    tk.end_date and tk.date.date() <= today <= tk.end_date.date()
                ):
                    today_tasks.append(tk)

        if not today_tasks:
            self._today_list.controls = [
                ft.Container(
                    padding=ft.Padding(0, 16, 0, 16),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text(
                        t("stats.no_today"),
                        size=13,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                )
            ]
            return

        items = []
        for tk in today_tasks:
            if tk.end_date and tk.date <= now <= tk.end_date:
                tag_color = COLOR_ONGOING
                tag_text = t("stats.in_progress")
            elif tk.date.date() == today:
                tag_color = ft.Colors.ORANGE
                tag_text = t("stats.today_tag")
            else:
                tag_color = ft.Colors.GREY
                tag_text = t("stats.pending_tag")

            time_str = tk.date.strftime("%H:%M") if tk.date.hour or tk.date.minute else ""

            repeat_suffix = ""
            if tk.repeat_days > 0:
                repeat_suffix = f" · {t('repeat.every_day') if tk.repeat_days == 1 else t('repeat.every_n_days', tk.repeat_days)}"
                if tk.repeat_mode == "each" and tk.is_recurring:
                    done = len(tk.completed_dates)
                    repeat_suffix += f" · {t('repeat.progress', done, len(tk.repeat_occurrences))}"
                else:
                    repeat_suffix += f" · {t('repeat.once_mode')}"

            items.append(
                ft.Container(
                    padding=ft.Padding(10, 8, 10, 8),
                    border_radius=8,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    content=ft.Row(
                        controls=[
                            ft.Text(f"{tk.name}{repeat_suffix}", size=13, expand=True),
                            *(
                                [ft.Text(time_str, size=12, color=ft.Colors.ON_SURFACE_VARIANT)]
                                if time_str
                                else []
                            ),
                            ft.Container(
                                padding=ft.Padding(6, 2, 6, 2),
                                border_radius=4,
                                bgcolor=tag_color,
                                content=ft.Text(
                                    tag_text,
                                    size=10,
                                    color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.W_500,
                                ),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        self._today_list.controls = items

    # ── 7 天趋势 ─────────────────────────────────────────

    def _build_trend(self, tasks, today):
        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        day_labels = [d.strftime("%m/%d") for d in days]

        new_counts = []
        done_counts = []
        expired_counts = []
        for d in days:
            new_count = sum(1 for tk in tasks if tk.date.date() == d)
            done_count = 0
            expired_count = 0
            for tk in tasks:
                deadline = (tk.end_date or tk.date).date()
                if tk.repeat_mode == "each" and tk.is_recurring:
                    if tk.all_occurrences_done and deadline == d:
                        done_count += 1
                    elif not tk.all_occurrences_done and deadline == d and deadline < today:
                        expired_count += 1
                else:
                    if tk.completed and tk.date.date() == d:
                        done_count += 1
                    elif not tk.completed and deadline == d and deadline < today:
                        expired_count += 1
            new_counts.append(new_count)
            done_counts.append(done_count)
            expired_counts.append(expired_count)

        max_val = max(
            max(new_counts, default=0),
            max(done_counts, default=0),
            max(expired_counts, default=0),
            1,
        )

        groups = []
        for i, (new_c, done_c, exp_c) in enumerate(zip(new_counts, done_counts, expired_counts)):
            groups.append(
                BarChartGroup(
                    x=i,
                    rods=[
                        BarChartRod(from_y=0, to_y=new_c, color=COLOR_NEW_TREND, width=10, border_radius=3),
                        BarChartRod(from_y=0, to_y=done_c, color=COLOR_DONE_TREND, width=10, border_radius=3),
                        BarChartRod(from_y=0, to_y=exp_c, color=COLOR_EXPIRED_TREND, width=10, border_radius=3),
                    ],
                )
            )

        chart = BarChart(
            groups=groups,
            min_y=0,
            max_y=max_val + 1,
            interactive=True,
            animation=True,
            expand=True,
            bottom_axis=ChartAxis(
                show_labels=True,
                labels=[
                    ChartAxisLabel(value=i, label=ft.Text(lb, size=9))
                    for i, lb in enumerate(day_labels)
                ],
            ),
            left_axis=ChartAxis(
                show_labels=True,
                labels=[
                    ChartAxisLabel(value=v, label=ft.Text(str(v), size=9))
                    for v in range(0, max_val + 2, max(1, max_val // 4))
                ],
            ),
        )

        legend = ft.Row(
            spacing=12,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Container(width=10, height=10, border_radius=2, bgcolor=COLOR_NEW_TREND),
                        ft.Text(t("stats.trend_added"), size=10),
                    ],
                ),
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Container(width=10, height=10, border_radius=2, bgcolor=COLOR_DONE_TREND),
                        ft.Text(t("stats.trend_completed"), size=10),
                    ],
                ),
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Container(width=10, height=10, border_radius=2, bgcolor=COLOR_EXPIRED_TREND),
                        ft.Text(t("stats.trend_expired"), size=10),
                    ],
                ),
            ],
        )

        self._trend_chart.content = ft.Column(
            controls=[
                ft.Text(t("stats.trend_title"), size=14, weight=ft.FontWeight.W_500),
                ft.Container(content=chart, expand=True),
                legend,
            ],
            spacing=6,
            expand=True,
        )

    # ── 数字翻滚动画 ─────────────────────────────────────

    async def _animate_numbers(self):
        """从 0 翻滚增长到目标值，持续 0.75 秒。"""
        delay = _ANIM_DURATION / _ANIM_STEPS
        for step in range(1, _ANIM_STEPS + 1):
            ratio = step / _ANIM_STEPS
            # ease-out 缓动
            ratio = 1 - (1 - ratio) ** 3
            for text_ctrl, target, suffix in self._number_targets:
                current = round(target * ratio)
                text_ctrl.value = str(current) + suffix
            self.update()
            await asyncio.sleep(delay)
        # 确保最终值精确
        for text_ctrl, target, suffix in self._number_targets:
            text_ctrl.value = str(target) + suffix
        self.update()

    # ── 刷新（重播动画）──────────────────────────────────

    async def _reveal(self):
        """触发入场：卡片立即显示，其余依次出现，然后数字翻滚。"""
        # 卡片一次性全部显示
        for card in self._cards_row.controls:
            card.opacity = 1
        self.update()

        await asyncio.sleep(0.08)

        # 环状图面板
        self._donut_panel.opacity = 1
        self._donut_panel.scale = ft.Scale(1.0)
        self.update()

        await asyncio.sleep(0.08)

        # 柱状图
        self._trend_chart.opacity = 1
        self.update()

        await asyncio.sleep(0.08)

        # 今日待办
        self._today_container.opacity = 1
        self.update()

        # 数字翻滚
        await self._animate_numbers()

    async def _on_refresh(self, e):
        for item in self._animated_items:
            item.opacity = 0
        self._donut_panel.scale = ft.Scale(0.85)
        self.update()

        await asyncio.sleep(0.1)

        self._load_data()
        await self._reveal()

    def refresh_data(self):
        self._load_data()
        for item in self._animated_items:
            item.opacity = 1
        self._donut_panel.scale = ft.Scale(1.0)
        self.update()
        asyncio.ensure_future(self._animate_numbers())

    def animate_in(self):
        for item in self._animated_items:
            item.opacity = 0
        self._donut_panel.scale = ft.Scale(0.85)
        self.update()
        self._load_data()
        asyncio.ensure_future(self._reveal())
