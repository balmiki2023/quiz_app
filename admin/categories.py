import flet as ft


class AdminCategories:
    def __init__(
        self,
        page,
        quiz_service,
        on_back,
    ):
        self.page = page
        self.quiz_service = quiz_service
        self.on_back = on_back

        self.name_field = ft.TextField(
            label="Category name",
            width=400,
        )

        self.description_field = ft.TextField(
            label="Description",
            width=400,
            multiline=True,
        )

        self.message = ft.Text("")

    def build(self):
        return ft.Column(
            [
                ft.Button(
                    "← Back",
                    on_click=self.on_back,
                ),

                ft.Text(
                    "Categories",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),

                self.name_field,

                self.description_field,

                ft.Button(
                    "Add Category",
                    on_click=self.add_category,
                ),

                self.message,

                ft.Divider(),

                ft.Text(
                    "Existing Categories",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),

                self.build_category_list(),
            ],
            width=600,
            spacing=15,
        )

    def build_category_list(self):
        categories = self.quiz_service.get_categories()

        controls = []

        for category in categories:
            controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    category["name"],
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    category.get(
                                        "description"
                                    )
                                    or ""
                                ),
                            ],
                            spacing=5,
                        ),
                        padding=15,
                    )
                )
            )

        if not controls:
            controls.append(
                ft.Text("No categories found.")
            )

        return ft.Column(
            controls,
            spacing=10,
        )

    def add_category(self, e=None):
        name = self.name_field.value.strip()
        description = (
            self.description_field.value.strip()
        )

        if not name:
            self.message.value = (
                "Category name is required."
            )
            self.page.update()
            return

        try:
            self.quiz_service.create_category(
                name=name,
                description=description,
            )

            self.name_field.value = ""
            self.description_field.value = ""

            self.message.value = (
                "Category created successfully."
            )

            self.page.clean()
            self.page.add(self.build())
            self.page.update()

        except Exception as error:
            self.message.value = str(error)
            self.page.update()