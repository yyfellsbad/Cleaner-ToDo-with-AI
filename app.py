import flet as ft

from ui.views.todo_view import TodoApp
from ui.theme import get_app_theme


def main(page: ft.Page):
    page.title = "Cleaner"
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.theme = get_app_theme()
    page.padding = ft.Padding.symmetric(horizontal=12, vertical=16)
    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Container(
                expand=True,
                alignment=ft.Alignment(0, -1),
                content=ft.Container(content=TodoApp(), expand=True, padding=8),
            ),
        )
    )


if __name__ == "__main__":
    ft.run(main)
