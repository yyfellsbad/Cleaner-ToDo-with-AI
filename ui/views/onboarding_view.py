from __future__ import annotations

import flet as ft

from services.llm_config_manager import LLMConfigManager
from storage.setting_repo import SettingRepo
from ui.i18n import t
from ui.theme import AppColors


class OnboardingView(ft.Column):
    """Onboarding 引导流程组件"""

    TOTAL_STEPS = 4

    def __init__(self, on_complete: callable, llm_cfg: LLMConfigManager | None = None):
        super().__init__()
        self._on_complete = on_complete
        self._llm_cfg = llm_cfg
        self._repo = SettingRepo()
        self._current_step = 0
        self._api_key_input = None
        self._test_result = None
        self._save_result = None
        self._test_btn_ref = ft.Ref[ft.ElevatedButton]()
        self.expand = True
        self.spacing = 0
        self._build()

    async def _close_window(self, e):
        await e.page.window.close()

    def _build(self):
        # 自定义标题栏
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

        # 内容区 - 可伸缩，限制最大宽度，支持滚动
        self._content = ft.ListView(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding(20, 20, 20, 20),
                    content=ft.Container(
                        padding=ft.Padding(48, 40, 48, 40),
                        border_radius=16,
                        bgcolor=AppColors.PANEL_BG,
                        content=self._build_step(0),
                    ),
                ),
            ],
        )

        self.controls = [title_bar, self._content]

    def _build_step(self, step: int) -> ft.Control:
        if step == 0:
            return self._build_welcome()
        elif step == 1:
            return self._build_features()
        elif step == 2:
            return self._build_api_setup()
        elif step == 3:
            return self._build_done()
        return self._build_welcome()

    def _build_welcome(self):
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=72, color=ft.Colors.PRIMARY),
                ft.Container(height=28),
                ft.Text(t("onboarding.welcome_title"), size=32, weight=ft.FontWeight.BOLD),
                ft.Container(height=16),
                ft.Text(
                    t("onboarding.welcome_desc"),
                    size=16,
                    color=AppColors.TEXT_HINT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=40),
                self._build_dots(),
                ft.Container(height=32),
                ft.ElevatedButton(
                    t("onboarding.btn_next"),
                    on_click=self._next,
                    width=220,
                    height=50,
                ),
            ],
        )

    def _build_features(self):
        features = [
            (ft.Icons.SMART_TOY, t("onboarding.feature_ai_title"), t("onboarding.feature_ai_desc")),
            (ft.Icons.CALENDAR_MONTH, t("onboarding.feature_calendar_title"), t("onboarding.feature_calendar_desc")),
            (ft.Icons.BAR_CHART, t("onboarding.feature_stats_title"), t("onboarding.feature_stats_desc")),
            (ft.Icons.REPEAT, t("onboarding.feature_repeat_title"), t("onboarding.feature_repeat_desc")),
        ]

        feature_cards = []
        for icon, title, desc in features:
            feature_cards.append(
                ft.Container(
                    padding=ft.Padding(0, 14, 0, 14),
                    content=ft.Row(
                        spacing=20,
                        controls=[
                            ft.Container(
                                width=52,
                                height=52,
                                border_radius=14,
                                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(icon, size=26, color=ft.Colors.PRIMARY),
                            ),
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(title, size=17, weight=ft.FontWeight.W_600),
                                    ft.Text(desc, size=14, color=AppColors.TEXT_HINT),
                                ],
                            ),
                        ],
                    ),
                )
            )

        # 功能卡片区域 - 限制最大宽度
        cards_container = ft.Container(
            width=550,
            padding=ft.Padding(24, 0, 24, 0),
            content=ft.Column(
                spacing=0,
                controls=feature_cards,
            ),
        )

        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(t("onboarding.step_features"), size=26, weight=ft.FontWeight.BOLD),
                ft.Container(height=28),
                cards_container,
                ft.Container(height=20),
                self._build_dots(),
                ft.Container(height=28),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=16,
                    controls=[
                        ft.OutlinedButton(
                            t("onboarding.btn_prev"),
                            on_click=self._prev,
                            width=130,
                            height=46,
                        ),
                        ft.ElevatedButton(
                            t("onboarding.btn_next"),
                            on_click=self._next,
                            width=130,
                            height=46,
                        ),
                    ],
                ),
            ],
        )

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

        # API配置区域 - 限制最大宽度
        api_container = ft.Container(
            width=450,
            padding=ft.Padding(0, 0, 0, 0),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Text(
                        t("onboarding.api_desc"),
                        size=15,
                        color=AppColors.TEXT_HINT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=28),
                    self._api_key_input,
                    ft.Container(height=14),
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.ElevatedButton(
                                t("onboarding.api_test"),
                                on_click=self._test_api,
                                height=42,
                                ref=self._test_btn_ref,
                            ),
                            ft.ElevatedButton(
                                t("onboarding.api_save"),
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
                ft.Text(t("onboarding.step_api"), size=26, weight=ft.FontWeight.BOLD),
                ft.Text(
                    t("onboarding.api_skip_hint"),
                    size=13,
                    color=AppColors.TEXT_HINT,
                ),
                ft.Container(height=24),
                api_container,
                ft.Container(height=20),
                self._build_dots(),
                ft.Container(height=28),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=16,
                    controls=[
                        ft.OutlinedButton(
                            t("onboarding.btn_prev"),
                            on_click=self._prev,
                            width=130,
                            height=46,
                        ),
                        ft.ElevatedButton(
                            t("onboarding.btn_next"),
                            on_click=self._next,
                            width=130,
                            height=46,
                        ),
                    ],
                ),
            ],
        )

    def _build_done(self):
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=72, color=ft.Colors.PRIMARY),
                ft.Container(height=28),
                ft.Text(t("onboarding.done_title"), size=32, weight=ft.FontWeight.BOLD),
                ft.Container(height=16),
                ft.Text(
                    t("onboarding.done_desc"),
                    size=16,
                    color=AppColors.TEXT_HINT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=10),
                ft.Text(
                    t("onboarding.done_hint"),
                    size=14,
                    color=AppColors.TEXT_HINT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=40),
                self._build_dots(),
                ft.Container(height=32),
                ft.ElevatedButton(
                    t("onboarding.btn_start"),
                    on_click=self._complete,
                    width=220,
                    height=50,
                ),
            ],
        )

    def _build_dots(self):
        dots = []
        for i in range(self.TOTAL_STEPS):
            is_active = i == self._current_step
            dots.append(
                ft.Container(
                    width=10 if is_active else 8,
                    height=10 if is_active else 8,
                    border_radius=5 if is_active else 4,
                    bgcolor=ft.Colors.PRIMARY if is_active else AppColors.TEXT_HINT,
                )
            )
        return ft.Row(
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                *dots,
                ft.Container(width=20),
                ft.Text(
                    t("onboarding.dots_hint", self._current_step + 1, self.TOTAL_STEPS),
                    size=13,
                    color=AppColors.TEXT_HINT,
                ),
            ],
        )

    def _go_to_step(self, step: int):
        self._current_step = step
        # 更新 ListView 中的内容容器
        if self._content.controls:
            self._content.controls[0].content.content = self._build_step(step)
        self.update()

    def _next(self, e=None):
        self._go_to_step(self._current_step + 1)

    def _prev(self, e=None):
        self._go_to_step(self._current_step - 1)

    def _save_api_key(self, e=None):
        key = self._api_key_input.value.strip()
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

        key = self._api_key_input.value.strip()
        if not key:
            self._test_result.value = t("test.no_key")
            self._test_result.color = ft.Colors.ORANGE
            self.update()
            return

        # 禁用按钮并显示加载状态
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

        # 测试连接时只临时设置，不保存到数据库
        # 用户点击"保存"按钮时才会持久化
        if self._llm_cfg:
            self._llm_cfg.api_key = key
            self._llm_cfg.base_url = self._repo.get("llm_base_url") or ""
            self._llm_cfg.model = self._repo.get("llm_model") or ""

        try:
            import asyncio
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
            # 恢复按钮状态
            if self._test_btn_ref.current:
                self._test_btn_ref.current.disabled = False
                self._test_btn_ref.current.content = ft.Text(t("onboarding.api_test"))
        self.update()
