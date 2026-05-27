from __future__ import annotations

import flet as ft


# ── 主题色预设 ──────────────────────────────────────────────
THEME_SEEDS: dict[str, ft.Colors] = {
    "blue": ft.Colors.BLUE,
    "indigo": ft.Colors.INDIGO,
    "purple": ft.Colors.DEEP_PURPLE,
    "teal": ft.Colors.TEAL,
    "orange": ft.Colors.DEEP_ORANGE,
    "pink": ft.Colors.PINK,
}

THEME_SEED_LABELS: dict[str, str] = {
    "blue": "蓝色",
    "indigo": "靛蓝",
    "purple": "紫色",
    "teal": "青色",
    "orange": "橙色",
    "pink": "粉色",
}

DEFAULT_SEED = "blue"


# ── 语义颜色（theme-aware，跟随 Material 3 配色方案自动变化） ──
class AppColors:
    # 面板
    PANEL_BG = ft.Colors.SURFACE_CONTAINER_LOW
    PANEL_BORDER = ft.Colors.OUTLINE_VARIANT

    # 分割条
    SPLITTER_TRACK = ft.Colors.OUTLINE_VARIANT
    SPLITTER_HANDLE = ft.Colors.OUTLINE

    # 聊天气泡
    BUBBLE_USER = ft.Colors.PRIMARY_CONTAINER
    BUBBLE_USER_TEXT = ft.Colors.ON_PRIMARY_CONTAINER
    BUBBLE_ASSISTANT = ft.Colors.SECONDARY_CONTAINER
    BUBBLE_ASSISTANT_TEXT = ft.Colors.ON_SECONDARY_CONTAINER

    # 任务日期（固定语义色，不随主题变化）
    DATE_FUTURE = ft.Colors.BLUE
    DATE_TODAY = ft.Colors.ORANGE
    DATE_PAST = ft.Colors.GREY
    DATE_ONGOING = ft.Colors.GREEN

    # 编辑确认
    EDIT_CONFIRM_ICON = ft.Colors.GREEN

    # 辅助
    TEXT_HINT = ft.Colors.ON_SURFACE_VARIANT


# ── ThemeManager 单例 ──────────────────────────────────────
class ThemeManager:
    _instance: ThemeManager | None = None

    @classmethod
    def instance(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.theme_mode: str = "system"  # "light" / "dark" / "system"
        self.seed_name: str = DEFAULT_SEED
        self.language: str = "zh"
        self._repo = None

    @property
    def dark_mode(self) -> bool:
        return self.theme_mode == "dark"

    def load(self, repo) -> None:
        """从数据库加载偏好"""
        self._repo = repo
        mode = repo.get("theme_mode", "system")
        if mode in ("light", "dark", "system"):
            self.theme_mode = mode
        else:
            self.theme_mode = "system"
        self.seed_name = repo.get("theme_seed", DEFAULT_SEED)
        if self.seed_name not in THEME_SEEDS:
            self.seed_name = DEFAULT_SEED
        self.language = repo.get("language", "zh")

    def _save(self) -> None:
        if self._repo:
            self._repo.set("theme_mode", self.theme_mode)
            self._repo.set("theme_seed", self.seed_name)
            self._repo.set("language", self.language)

    @property
    def seed_color(self) -> ft.Colors:
        return THEME_SEEDS.get(self.seed_name, THEME_SEEDS[DEFAULT_SEED])

    def _build_theme(self, seed: ft.Colors) -> ft.Theme:
        return ft.Theme(
            color_scheme_seed=seed,
            font_family="Microsoft YaHei",
            visual_density=ft.VisualDensity.COMPACT,
        )

    def apply(self, page: ft.Page) -> None:
        seed = self.seed_color
        page.theme = self._build_theme(seed)
        page.dark_theme = self._build_theme(seed)
        if self.theme_mode == "system":
            page.theme_mode = ft.ThemeMode.SYSTEM
        elif self.theme_mode == "dark":
            page.theme_mode = ft.ThemeMode.DARK
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
        page.bgcolor = ft.Colors.SURFACE

    def set_theme_mode(self, page: ft.Page, mode: str) -> None:
        if mode not in ("light", "dark", "system"):
            return
        self.theme_mode = mode
        self.apply(page)
        self._save()

    def set_seed(self, page: ft.Page, seed_name: str) -> None:
        if seed_name not in THEME_SEEDS:
            return
        self.seed_name = seed_name
        self.apply(page)
        self._save()

    def set_language(self, lang: str) -> None:
        if lang not in ("zh", "en"):
            return
        self.language = lang
        self._save()
