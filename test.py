import flet as ft

def main(page: ft.Page):
    page.title = "Flet counter example"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    input = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)
    input1 = ft.TextField(value="10", text_align=ft.TextAlign.LEFT, width=150, height=50)
    test_list = []

    def minus_click(e):
        input.value = str(int(input.value) - 1)

    def plus_click(e):
        input.value = str(int(input.value) + 1)

    def add_button(e):
        test_list.append(ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=add_button))
        page.update()

    tasks_view = ft.Column()

    page.add(
        ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                input,
                ft.IconButton(ft.Icons.REMOVE, on_click=minus_click),
                input1,
                ft.IconButton(ft.Icons.ADD, on_click=plus_click),
                ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=add_button),
            ],
            
        ),
        ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=test_list,
        ),
        tasks_view,
    )

ft.run(main)