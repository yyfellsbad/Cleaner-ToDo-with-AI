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
    page.window.width = 1100
    page.window.height = 800

    # 初始化主题管理器并加载偏好
    repo = SettingRepo()
    tm = ThemeManager.instance()
    tm.load(repo)
    tm.apply(page)

    # 初始化 LLM 配置管理器
    llm_cfg = LLMConfigManager.instance()
    llm_cfg.load(repo)

    # 初始化每日评估存储
    assessment_repo = DailyAssessmentRepo()

    page.add(TodoApp(tm, repo, llm_cfg, assessment_repo))


if __name__ == "__main__":
    ft.run(main)
