from __future__ import annotations

import asyncio

import flet as ft

from services.llm_config_manager import LLMConfigManager
from storage.setting_repo import SettingRepo
from ui.i18n import t
from ui.theme import AppColors


class OnboardingView(ft.Column):
    """Onboarding 引导流程组件 — 7 步教程"""

    TOTAL_STEPS = 7

    def __init__(self, on_complete: callable, llm_cfg: LLMConfigManager | None = None,
                 is_revisit: bool = False):
        super().__init__()
        self._on_complete = on_complete
        self._llm_cfg = llm_cfg
        self._repo = SettingRepo()
        self._current_step = 0
        self._is_revisit = is_revisit
        self._api_key_input = None
        self._test_result = None
        self._save_result = None
        self._test_btn_ref = ft.Ref[ft.Button]()
        self.expand = True
        self.spacing = 0
        self._build()

    async def _close_window(self, e):
        await e.page.window.close()

    def _build(self):
        title_bar = ft.WindowDragArea(
            content=ft.Container(
                bgcolor=ft.Colors.SURFACE,
                padding=ft.Padding(12, 6, 6, 6),
                content=ft.Row(
                    controls=[
                        ft.Text("Cleaner", size=14, weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.REMOVE_ROUNDED,
                            icon_size=18,
                            on_click=lambda e: setattr(e.page.window, "minimized", True),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CROP_SQUARE_ROUNDED,
                            icon_size=18,
                            on_click=lambda e: setattr(e.page.window, "maximized", not e.page.window.maximized),
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

        self._content = ft.ListView(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding(20, 20, 20, 20),
                    content=ft.Container(
                        padding=ft.Padding(48, 36, 48, 36),
                        border_radius=16,
                        bgcolor=AppColors.PANEL_BG,
                        content=self._build_step(0),
                    ),
                ),
            ],
        )

        self.controls = [title_bar, self._content]

    # ── 步骤路由 ─────────────────────────────────────────

    def _build_step(self, step: int) -> ft.Control:
        builders = [
            self._build_welcome,
            self._build_features,
            self._build_ai_tutorial,
            self._build_tasks_tutorial,
            self._build_views_tutorial,
            self._build_api_setup,
            self._build_done,
        ]
        if 0 <= step < len(builders):
            return builders[step]()
        return self._build_welcome()

    # ── Step 0: 欢迎 ────────────────────────────────────

    def _build_welcome(self):
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=96,
                    height=96,
                    border_radius=24,
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.CHECK_CIRCLE, size=48, color=ft.Colors.PRIMARY),
                ),
                ft.Container(height=28),
                ft.Text(t("onboarding.welcome_title"), size=32, weight=ft.FontWeight.BOLD),
                ft.Container(height=12),
                ft.Text(
                    t("onboarding.welcome_desc"),
                    size=16,
                    color=AppColors.TEXT_HINT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=40),
                self._build_dots(),
                ft.Container(height=28),
                ft.Button(
                    text=t("onboarding.btn_next"),
                    on_click=self._next,
                    width=220,
                    height=50,
                ),
                ft.Container(height=8),
                ft.TextButton(
                    t("onboarding.btn_skip"),
                    on_click=self._complete,
                ),
            ],
        )

    # ── Step 1: 功能概览 ────────────────────────────────

    def _build_features(self):
        features = [
            (ft.Icons.SMART_TOY_OUTLINED, t("onboarding.feature_ai_title"), t("onboarding.feature_ai_desc"), ft.Colors.PRIMARY_CONTAINER),
            (ft.Icons.CALENDAR_MONTH_OUTLINED, t("onboarding.feature_calendar_title"), t("onboarding.feature_calendar_desc"), ft.Colors.TERTIARY_CONTAINER),
            (ft.Icons.BAR_CHART_OUTLINED, t("onboarding.feature_stats_title"), t("onboarding.feature_stats_desc"), ft.Colors.SECONDARY_CONTAINER),
            (ft.Icons.REPEAT, t("onboarding.feature_repeat_title"), t("onboarding.feature_repeat_desc"), ft.Colors.PRIMARY_CONTAINER),
        ]

        cards = []
        for icon, title, desc, bg in features:
            cards.append(
                ft.Container(
                    padding=ft.Padding(16, 14, 16, 14),
                    border_radius=12,
                    bgcolor=bg,
                    content=ft.Row(
                        spacing=16,
                        controls=[
                            ft.Icon(icon, size=28, color=ft.Colors.PRIMARY),
                            ft.Column(
                                spacing=4,
                                expand=True,
                                controls=[
                                    ft.Text(title, size=15, weight=ft.FontWeight.W_600),
                                    ft.Text(desc, size=13, color=AppColors.TEXT_HINT),
                                ],
                            ),
                        ],
                    ),
                )
            )

        # 2x2 网格
        grid = ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Container(expand=True, content=cards[0]),
                        ft.Container(expand=True, content=cards[1]),
                    ],
                ),
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Container(expand=True, content=cards[2]),
                        ft.Container(expand=True, content=cards[3]),
                    ],
                ),
            ],
        )

        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(t("onboarding.step_features"), size=26, weight=ft.FontWeight.BOLD),
                ft.Container(height=24),
                ft.Container(width=580, content=grid),
                ft.Container(height=24),
                self._build_dots(),
                ft.Container(height=28),
                self._build_nav_row(),
            ],
        )

    # ── Step 2: AI 助手教程 ─────────────────────────────

    def _build_ai_tutorial(self):
        examples = [
            (t("onboarding.ai_ex_add"), True, t("onboarding.ai_ex_add_resp")),
            (t("onboarding.ai_ex_query"), True, t("onboarding.ai_ex_query_resp")),
            (t("onboarding.ai_ex_plan"), True, t("onboarding.ai_ex_plan_resp")),
        ]
        chat_rows = []
        for user_msg, _, ai_resp in examples:
            chat_rows.append(self._chat_bubble(user_msg, is_user=True))
            chat_rows.append(self._chat_bubble(ai_resp, is_user=False))

        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=48,
                    height=48,
                    border_radius=14,
                    bgcolor=ft.Colors.TERTIARY_CONTAINER,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=24, color=ft.Colors.TERTIARY),
                ),
                ft.Container(height=16),
                ft.Text(t("onboarding.ai_tutorial"), size=26, weight=ft.FontWeight.BOLD),
                ft.Container(height=12),
                ft.Text(
                    t("onboarding.ai_intro"),
                    size=14,
                    color=AppColors.TEXT_HINT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=20),
                ft.Container(
                    width=440,
                    padding=ft.Padding(20, 16, 20, 16),
                    border_radius=12,
                    bgcolor=ft.Colors.SURFACE,
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.OUTLINE)),
                    content=ft.Column(
                        spacing=10,
                        controls=chat_rows,
                    ),
                ),
                ft.Container(height=12),
                ft.Container(
                    padding=ft.Padding(12, 8, 12, 8),
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.PRIMARY),
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=16, color=ft.Colors.PRIMARY),
                            ft.Text(t("onboarding.ai_tip"), size=13, color=AppColors.TEXT_HINT),
                        ],
                    ),
                ),
                ft.Container(height=24),
                self._build_dots(),
                ft.Container(height=28),
                self._build_nav_row(),
            ],
        )

    def _chat_bubble(self, text: str, is_user: bool) -> ft.Row:
        bubble = ft.Container(
            padding=ft.Padding(14, 10, 14, 10),
            border_radius=ft.BorderRadius(14, 14, 4, 14) if is_user else ft.BorderRadius(14, 14, 14, 4),
            bgcolor=ft.Colors.PRIMARY_CONTAINER if is_user else ft.Colors.SECONDARY_CONTAINER,
            content=ft.Text(text, size=13, selectable=True),
            # 限制最大宽度
        )
        return ft.Row(
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
            controls=[ft.Container(width=320, content=bubble)],
        )

    # ── Step 3: 任务管理教程 ─────────────────────────────

    def _build_tasks_tutorial(self):
        items = [
            (ft.Icons.ADD_CIRCLE_OUTLINE, t("onboarding.tasks_add"), t("onboarding.tasks_add_desc"), ft.Colors.PRIMARY_CONTAINER),
            (ft.Icons.EDIT_OUTLINED, t("onboarding.tasks_edit"), t("onboarding.tasks_edit_desc"), ft.Colors.TERTIARY_CONTAINER),
            (ft.Icons.CHECK_CIRCLE_OUTLINE, t("onboarding.tasks_complete"), t("onboarding.tasks_complete_desc"), ft.Colors.SECONDARY_CONTAINER),
            (ft.Icons.DRAG_INDICATOR, t("onboarding.tasks_drag"), t("onboarding.tasks_drag_desc"), ft.Colors.PRIMARY_CONTAINER),
            (ft.Icons.FILTER_LIST, t("onboarding.tasks_filter"), t("onboarding.tasks_filter_desc"), ft.Colors.TERTIARY_CONTAINER),
            (ft.Icons.KEYBOARD_OUTLINED, t("onboarding.tasks_shortcuts"), t("onboarding.tasks_shortcuts_desc"), ft.Colors.SECONDARY_CONTAINER),
        ]

        cards = []
        for icon, title, desc, bg in items:
            cards.append(
                ft.Container(
                    padding=ft.Padding(14, 12, 14, 12),
                    border_radius=10,
                    bgcolor=bg,
                    content=ft.Row(
                        spacing=14,
                        controls=[
                            ft.Container(
                                width=36,
                                height=36,
                                border_radius=10,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(icon, size=20, color=ft.Colors.PRIMARY),
                            ),
                            ft.Column(
                                spacing=3,
                                expand=True,
                                controls=[
                                    ft.Text(title, size=14, weight=ft.FontWeight.W_600),
                                    ft.Text(desc, size=12, color=AppColors.TEXT_HINT),
                                ],
                            ),
                        ],
                    ),
                )
            )

        # 两列网格
        rows = []
        for i in range(0, len(cards), 2):
            row_cards = [ft.Container(expand=True, content=cards[i])]
            if i + 1 < len(cards):
                row_cards.append(ft.Container(expand=True, content=cards[i + 1]))
            rows.append(ft.Row(spacing=10, controls=row_cards))

        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=48,
                    height=48,
                    border_radius=14,
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.TASK_ALT, size=24, color=ft.Colors.PRIMARY),
                ),
                ft.Container(height=16),
                ft.Text(t("onboarding.tasks_tutorial"), size=26, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                ft.Container(width=580, content=ft.Column(spacing=8, controls=rows)),
                ft.Container(height=24),
                self._build_dots(),
                ft.Container(height=28),
                self._build_nav_row(),
            ],
        )

    # ── Step 4: 视图与通知教程 ───────────────────────────

    def _build_views_tutorial(self):
        items = [
            (ft.Icons.CALENDAR_MONTH_OUTLINED, t("onboarding.views_calendar"), t("onboarding.views_calendar_desc"), ft.Colors.TERTIARY_CONTAINER),
            (ft.Icons.INSERT_CHART_OUTLINED, t("onboarding.views_stats"), t("onboarding.views_stats_desc"), ft.Colors.SECONDARY_CONTAINER),
            (ft.Icons.NOTIFICATIONS_OUTLINED, t("onboarding.views_notif"), t("onboarding.views_notif_desc"), ft.Colors.PRIMARY_CONTAINER),
            (ft.Icons.REPEAT, t("onboarding.views_recurring"), t("onboarding.views_recurring_desc"), ft.Colors.TERTIARY_CONTAINER),
        ]

        cards = []
        for icon, title, desc, bg in items:
            cards.append(
                ft.Container(
                    padding=ft.Padding(18, 16, 18, 16),
                    border_radius=12,
                    bgcolor=bg,
                    content=ft.Row(
                        spacing=16,
                        controls=[
                            ft.Container(
                                width=44,
                                height=44,
                                border_radius=12,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(icon, size=24, color=ft.Colors.PRIMARY),
                            ),
                            ft.Column(
                                spacing=4,
                                expand=True,
                                controls=[
                                    ft.Text(title, size=15, weight=ft.FontWeight.W_600),
                                    ft.Text(desc, size=13, color=AppColors.TEXT_HINT),
                                ],
                            ),
                        ],
                    ),
                )
            )

        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=48,
                    height=48,
                    border_radius=14,
                    bgcolor=ft.Colors.SECONDARY_CONTAINER,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.DASHBOARD_OUTLINED, size=24, color=ft.Colors.SECONDARY),
                ),
                ft.Container(height=16),
                ft.Text(t("onboarding.views_tutorial"), size=26, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                ft.Container(width=520, content=ft.Column(spacing=10, controls=cards)),
                ft.Container(height=24),
                self._build_dots(),
                ft.Container(height=28),
                self._build_nav_row(),
            ],
        )

    # ── Step 5: API 设置 ─────────────────────────────────

    def _build_api_setup(self):
        self._api_key_input = ft.TextField(
            label=t("onboarding.api_key_label"),
            hint_text=t("onboarding.api_key_hint"),
            password=True,
            can_reveal_password=True,
            expand=True,
            on_submit=self._save_api_key,
        )

        self._test_result = ft.Text("", size=13, color=ft.Colors.GREEN)
        self._save_result = ft.Text("", size=13, color=ft.Colors.GREEN)

        api_container = ft.Container(
            width=450,
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Text(
                        t("onboarding.api_desc"),
                        size=15,
                        color=AppColors.TEXT_HINT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=24),
                    self._api_key_input,
                    ft.Container(height=14),
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Button(
                                text=t("onboarding.api_test"),
                                on_click=self._test_api,
                                height=42,
                                ref=self._test_btn_ref,
                            ),
                            ft.Button(
                                text=t("onboarding.api_save"),
                                on_click=self._save_api_key,
                                height=42,
                            ),
                            self._test_result,
                        ],
                    ),
                    ft.Container(height=8),
                    self._save_result,
                ],
            ),
        )

        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=48,
                    height=48,
                    border_radius=14,
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.KEY, size=24, color=ft.Colors.PRIMARY),
                ),
                ft.Container(height=16),
                ft.Text(t("onboarding.step_api"), size=26, weight=ft.FontWeight.BOLD),
                ft.Text(
                    t("onboarding.api_skip_hint"),
                    size=13,
                    color=AppColors.TEXT_HINT,
                ),
                ft.Container(height=20),
                api_container,
                ft.Container(height=20),
                self._build_dots(),
                ft.Container(height=28),
                self._build_nav_row(),
            ],
        )

    # ── Step 6: 完成 ─────────────────────────────────────

    def _build_done(self):
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=96,
                    height=96,
                    border_radius=24,
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.CHECK_CIRCLE, size=48, color=ft.Colors.PRIMARY),
                ),
                ft.Container(height=28),
                ft.Text(t("onboarding.done_title"), size=32, weight=ft.FontWeight.BOLD),
                ft.Container(height=12),
                ft.Text(
                    t("onboarding.done_desc"),
                    size=16,
                    color=AppColors.TEXT_HINT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=8),
                ft.Text(
                    t("onboarding.done_hint"),
                    size=14,
                    color=AppColors.TEXT_HINT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=40),
                self._build_dots(),
                ft.Container(height=28),
                ft.Button(
                    text=t("onboarding.btn_start"),
                    on_click=self._complete,
                    width=220,
                    height=50,
                ),
            ],
        )

    # ── 通用组件 ─────────────────────────────────────────

    def _build_dots(self):
        dots = []
        for i in range(self.TOTAL_STEPS):
            is_active = i == self._current_step
            is_done = i < self._current_step
            dots.append(
                ft.Container(
                    width=10 if is_active else 8,
                    height=10 if is_active else 8,
                    border_radius=5 if is_active else 4,
                    bgcolor=ft.Colors.PRIMARY if is_active else (
                        ft.Colors.with_opacity(0.4, ft.Colors.PRIMARY) if is_done else AppColors.TEXT_HINT
                    ),
                )
            )
        return ft.Row(
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                *dots,
                ft.Container(width=16),
                ft.Text(
                    t("onboarding.dots_hint", self._current_step + 1, self.TOTAL_STEPS),
                    size=13,
                    color=AppColors.TEXT_HINT,
                ),
            ],
        )

    def _build_nav_row(self):
        controls = []
        if self._current_step > 0:
            controls.append(
                ft.OutlinedButton(
                    text=t("onboarding.btn_prev"),
                    on_click=self._prev,
                    width=130,
                    height=46,
                )
            )
        if self._current_step < self.TOTAL_STEPS - 1:
            controls.append(
                ft.Button(
                    text=t("onboarding.btn_next"),
                    on_click=self._next,
                    width=130,
                    height=46,
                )
            )
        return ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
            controls=controls,
        )

    # ── 导航 ─────────────────────────────────────────────

    def _go_to_step(self, step: int):
        self._current_step = step
        if self._content.controls:
            self._content.controls[0].content.content = self._build_step(step)
        self.update()

    def _next(self, e=None):
        self._go_to_step(self._current_step + 1)

    def _prev(self, e=None):
        self._go_to_step(self._current_step - 1)

    # ── API 操作 ─────────────────────────────────────────

    def _save_api_key(self, e=None):
        key = (self._api_key_input.value or "").strip()
        if key:
            self._repo.set("llm_api_key", key)
            if self._llm_cfg:
                self._llm_cfg.load(self._repo)
            self._save_result.value = t("onboarding.save_success")
            self._save_result.color = ft.Colors.GREEN
        else:
            self._save_result.value = t("onboarding.save_empty")
            self._save_result.color = ft.Colors.ORANGE
        self.update()

    def _complete(self, e=None):
        self._repo.set("onboarding_completed", "1")
        self._on_complete()

    async def _test_api(self, e=None):
        if not self._llm_cfg:
            self._test_result.value = t("settings.assistant.not_loaded")
            self._test_result.color = ft.Colors.ORANGE
            self.update()
            return

        key = (self._api_key_input.value or "").strip()
        if not key:
            self._test_result.value = t("test.no_key")
            self._test_result.color = ft.Colors.ORANGE
            self.update()
            return

        if self._test_btn_ref.current:
            self._test_btn_ref.current.disabled = True
            self._test_btn_ref.current.content = ft.Row(
                controls=[
                    ft.ProgressRing(width=16, height=16, stroke_width=2),
                    ft.Text("测试中..."),
                ],
                spacing=8,
            )
        self._test_result.value = ""
        self.update()

        if self._llm_cfg:
            self._llm_cfg.api_key = key
            self._llm_cfg.base_url = self._repo.get("llm_base_url") or ""
            self._llm_cfg.model = self._repo.get("llm_model") or ""

        try:
            success, msg = await asyncio.to_thread(self._llm_cfg.test_connection)
            if success:
                self._test_result.value = "连接成功"
                self._test_result.color = ft.Colors.GREEN
            else:
                self._test_result.value = msg
                self._test_result.color = ft.Colors.RED
        except Exception as ex:
            self._test_result.value = t("test.fail", str(ex))
            self._test_result.color = ft.Colors.RED
        finally:
            if self._test_btn_ref.current:
                self._test_btn_ref.current.disabled = False
                self._test_btn_ref.current.content = ft.Text(t("onboarding.api_test"))
        self.update()
