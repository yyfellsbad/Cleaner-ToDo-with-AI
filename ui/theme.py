import flet as ft


# ── 颜色配置 ──────────────────────────────────────────────
class AppColors:
    # 面板背景
    PANEL_BG = ft.Colors.SURFACE
    CHAT_INPUT_BG = ft.Colors.SURFACE_CONTAINER_HIGHEST

    # 分割条
    SPLITTER_TRACK = "#3A3A3A"
    SPLITTER_HANDLE = "#BDBDBD"

    # 聊天气泡
    CHAT_USER = ft.Colors.BLUE_GREY
    CHAT_ASSISTANT = ft.Colors.TEAL_700

    # 任务日期
    DATE_FUTURE = ft.Colors.BLUE
    DATE_TODAY = ft.Colors.ORANGE
    DATE_PAST = ft.Colors.GREY

    # 编辑确认按钮
    EDIT_CONFIRM_ICON = ft.Colors.GREEN

    # 辅助文字
    TEXT_HINT = ft.Colors.GREY


def get_app_theme():
    return ft.Theme(
        font_family="Microsoft YaHei",
    )
