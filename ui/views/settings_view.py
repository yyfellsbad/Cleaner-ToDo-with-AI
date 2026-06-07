from __future__ import annotations

import asyncio

import flet as ft

from ui.i18n import t
from ui.theme import AppColors, THEME_SEEDS, THEME_SEED_LABELS, ThemeManager


PERSONA_PRESETS: dict[str, str] = {
    "阿喵": "你是一只可爱的猫娘助手「阿喵」，说话带喵~语气，活泼可爱，用中文回答。如果用户问到待办操作，用可爱的语气提醒他们。",
    "阿汪": "你是一只忠诚的柴犬助手「阿汪」，热情友好，偶尔用汪~语气，用中文回答。如果用户问到待办操作，用积极的语气鼓励他们。",
    "砖家": "你是一位严谨的学术专家「砖家」，说话条理清晰、逻辑严密，喜欢引用数据和理论，用中文回答。如果用户问到待办操作，用专业的角度给出建议。",
    "小冰": "你是温柔体贴的助手「小冰」，善解人意，语气温和，会关心用户的情绪，用中文回答。如果用户问到待办操作，用关怀的语气提醒。",
    "默认": "你是一个简洁友好的中文助手。可以正常聊天；如果用户问到待办操作，也可以先解释再建议他用任务指令。",
}


