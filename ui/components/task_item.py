import flet as ft
from datetime import datetime


class Task(ft.Column):
    def __init__(
        self, task_name, task_delete, app, task_id=None, date=None, completed=False
    ):
        super().__init__()
        self.app = app
        self.task_id = task_id
        self.task_name = task_name
        self.date = date or datetime.now().date()
        self.completed = completed
        self.task_delete = task_delete

    def build(self):
        self.display_task = ft.Checkbox(
            value=False, label=self.task_name, on_change=self.status_changed
        )
        self.edit_name = ft.TextField(expand=1)

        self.display_view = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    [
                        ft.Text(self.task_name, size=16),
                        ft.Text(f"Date: {self.date}", size=12, color=ft.Colors.GREY),
                    ]
                ),
                ft.Checkbox(value=self.completed, on_change=self.status_changed),
                ft.Row(
                    spacing=0,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CREATE_OUTLINED,
                            tooltip="Edit To-Do",
                            on_click=self.edit_clicked,
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            tooltip="Delete To-Do",
                            on_click=self.delete_clicked,
                        ),
                    ],
                ),
            ],
        )

        self.edit_view = ft.Row(
            visible=False,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.edit_name,
                ft.IconButton(
                    icon=ft.Icons.DONE_OUTLINE_OUTLINED,
                    icon_color=ft.Colors.GREEN,
                    tooltip="Update To-Do",
                    on_click=self.save_clicked,
                ),
            ],
        )
        self.controls = [self.display_view, self.edit_view]

    def edit_clicked(self, e):
        self.edit_name.value = self.display_task.label
        self.display_view.visible = False
        self.edit_view.visible = True

    def save_clicked(self, e):
        self.task_name = self.edit_name.value
        self.display_view.visible = True
        self.edit_view.visible = False
        self.app.save_task(self)

    def status_changed(self, e):
        self.completed = e.control.value
        self.app.save_task(self)

    def delete_clicked(self, e):
        self.task_delete(self)
