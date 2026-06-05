from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
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
    from storage.daily_assessment_repo import DailyAssessmentRepo

# ── 颜色常量（跟随主题）────────────────────────────────
COLOR_DONE = ft.Colors.TERTIARY
COLOR_ONGOING = ft.Colors.SECONDARY
COLOR_EXPIRED = ft.Colors.ERROR
COLOR_PENDING = ft.Colors.OUTLINE
COLOR_NEW_TREND = ft.Colors.PRIMARY_CONTAINER
COLOR_DONE_TREND = ft.Colors.TERTIARY_CONTAINER
COLOR_EXPIRED_TREND = ft.Colors.ERROR_CONTAINER

# 热力图颜色（跟随主题，基于 GREEN 的透明度阶梯）
HEAT_COLORS = [
    None,                                # 0: 使用默认底色
    ft.Colors.with_opacity(0.15, ft.Colors.GREEN),   # 1: 浅
    ft.Colors.with_opacity(0.30, ft.Colors.GREEN),   # 2: 中
    ft.Colors.with_opacity(0.55, ft.Colors.GREEN),   # 3: 深
    ft.Colors.with_opacity(0.85, ft.Colors.GREEN),   # 4: 满
]
HEAT_CELL = 12
HEAT_GAP = 2

_ANIM_DURATION = 0.75  # 翻滚动画总时长（秒）
_ANIM_STEPS = 25       # 动画帧数


