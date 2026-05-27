from __future__ import annotations

import flet as ft

from ui.theme import AppColors, THEME_SEEDS, THEME_SEED_LABELS, ThemeManager


class SettingsView(ft.Column):
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.tm = theme_manager
        self.expand = True
        self.spacing = 0
        self._current_section = "appearance"
        self._build()

    def _build(self):
        # ── 左侧导航 ──
        self._nav_items = {
            "appearance": ("外观", ft.Icons.PALETTE_OUTLINED),
            "language": ("语言", ft.Icons.LANGUAGE),
            "assistant": ("助手设置", ft.Icons.SMART_TOY_OUTLINED),
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
            width=180,
            padding=ft.Padding(12, 16, 12, 16),
            content=ft.Column(
                spacing=4,
                controls=nav_controls,
            ),
        )

        # ── 右侧内容区 ──
        self._content_area = ft.Container(
            expand=True,
            padding=ft.Padding(20, 16, 20, 16),
            content=self._build_section(self._current_section),
        )

        self.controls = [
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
        return ft.Container()

    def _build_appearance(self) -> ft.Control:
        mode_radios = ft.RadioGroup(
            value=self.tm.theme_mode,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Radio(value="light", label="浅色"),
                    ft.Radio(value="dark", label="深色"),
                    ft.Radio(value="system", label="跟随系统"),
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
                        label=THEME_SEED_LABELS.get(name, name),
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
                ft.Text("外观设置", size=18, weight=ft.FontWeight.W_600),
                ft.Divider(),
                ft.Text("主题模式", weight=ft.FontWeight.W_500),
                mode_radios,
                ft.Divider(),
                ft.Text("主题色", weight=ft.FontWeight.W_500),
                seed_radios,
                ft.Container(height=8),
                ft.Text(
                    "设置会自动保存，下次打开时恢复。",
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
                ft.Text("语言设置", size=18, weight=ft.FontWeight.W_600),
                ft.Divider(),
                ft.Text("界面语言", weight=ft.FontWeight.W_500),
                lang_radios,
                ft.Container(height=8),
                ft.Text(
                    "切换语言后需要重启应用生效。",
                    size=12,
                    color=AppColors.TEXT_HINT,
                ),
            ],
        )

    def _build_assistant(self) -> ft.Control:
        return ft.Column(
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("助手设置", size=18, weight=ft.FontWeight.W_600),
                ft.Divider(),
                ft.Container(
                    border_radius=8,
                    padding=16,
                    bgcolor=AppColors.PANEL_BG,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("关于智能助手", weight=ft.FontWeight.W_500),
                            ft.Text(
                                "智能助手支持自然语言操作待办任务，包括：\n\n"
                                "• 新增任务：帮我添加一个待办\n"
                                "• 查看待办：查看我的任务\n"
                                "• 修改任务：把开会改成周五\n"
                                "• 完成任务：标记任务为完成\n"
                                "• 删除任务：删除待办xxx\n"
                                "• 任务规划：我接下来应该做什么\n\n"
                                "支持中文自然语言输入，也可指定日期和持续时间。",
                                size=13,
                                color=AppColors.TEXT_HINT,
                            ),
                        ],
                    ),
                ),
            ],
        )

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
