from pathlib import Path

import flet as ft

from services.llm_config_manager import LLMConfigManager
from storage.daily_assessment_repo import DailyAssessmentRepo
from storage.setting_repo import SettingRepo
from ui.theme import ThemeManager
from ui.views.todo_view import TodoApp

ROOT_DIR = Path(__file__).resolve().parent


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

    # 恢复上次窗口位置和大小
    w = repo.get("win.width")
    h = repo.get("win.height")
    left = repo.get("win.left")
    top = repo.get("win.top")
    if w:
        page.window.width = float(w)
    else:
        page.window.width = 1100
    if h:
        page.window.height = float(h)
    else:
        page.window.height = 800
    if left:
        page.window.left = float(left)
    if top:
        page.window.top = float(top)

    # 关闭时保存窗口位置和大小
    def _on_window_event(e: ft.WindowEvent):
        if e.type == ft.WindowEventType.RESIZE:
            repo.set("win.width", str(int(page.window.width)))
            repo.set("win.height", str(int(page.window.height)))
        elif e.type == ft.WindowEventType.MOVE:
            repo.set("win.left", str(int(page.window.left)))
            repo.set("win.top", str(int(page.window.top)))

    page.window.on_event = _on_window_event

    page.add(TodoApp(tm, repo, llm_cfg, assessment_repo))


if __name__ == "__main__":
    ft.run(main)
