import flet as ft

from storage.setting_repo import SettingRepo
from ui.theme import ThemeManager
from ui.views.todo_view import TodoApp


def main(page: ft.Page):
    page.title = "Cleaner"
    page.padding = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    # 隐藏原生标题栏，使用自定义标题栏
    page.window.title_bar_hidden = True
    page.window.title_bar_buttons_hidden = False
    page.window.min_width = 780
    page.window.min_height = 400
    page.window.width = 900
    page.window.height = 800

    # 初始化主题管理器并加载偏好
    repo = SettingRepo()
    tm = ThemeManager.instance()
    tm.load(repo)
    tm.apply(page)

    page.add(TodoApp(tm, repo))


if __name__ == "__main__":
    ft.run(main)