class SettingsView(ft.Column):
    def __init__(self, theme_manager: ThemeManager, config_manager=None,
                 on_lang_change=None, notification_service=None, on_close=None):
        super().__init__()
        self.tm = theme_manager
        self._cfg = config_manager
        self._notif = notification_service
        self._on_lang_change_cb = on_lang_change
        self._on_close = on_close
        self.expand = True
        self.spacing = 0
        self._current_section = "appearance"
        self._build()

    def _build(self):
        # ── 顶部导航栏 ──
        def _on_close_click(e):
            if self._on_close:
                self._on_close(e)

        top_bar = ft.Container(
            padding=ft.Padding(16, 12, 16, 8),
            content=ft.Row(
                controls=[
                    ft.Text(
                        t("settings.title"),
                        size=16,
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=22,
                        tooltip=t("task.close"),
                        on_click=_on_close_click,
                    ),
                ],
            ),
        )

        # ── 左侧导航 ──
        self._nav_items = {
            "appearance": (t("nav.appearance"), ft.Icons.PALETTE_OUTLINED),
            "language": (t("nav.language"), ft.Icons.LANGUAGE),
            "assistant": (t("nav.assistant"), ft.Icons.SMART_TOY_OUTLINED),
            "notifications": (t("nav.notifications"), ft.Icons.NOTIFICATIONS_OUTLINED),
            "tutorial": (t("nav.tutorial"), ft.Icons.SCHOOL_OUTLINED),
        }

        nav_controls = []
        for key, (label, icon) in self._nav_items.items():
            is_selected = key == self._current_section
            nav_controls.append(
                ft.Container(
                    data=key,
                    border_radius=8,
                    padding=ft.Padding(12, 10, 12, 10),
                    bgcolor=AppColors.PANEL_BG if is_selected else None,
                    on_click=self._on_nav_click,
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(
                                icon,
                                size=20,
                                color=ft.Colors.PRIMARY if is_selected else AppColors.TEXT_HINT,
                            ),
                            ft.Text(
                                label,
                                size=14,
                                weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_400,
                                color=ft.Colors.PRIMARY if is_selected else None,
                            ),
                        ],
                    ),
                )
            )

        self._nav_column = ft.Container(
            width=150,
            padding=ft.Padding(12, 16, 12, 16),
            content=ft.Column(
                spacing=4,
                controls=nav_controls,
            ),
        )

        # ── 右侧内容区 ──
        self._content_area = ft.Container(
            expand=True,
            padding=ft.Padding(8, 16, 8, 16),
            content=self._build_section(self._current_section),
        )

        self.controls = [
            top_bar,
            ft.Row(
                expand=True,
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    self._nav_column,
                    ft.VerticalDivider(width=1),
                    self._content_area,
                ],
            ),
        ]

    def _build_section(self, section: str) -> ft.Control:
        if section == "appearance":
            return self._build_appearance()
        if section == "language":
            return self._build_language()
        if section == "assistant":
            return self._build_assistant()
        if section == "notifications":
            return self._build_notifications()
        if section == "tutorial":
            return self._build_tutorial()
        return ft.Container()

    def _build_appearance(self) -> ft.Control:
        mode_radios = ft.RadioGroup(
            value=self.tm.theme_mode,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Radio(value="light", label=t("settings.appearance.light")),
                    ft.Radio(value="dark", label=t("settings.appearance.dark")),
                    ft.Radio(value="system", label=t("settings.appearance.system")),
                ],
            ),
            on_change=self._on_mode_change,
        )

        seed_radios = ft.RadioGroup(
            value=self.tm.seed_name,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Radio(
                        value=name,
                        label=t(f"seed.{name}"),
                        active_color=seed,
                    )
                    for name, seed in THEME_SEEDS.items()
                ],
            ),
            on_change=self._on_seed_change,
        )

        return ft.Column(
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text(t("settings.appearance.title"), size=18, weight=ft.FontWeight.W_600),
                ft.Divider(),
                ft.Text(t("settings.appearance.mode"), weight=ft.FontWeight.W_500),
                mode_radios,
                ft.Divider(),
                ft.Text(t("settings.appearance.seed"), weight=ft.FontWeight.W_500),
                seed_radios,
                ft.Container(height=8),
                ft.Text(
                    t("settings.appearance.hint"),
                    size=12,
                    color=AppColors.TEXT_HINT,
                ),
            ],
        )

    def _build_language(self) -> ft.Control:
        current_lang = self.tm.language

        lang_radios = ft.RadioGroup(
            value=current_lang,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Radio(value="zh", label="中文"),
                    ft.Radio(value="en", label="English"),
                ],
            ),
            on_change=self._on_lang_change,
        )

        return ft.Column(
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text(t("settings.language.title"), size=18, weight=ft.FontWeight.W_600),
                ft.Divider(),
                ft.Text(t("settings.language.label"), weight=ft.FontWeight.W_500),
                lang_radios,
                ft.Container(height=8),
                ft.Text(
                    t("settings.language.hint"),
                    size=12,
                    color=AppColors.TEXT_HINT,
                ),
            ],
        )

    def _build_assistant(self) -> ft.Control:
        cfg = self._cfg
        if not cfg:
            return ft.Column(
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Text(t("settings.assistant.title"), size=18, weight=ft.FontWeight.W_600),
                    ft.Divider(),
                    ft.Text(t("settings.assistant.not_loaded"), color=AppColors.TEXT_HINT),
                ],
            )

        self._api_key_field = ft.TextField(
            label=t("settings.assistant.api_key"),
            value=cfg.api_key,
            password=True,
            can_reveal_password=True,
            dense=True,
            on_change=lambda e: cfg.set_api_key(e.control.value),
        )
        self._base_url_field = ft.TextField(
            label="Base URL",
            value=cfg.base_url,
            dense=True,
            on_change=lambda e: cfg.set_base_url(e.control.value),
        )
        self._model_field = ft.TextField(
            label=t("settings.assistant.model"),
            value=cfg.model,
            dense=True,
            on_change=lambda e: cfg.set_model(e.control.value),
        )
        self._chat_prompt_dirty = False
        self._chat_prompt_field = ft.TextField(
            label=t("settings.assistant.chat_prompt"),
            value=cfg.chat_prompt,
            multiline=True,
            min_lines=5,
            max_lines=12,
            dense=True,
            expand=True,
            on_change=self._on_prompt_change,
        )
        self._save_prompt_btn = ft.Button(
            t("settings.assistant.save_prompt"),
            icon=ft.Icons.CHECK_ROUNDED,
            visible=False,
            on_click=self._save_prompt,
        )

        test_btn = ft.Button(
            t("settings.assistant.test"),
            icon=ft.Icons.LINK_ROUNDED,
            on_click=self._test_connection,
        )

        # 预设性格 Chip 行
        preset_chips = ft.Row(
            wrap=True,
            spacing=8,
            controls=[
                ft.Chip(
                    label=ft.Text(name),
                    on_click=self._on_preset_select,
                    data=name,
                )
                for name in PERSONA_PRESETS
            ],
        )

        return ft.Column(
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text(t("settings.assistant.title"), size=18, weight=ft.FontWeight.W_600),
                ft.Divider(),
                ft.Text(t("settings.assistant.api_config"), weight=ft.FontWeight.W_500),
                self._api_key_field,
                self._base_url_field,
                self._model_field,
                ft.Container(height=4),
                test_btn,
                ft.Divider(),
                ft.Text(t("settings.assistant.persona"), weight=ft.FontWeight.W_500),
                ft.Text(t("settings.assistant.presets"), size=12, color=AppColors.TEXT_HINT),
                preset_chips,
                ft.Container(
                    width=700,
                    content=self._chat_prompt_field,
                ),
                self._save_prompt_btn,
                ft.Container(height=8),
                ft.Text(
                    t("settings.assistant.hint"),
                    size=12,
                    color=AppColors.TEXT_HINT,
                ),
            ],
        )

    def _build_notifications(self) -> ft.Control:
        notif = self._notif
        if not notif:
            return ft.Column(
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Text(t("settings.notifications.title"), size=18, weight=ft.FontWeight.W_600),
                    ft.Divider(),
                    ft.Text(t("settings.assistant.not_loaded"), color=AppColors.TEXT_HINT),
                ],
            )

        enable_switch = ft.Switch(
            label=t("settings.notifications.enabled"),
            value=notif.enabled,
            on_change=lambda e: setattr(notif, "enabled", e.control.value),
        )

        advance_dd = ft.Dropdown(
            label=t("settings.notifications.advance"),
            value=str(notif.advance_min),
            width=200,
            dense=True,
            options=[
                ft.dropdown.Option("5", "5 分钟"),
                ft.dropdown.Option("15", "15 分钟"),
                ft.dropdown.Option("30", "30 分钟"),
                ft.dropdown.Option("60", "1 小时"),
            ],
            on_select=lambda e: setattr(notif, "advance_min", int(e.control.value)),
        )

        dnd_switch = ft.Switch(
            label=t("settings.notifications.dnd_enabled"),
            value=notif.dnd_enabled,
            on_change=lambda e: setattr(notif, "dnd_enabled", e.control.value),
        )

        time_options = [
            ft.dropdown.Option(f"{h:02d}:{m:02d}")
            for h in range(24) for m in (0, 30)
        ]

        dnd_start_dd = ft.Dropdown(
            label=t("settings.notifications.dnd_start"),
            value=notif.dnd_start,
            width=120,
            dense=True,
            options=time_options,
            on_select=lambda e: setattr(notif, "dnd_start", e.control.value),
        )

        dnd_end_dd = ft.Dropdown(
            label=t("settings.notifications.dnd_end"),
            value=notif.dnd_end,
            width=120,
            dense=True,
            options=time_options,
            on_select=lambda e: setattr(notif, "dnd_end", e.control.value),
        )

        async def _test_notif(e):
            e.control.disabled = True
            self.update()
            ok = notif.send_test()
            e.control.disabled = False
            self.update()
            snack = ft.SnackBar(
                content=ft.Text(t("settings.notifications.test_ok") if ok else "Failed"),
                bgcolor=ft.Colors.GREEN_400 if ok else ft.Colors.RED_400,
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

        test_btn = ft.Button(
            t("settings.notifications.test"),
            icon=ft.Icons.NOTIFICATIONS_ACTIVE,
            on_click=_test_notif,
        )

        return ft.Column(
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text(t("settings.notifications.title"), size=18, weight=ft.FontWeight.W_600),
                ft.Divider(),
                enable_switch,
                ft.Row([advance_dd]),
                ft.Text(t("settings.notifications.advance_hint"), size=12, color=AppColors.TEXT_HINT),
                ft.Divider(),
                ft.Text(t("settings.notifications.dnd"), weight=ft.FontWeight.W_500),
                dnd_switch,
                ft.Row([dnd_start_dd, dnd_end_dd]),
                ft.Divider(),
                test_btn,
                ft.Container(height=8),
                ft.Text(t("settings.notifications.hint"), size=12, color=AppColors.TEXT_HINT),
            ],
        )

    def _on_preset_select(self, e):
        name = e.control.data
        prompt = PERSONA_PRESETS.get(name, "")
        if prompt:
            self._chat_prompt_field.value = prompt
            self._chat_prompt_dirty = True
            self._save_prompt_btn.visible = True
            self.update()

    def _on_prompt_change(self, e):
        self._chat_prompt_dirty = True
        self._save_prompt_btn.visible = True
        self.update()

    def _save_prompt(self, e):
        if not self._cfg:
            return
        self._cfg.set_chat_prompt(self._chat_prompt_field.value)
        self._chat_prompt_dirty = False
        self._save_prompt_btn.visible = False
        self.update()

    async def _test_connection(self, e):
        if not self._cfg:
            return
        e.control.disabled = True
        self.update()
        success, msg = await asyncio.to_thread(self._cfg.test_connection)
        e.control.disabled = False
        self.update()
        snack = ft.SnackBar(
            content=ft.Text(msg),
            bgcolor=ft.Colors.GREEN_400 if success else ft.Colors.RED_400,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _build_tutorial(self) -> ft.Control:
        return ft.Container(
            padding=ft.Padding(24, 20, 24, 20),
            content=ft.Column(
                spacing=20,
                controls=[
                    ft.Text(t("settings.tutorial.title"), size=22, weight=ft.FontWeight.BOLD),
                    ft.Text(t("settings.tutorial.desc"), size=14, color=AppColors.TEXT_HINT),
                    ft.Container(height=8),
                    ft.Button(
                        content=ft.Text(t("settings.tutorial.btn")),
                        icon=ft.Icons.SCHOOL_OUTLINED,
                        on_click=self._launch_tutorial,
                        width=200,
                        height=48,
                    ),
                ],
            ),
        )

    def _launch_tutorial(self, e):
        from ui.views.onboarding_view import OnboardingView

        page = self.page
        todo_app = getattr(page, '_todo_app_ref', None)

        def _close_tutorial():
            page.controls.clear()
            if todo_app:
                page.add(todo_app)

        onboarding = OnboardingView(
            on_complete=_close_tutorial,
            llm_cfg=self._cfg,
            is_revisit=True,
        )
        page.controls.clear()
        page.add(onboarding)

    def _on_nav_click(self, e):
        section = e.control.data
        if section == self._current_section:
            return
        self._current_section = section
        # 更新导航高亮
        for item in self._nav_column.content.controls:
            is_selected = item.data == section
            item.bgcolor = AppColors.PANEL_BG if is_selected else None
            row = item.content
            row.controls[0].color = ft.Colors.PRIMARY if is_selected else AppColors.TEXT_HINT
            row.controls[1].weight = ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_400
            row.controls[1].color = ft.Colors.PRIMARY if is_selected else None
        # 更新内容区
        self._content_area.content = self._build_section(section)
        self.update()

    def _on_mode_change(self, e):
        self.tm.set_theme_mode(self.page, e.control.value)

    def _on_seed_change(self, e):
        self.tm.set_seed(self.page, e.control.value)

    def _on_lang_change(self, e):
        self.tm.set_language(e.control.value)
        if self._on_lang_change_cb:
            self._on_lang_change_cb()
        self._content_area.content = self._build_section(self._current_section)
        self.update()