class StatsView(ft.Column):
    """数据统计页面：概览卡片 + 环状图 + 今日待办 + 7 天趋势。"""

    def __init__(self, task_service: TaskService, assessment_repo: DailyAssessmentRepo | None = None):
        super().__init__()
        self._task_service = task_service
        self._assessment_repo = assessment_repo
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

        # 热力图 + 今日评估（合并卡片）
        self._heatmap_year = datetime.now().year
        self._heatmap_cells: dict[str, ft.Container] = {}
        self._today_assess_chips = ft.Row(spacing=8, wrap=True)
        self._heatmap_container = ft.Container(
            content=ft.Column(spacing=4),
            padding=ft.Padding(16, 12, 16, 12),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            opacity=0,
            animate_opacity=150,
        )
        self._animated_items.append(self._heatmap_container)

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
                        self._heatmap_container,
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
        self._backfill_assessments(tasks, today)
        self._build_heatmap(today)
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
            (ft.Icons.LIST_ALT_ROUNDED, total, t("stats.total"), ft.Colors.OUTLINE, ""),
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

    # ── 热力图 ─────────────────────────────────────────

    def _backfill_assessments(self, tasks, today: date):
        """自动回填未手动评估的历史日期（当年）。"""
        if not self._assessment_repo:
            return
        year_start = date(today.year, 1, 1)
        existing = self._assessment_repo.get_range(
            year_start.isoformat(), today.isoformat()
        )
        assessed = {r["date"] for r in existing if r["manual"] == 1}

        d = year_start
        while d <= today:
            ds = d.isoformat()
            if ds in assessed:
                d += timedelta(days=1)
                continue
            # 统计当天应完成和已完成的任务数
            should = 0
            completed = 0
            for tk in tasks:
                if tk.repeat_mode == "each" and tk.is_recurring:
                    occurrences = tk.repeat_occurrences
                    if d in occurrences:
                        should += 1
                        if tk.occurrence_done(d):
                            completed += 1
                else:
                    task_start = tk.date.date()
                    task_end = tk.end_date.date() if tk.end_date else task_start
                    if task_start <= d <= task_end:
                        should += 1
                        if tk.completed:
                            completed += 1
            if should > 0:
                ratio = completed / should
                if ratio >= 0.76:
                    score = 4
                elif ratio >= 0.51:
                    score = 3
                elif ratio >= 0.26:
                    score = 2
                else:
                    score = 1
                self._assessment_repo.upsert(ds, score, 0)
            d += timedelta(days=1)

    def _build_heatmap(self, today: date):
        """构建全年热力图 + 今日评估合并卡片。"""
        year = self._heatmap_year
        is_current_year = year == today.year

        # 全年日期范围
        jan1 = date(year, 1, 1)
        dec31 = date(year, 12, 31)

        # 读取评估数据（整年）
        assessments: dict[str, int] = {}
        if self._assessment_repo:
            rows = self._assessment_repo.get_range(
                jan1.isoformat(), dec31.isoformat()
            )
            assessments = {r["date"]: r["score"] for r in rows}

        # 星期标签
        weekday_labels = t("stats.heatmap_weekdays").split(",")

        # 1月1日所在周的周一
        first_monday = jan1 - timedelta(days=jan1.weekday())

        # 构建网格列（按周分组）
        self._heatmap_cells.clear()
        columns: list[ft.Control] = []
        # 记录每个月占据的列范围 {month: (first_col_idx, last_col_idx)}
        month_col_ranges: dict[int, tuple[int, int]] = {}
        col_idx = 0
        week_start = first_monday

        while week_start <= dec31:
            # 统计该周各月天数
            for wd in range(7):
                cell_date = week_start + timedelta(days=wd)
                if jan1 <= cell_date <= dec31:
                    m = cell_date.month
                    if m not in month_col_ranges:
                        month_col_ranges[m] = (col_idx, col_idx)
                    else:
                        month_col_ranges[m] = (month_col_ranges[m][0], col_idx)

            # 该周的 7 天
            day_cells = []
            for wd in range(7):
                cell_date = week_start + timedelta(days=wd)
                if cell_date < jan1 or cell_date > dec31:
                    day_cells.append(ft.Container(width=HEAT_CELL, height=HEAT_CELL))
                    continue

                ds = cell_date.isoformat()
                score = assessments.get(ds, 0)
                is_future = cell_date > today

                if is_future:
                    bg = ft.Colors.SURFACE_CONTAINER_HIGHEST
                    tooltip = ds
                    clickable = False
                elif score > 0:
                    bg = HEAT_COLORS[score]
                    tooltip = f"{ds}: {score * 25}%"
                    clickable = True
                else:
                    bg = ft.Colors.SURFACE_CONTAINER_HIGHEST
                    tooltip = f"{ds}: 0%"
                    clickable = True

                cell = ft.Container(
                    width=HEAT_CELL,
                    height=HEAT_CELL,
                    border_radius=3,
                    bgcolor=bg,
                    data=ds,
                    on_click=self._on_heatmap_click if clickable else None,
                    tooltip=tooltip,
                )
                self._heatmap_cells[ds] = cell
                day_cells.append(cell)

            col = ft.Column(spacing=HEAT_GAP, controls=day_cells)
            columns.append(col)
            col_idx += 1
            week_start += timedelta(days=7)

        # 月份标签：基于每月占据的列范围，居中放置
        total_cols = len(columns)
        month_labels: list[ft.Control] = [ft.Container(width=HEAT_CELL)] * total_cols
        for m, (first_col, last_col) in month_col_ranges.items():
            center_col = (first_col + last_col) // 2
            if 0 <= center_col < total_cols:
                month_labels[center_col] = ft.Container(
                    width=HEAT_CELL,
                    content=ft.Text(
                        t("stats.heatmap_month", m),
                        size=9,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                )

        month_row = ft.Row(spacing=HEAT_GAP, controls=month_labels)

        # 星期标签列
        label_col = ft.Column(
            spacing=HEAT_GAP,
            controls=[
                ft.Container(
                    width=20,
                    height=HEAT_CELL,
                    alignment=ft.Alignment(1, 0),
                    content=ft.Text(lb, size=9, color=ft.Colors.ON_SURFACE_VARIANT),
                )
                for lb in weekday_labels
            ],
        )

        # 可滚动的网格区域
        grid_scroll = ft.Row(
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[label_col, ft.Container(width=4), ft.Row(spacing=HEAT_GAP, controls=columns, scroll=ft.ScrollMode.AUTO)],
        )

        # 年份导航
        year_nav = ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_size=18, on_click=self._on_year_prev),
                ft.Text(f"{year}", size=16, weight=ft.FontWeight.W_600),
                ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_size=18, on_click=self._on_year_next),
                ft.Container(expand=True),
                ft.Text(t("stats.heatmap_title"), size=14, weight=ft.FontWeight.W_500, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
        )

        # 今日评估区域
        today_str = today.isoformat()
        current = self._assessment_repo.get(today_str) if self._assessment_repo else None
        current_score = current["score"] if current else 0
        is_manual = current and current.get("manual") == 1

        score_labels = [
            (0, t("stats.assess_0")),
            (1, t("stats.assess_1")),
            (2, t("stats.assess_2")),
            (3, t("stats.assess_3")),
            (4, t("stats.assess_4")),
        ]

        self._today_assess_chips.controls = [
            ft.Chip(
                label=ft.Text(label, size=12),
                data=score_val,
                selected=(score_val == current_score),
                on_click=self._on_today_assess,
            )
            for score_val, label in score_labels
        ]

        hint_text = t("stats.assess_today_done") if is_manual else t("stats.assess_today_hint")

        today_section = ft.Column(
            spacing=6,
            controls=[
                ft.Divider(),
                ft.Row(
                    controls=[
                        ft.Text(t("stats.assess_today_title"), size=14, weight=ft.FontWeight.W_500),
                        ft.Container(expand=True),
                        ft.Text(hint_text, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                ),
                self._today_assess_chips,
            ],
        )

        # 组装整个卡片
        self._heatmap_container.content = ft.Column(
            spacing=8,
            controls=[
                year_nav,
                month_row,
                grid_scroll,
                today_section,
            ],
        )

    def _on_year_prev(self, e):
        self._heatmap_year -= 1
        self._build_heatmap(datetime.now().date())
        self.update()

    def _on_year_next(self, e):
        self._heatmap_year += 1
        self._build_heatmap(datetime.now().date())
        self.update()

    def _on_today_assess(self, e):
        score_val = e.control.data
        today_str = datetime.now().date().isoformat()
        if not self._assessment_repo:
            return
        self._assessment_repo.upsert(today_str, score_val, 1)
        self._build_heatmap(datetime.now().date())
        self.page.update()

    def _on_heatmap_click(self, e):
        """点击历史日期方块，弹出判定对话框。"""
        date_str = e.control.data
        if not date_str or not self._assessment_repo:
            return
        current = self._assessment_repo.get(date_str)
        current_score = current["score"] if current else 0
        self._show_assess_dialog(date_str, current_score)

    def _show_assess_dialog(self, date_str: str, current_score: int):
        """弹出历史日期完成度判定对话框。"""
        score_labels = [
            (0, t("stats.assess_0")),
            (1, t("stats.assess_1")),
            (2, t("stats.assess_2")),
            (3, t("stats.assess_3")),
            (4, t("stats.assess_4")),
        ]
        selected_score = {"value": current_score}

        def on_select(e):
            selected_score["value"] = e.control.data
            for chip in chip_row.controls:
                chip.selected = chip.data == selected_score["value"]
            dialog.update()

        chip_row = ft.Row(
            spacing=8,
            wrap=True,
            controls=[
                ft.Chip(
                    label=ft.Text(label, size=12),
                    data=score,
                    selected=(score == current_score),
                    on_click=on_select,
                )
                for score, label in score_labels
            ],
        )

        def on_confirm(e):
            self._assessment_repo.upsert(date_str, selected_score["value"], 1)
            self.page.pop_dialog()
            # 重建热力图以反映变更
            self._build_heatmap(datetime.now().date())
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(t("stats.assess_title", date_str)),
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Text(t("stats.assess_hint"), size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                    chip_row,
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton(t("dialog.cancel"), on_click=lambda e: self.page.pop_dialog()),
                ft.FilledButton(t("picker.confirm"), on_click=on_confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

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

        # 热力图 + 今日评估
        self._heatmap_container.opacity = 1
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
        self._schedule_midnight_refresh()

    def _schedule_midnight_refresh(self):
        """每天 0 点自动刷新，进入下一天评估。"""
        async def _wait_and_refresh():
            while True:
                now = datetime.now()
                tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                seconds = (tomorrow - now).total_seconds()
                await asyncio.sleep(seconds)
                self._heatmap_year = datetime.now().year
                self.refresh_data()
        if not hasattr(self, '_midnight_task') or self._midnight_task.done():
            self._midnight_task = asyncio.ensure_future(_wait_and_refresh())
