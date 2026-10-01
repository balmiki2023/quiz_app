import flet as ft

from services.question_import_service import QuestionImportService


class QuestionImport:
    def __init__(
        self,
        page,
        quiz_service,
        supabase,
        on_back,
    ):
        self.page = page
        self.quiz_service = quiz_service
        self.import_service = QuestionImportService(supabase)
        self.on_back = on_back

        self.selected_category_id = None
        self.selected_file = None

        self.category_dropdown = ft.Dropdown(
            label="Category",
            width=400,
        )
        
        self.new_category_name = ft.TextField(
            label="New category name",
            width=400,
        )

        self.new_category_description = ft.TextField(
            label="Description",
            width=400,
            multiline=True,
        )

        self.message = ft.Text("")

        self.file_picker = ft.FilePicker()

    def build(self):
        self.load_categories()

        return ft.Column(
            
            [
                ft.Button(
                    "← Back to Admin Dashboard",
                    on_click=lambda e: self.on_back(),
                ),

                ft.Text(
                    "Import Questions",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Text(
                    "Import questions from a CSV exported from Google Sheets."
                ),

                ft.Divider(),

                self.category_dropdown,
                
                ft.Text(
                    "Or create a new category",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),

                self.new_category_name,

                self.new_category_description,

                ft.Button(
                    "Add New Category",
                    on_click=self.add_category,
                ),

                ft.Button(
                    "Select CSV File",
                    on_click=self.select_file,
                ),

                ft.Button(
                    "Import Questions",
                    on_click=self.import_questions,
                ),

                self.message,
            ],
            width=600,
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
        )
    
    def add_category(self, e=None):
        name = self.new_category_name.value.strip()
        description = self.new_category_description.value.strip()

        if not name:
            self.message.value = "Category name is required."
            self.message.color = ft.Colors.RED
            self.page.update()
            return

        try:
            category = self.quiz_service.create_category(
                name=name,
                description=description,
            )

            self.new_category_name.value = ""
            self.new_category_description.value = ""

            self.load_categories()

            self.category_dropdown.value = category["id"]

            self.message.value = (
                f"Category '{name}' created successfully."
            )
            self.message.color = ft.Colors.GREEN

            self.page.update()

        except Exception as error:
            self.message.value = str(error)
            self.message.color = ft.Colors.RED
            self.page.update()
    
    def load_categories(self):
        categories = self.quiz_service.get_categories()

        self.category_dropdown.options = [
            ft.DropdownOption(
                key=category["id"],
                text=category["name"],
            )
            for category in categories
        ]

    async def select_file(self, e):
        files = await self.file_picker.pick_files(
            allow_multiple=False,
            with_data=True,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["csv"],
        )

        if not files:
            return

        self.selected_file = files[0]

        self.message.value = (
            f"Selected: {self.selected_file.name}"
        )
        self.message.color = ft.Colors.GREEN

        self.page.update()
        
        
    def import_questions(self, e=None):
        category_id = self.category_dropdown.value

        if not category_id:
            self.message.value = "Please select a category."
            self.message.color = ft.Colors.RED
            self.page.update()
            return

        if not self.selected_file:
            self.message.value = "Please select a CSV file."
            self.message.color = ft.Colors.RED
            self.page.update()
            return

        try:
            csv_text = self.selected_file.bytes.decode(
                "utf-8-sig"
            )

            imported_questions = (
                self.import_service.import_csv(
                    csv_text,
                    category_id,
                )
            )

            self.message.value = (
                f"Successfully imported "
                f"{len(imported_questions)} questions."
            )
            self.message.color = ft.Colors.GREEN

            self.page.update()

        except Exception as error:
            self.message.value = str(error)
            self.message.color = ft.Colors.RED

            self.page.update()