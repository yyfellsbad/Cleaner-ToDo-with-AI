from pathlib import Path

import flet as ft

from services.llm_config_manager import LLMConfigManager
from storage.daily_assessment_repo import DailyAssessmentRepo
from storage.setting_repo import SettingRepo
from ui.theme import ThemeManager
from ui.views.onboarding_view import OnboardingView
from ui.views.todo_view import TodoApp

ROOT_DIR = Path(__file__).resolve().parent


def _get_screens():
    """通过 Win32 API 获取所有显示器的工作区域。"""
    try:
        import ctypes
        import ctypes.wintypes as wintypes

        screens = []
        MONITORENUMPROC = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            wintypes.LPARAM,
        )

        def _cb(hmon, hdc, lprect, lparam):
            r = lprect.contents
            screens.append((r.left, r.top, r.right - r.left, r.bottom - r.top))
            return True

        ctypes.windll.user32.EnumDisplayMonitors(
            None, None, MONITORENUMPROC(_cb), 0
        )
        return screens or [(0, 0, 1920, 1080)]
    except Exception:
        return [(0, 0, 1920, 1080)]


def _pos_on_screen(x, y, w, h, screens):
    """判断 (x, y, w, h) 是否有足够面积落在某个屏幕上。"""
    for sx, sy, sw, sh in screens:
        ox = max(0, min(x + w, sx + sw) - max(x, sx))
        oy = max(0, min(y + h, sy + sh) - max(y, sy))
        if ox * oy > w * h * 0.3:
            return True
    return False


def before_main(page: ft.Page):
    """在 main 之前恢复窗口尺寸/位置，窗口首次出现时即为目标大小。"""
    repo = SettingRepo()
    screens = _get_screens()
    pw, ph = screens[0][2], screens[0][3]

    w = repo.get("win.width")
    h = repo.get("win.height")
    left = repo.get("win.left")
    top = repo.get("win.top")
    page.window.width = float(w) if w else min(1100, pw)
    page.window.height = float(h) if h else min(800, ph)
    if left and top:
        lx, ly = float(left), float(top)
        if _pos_on_screen(lx, ly, page.window.width, page.window.height, screens):
            page.window.left = lx
            page.window.top = ly
        else:
            page.window.left = (pw - page.window.width) / 2
            page.window.top = (ph - page.window.height) / 2

    maximized = repo.get("win.maximized")
    full_screen = repo.get("win.full_screen")
    if full_screen == "1":
        page.window.full_screen = True
    elif maximized == "1":
        page.window.maximized = True


def main(page: ft.Page):
    page.title = "Cleaner"
    page.padding = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    # 隐藏原生标题栏，使用自定义标题栏
    page.window.icon = str(ROOT_DIR / "pic" / "cleaner.ico")
    page.window.title_bar_hidden = True
    page.window.title_bar_buttons_hidden = False
    page.window.min_width = 780
    page.window.min_height = 400

    # 初始化存储和管理器
    repo = SettingRepo()
    tm = ThemeManager.instance()
    tm.load(repo)
    tm.apply(page)

    llm_cfg = LLMConfigManager.instance()
    llm_cfg.load(repo)

    assessment_repo = DailyAssessmentRepo()

    # 窗口事件：保存位置、大小、最大化/全屏状态
    def _on_window_event(e: ft.WindowEvent):
        if e.type == ft.WindowEventType.RESIZED:
            repo.set("win.width", str(int(page.window.width)))
            repo.set("win.height", str(int(page.window.height)))
        elif e.type == ft.WindowEventType.MOVED:
            repo.set("win.left", str(int(page.window.left)))
            repo.set("win.top", str(int(page.window.top)))
        elif e.type == ft.WindowEventType.MAXIMIZE:
            repo.set("win.maximized", "1")
        elif e.type == ft.WindowEventType.UNMAXIMIZE:
            repo.set("win.maximized", "0")
        elif e.type == ft.WindowEventType.ENTER_FULL_SCREEN:
            repo.set("win.full_screen", "1")
        elif e.type == ft.WindowEventType.LEAVE_FULL_SCREEN:
            repo.set("win.full_screen", "0")

    page.window.on_event = _on_window_event

    # 检查是否已完成 onboarding
    if repo.get("onboarding_completed") != "1":
        onboarding = OnboardingView(
            on_complete=lambda: _show_main_app(page, repo, tm, llm_cfg, assessment_repo),
            llm_cfg=llm_cfg,
        )
        page.add(onboarding)
    else:
        _show_main_app(page, repo, tm, llm_cfg, assessment_repo)

    # 注册键盘快捷键
    def _on_page_keyboard(e: ft.KeyboardEvent):
        if hasattr(page.controls[0], '_keyboard_handler'):
            page.controls[0]._keyboard_handler(e)

    page.on_keyboard_event = _on_page_keyboard


def _show_main_app(page: ft.Page, repo, tm, llm_cfg, assessment_repo):
    """显示主应用，移除 onboarding（如果存在）"""
    page.controls.clear()
    todo_app = TodoApp(tm, repo, llm_cfg, assessment_repo)
    page.add(todo_app)


if __name__ == "__main__":
    ft.run(main, before_main=before_main)
