import sqlite3
from datetime import datetime
from pathlib import Path

import flet as ft

from ui.components.task_item import Task


class TodoApp(ft.Column):
    def __init__(self):
        super().__init__()
        self.show_settings = False
        data_dir = Path(__file__).resolve().parents[2] / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = data_dir / "tasks.db"
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()
        self.tasks = ft.Column()
        self.load_tasks()

    def create_table(self):
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            completed INTEGER NOT NULL
        )"""
        )
        self.conn.commit()

    def load_tasks(self):
        cursor = self.conn.execute(
            "SELECT id, name, date, completed FROM tasks ORDER BY date DESC"
        )
        for row in cursor:
            task = Task(
                row[1],
                self.task_delete,
                self,
                row[0],
                datetime.fromisoformat(row[2]).date(),
                bool(row[3]),
            )
            self.tasks.controls.append(task)

    def save_task(self, task):
        if task.task_id is None:
            cursor = self.conn.execute(
                "INSERT INTO tasks (name, date, completed) VALUES (?, ?, ?)",
                (task.task_name, task.date.isoformat(), int(task.completed)),
            )
            task.task_id = cursor.lastrowid
        else:
            self.conn.execute(
                "UPDATE tasks SET name=?, date=?, completed=? WHERE id=?",
                (
                    task.task_name,
                    task.date.isoformat(),
                    int(task.completed),
                    task.task_id,
                ),
            )
        self.conn.commit()

    def delete_task(self, task):
        if task.task_id:
            self.conn.execute("DELETE FROM tasks WHERE id=?", (task.task_id,))
            self.conn.commit()

    def open_settings(self, e):
        self.show_settings = True
        self.main_view.visible = False
        self.settings_view.visible = True
        self.update()

    def close_settings(self, e):
        self.show_settings = False
        self.settings_view.visible = False
        self.main_view.visible = True
        self.update()

    def build(self):
        self.new_task = ft.TextField(
            hint_text="What needs to be done?", on_submit=self.add_clicked, expand=True
        )

        self.filter = ft.TabBar(
            scrollable=False,
            tabs=[
                ft.Tab(label="all"),
                ft.Tab(label="active"),
                ft.Tab(label="completed"),
            ],
        )

        self.filter_tabs = ft.Tabs(
            length=3,
            selected_index=0,
            on_change=lambda e: self.update(),
            content=self.filter,
        )

        self.items_left = ft.Text("0 items left")

        self.main_view = ft.Column(
            expand=True,
            spacing=16,
            visible=not self.show_settings,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS_OUTLINED,
                            tooltip="Settings",
                            on_click=self.open_settings,
                        ),
                        ft.Text(
                            value="TO DO",
                            theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                        ),
                        ft.Container(width=40),
                    ],
                ),
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(content=self.new_task, col={"xs": 10, "md": 11}),
                        ft.Container(
                            content=ft.FloatingActionButton(
                                icon=ft.Icons.ADD, on_click=self.add_clicked
                            ),
                            alignment=ft.Alignment(1, 0),
                            col={"xs": 2, "md": 1},
                        ),
                    ],
                    columns=12,
                    run_spacing=8,
                ),
                ft.Container(
                    expand=True,
                    padding=16,
                    border_radius=12,
                    bgcolor=ft.Colors.SURFACE,
                    content=ft.Column(
                        spacing=18,
                        expand=True,
                        controls=[
                            self.filter_tabs,
                            self.tasks,
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    self.items_left,
                                    ft.OutlinedButton(
                                        content="Clear completed",
                                        on_click=self.clear_clicked,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        )

        self.settings_view = ft.Column(
            expand=True,
            spacing=16,
            visible=self.show_settings,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            tooltip="Back",
                            on_click=self.close_settings,
                        ),
                        ft.Text(
                            value="Settings",
                            theme_style=ft.TextThemeStyle.HEADLINE_SMALL,
                        ),
                    ],
                ),
                ft.ResponsiveRow(
                    columns=12,
                    run_spacing=12,
                    controls=[
                        ft.Container(
                            col={"xs": 12, "md": 4},
                            height=460,
                            border_radius=12,
                            padding=16,
                            bgcolor=ft.Colors.SURFACE,
                            content=ft.Text("设置列表（预留）", color=ft.Colors.GREY),
                        ),
                        ft.Container(
                            col={"xs": 12, "md": 8},
                            height=460,
                            border_radius=12,
                            padding=16,
                            bgcolor=ft.Colors.SURFACE,
                            content=ft.Text(
                                "具体设置界面（预留）", color=ft.Colors.GREY
                            ),
                        ),
                    ],
                ),
            ],
        )

        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.spacing = 0
        self.controls = [self.main_view, self.settings_view]

    async def add_clicked(self, e):
        if self.new_task.value:
            task = Task(self.new_task.value, self.task_delete, self)
            self.tasks.controls.append(task)
            self.save_task(task)
            self.new_task.value = ""
            await self.new_task.focus()

    def task_delete(self, task):
        self.tasks.controls.remove(task)
        self.delete_task(task)

    def clear_clicked(self, e):
        for task in self.tasks.controls[:]:
            if task.completed:
                self.task_delete(task)

    def before_update(self):
        status = self.filter.tabs[self.filter_tabs.selected_index].label
        count = 0
        for task in self.tasks.controls:
            task.visible = (
                status == "all"
                or (status == "active" and not task.completed)
                or (status == "completed" and task.completed)
            )
            if not task.completed:
                count += 1
        self.items_left.value = f"{count} active item(s) left"
