import csv
import io
import re
import requests

from urllib.parse import (
    urlparse,
    parse_qs,
    urlencode,
    urlunparse,
)
from urllib.request import Request, urlopen
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
        
        self.sheet_url_field = ft.TextField(
            label="Google Sheets URL",
            hint_text="Paste your Google Sheets link here",
            width=500,
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
            controls=[
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
                    'Import questions from a CSV with headers:\n'
                    '"question_text","option_a","option_b",'
                    '"option_c","option_d","correct_option","explanation"'
                ),

                ft.Divider(),

                self.category_dropdown,

                ft.Text(
                    "Bulk Import Questions",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),

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
                
                self.sheet_url_field,

                ft.Button(
                    "Import from Google Sheets",
                    on_click=self.import_questions_from_sheet,
                ),


                self.message,
            ],
            width=600,
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
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
            
    
    def _get_google_csv_url(self, sheet_url):
        """Convert a normal Google Sheets link to a CSV export URL."""
        parsed = urlparse(sheet_url.strip())

        if (
            parsed.scheme != "https"
            or parsed.hostname != "docs.google.com"
        ):
            raise ValueError(
                "Enter a Google Sheets URL starting with "
                "https://docs.google.com/spreadsheets/..."
            )

        parts = parsed.path.strip("/").split("/")
        query = parse_qs(parsed.query)
        fragment = parse_qs(parsed.fragment)

        gid = (
            query.get("gid")
            or fragment.get("gid")
            or [""]
        )[0]

        if (
            len(parts) < 4
            or parts[0] != "spreadsheets"
            or parts[1] != "d"
        ):
            raise ValueError("This does not look like a Google Sheets link.")

        # Published-to-web links, such as /spreadsheets/d/e/.../pub
        if parts[2] == "e":
            if parts[-1] != "pub":
                raise ValueError(
                    "For a published sheet, use its published CSV link."
                )

            params = {
                key: values[0]
                for key, values in query.items()
                if values
            }
            params["output"] = "csv"

            if gid:
                params["gid"] = gid

            return urlunparse((
                "https",
                "docs.google.com",
                parsed.path,
                "",
                urlencode(params),
                "",
            ))

        # Normal sharing/edit link.
        sheet_id = parts[2]
        params = {"format": "csv"}

        if gid:
            params["gid"] = gid

        return urlunparse((
            "https",
            "docs.google.com",
            f"/spreadsheets/d/{sheet_id}/export",
            "",
            urlencode(params),
            "",
        ))

    
    def import_questions_from_sheet(self, e=None):
        sheet_url = (self.sheet_url_field.value or "").strip()

        if not sheet_url:
            self.message.value = "Please enter a Google Sheets URL."
            self.message.color = ft.Colors.RED
            self.page.update()
            return

        try:
            match = re.search(
                r"/spreadsheets/d/([a-zA-Z0-9_-]+)",
                sheet_url,
            )

            if not match:
                raise ValueError("Invalid Google Sheets URL.")

            spreadsheet_id = match.group(1)

            gid_match = re.search(r"[?&#]gid=(\d+)", sheet_url)
            gid = gid_match.group(1) if gid_match else "0"

            export_url = (
                f"https://docs.google.com/spreadsheets/d/"
                f"{spreadsheet_id}/export?format=csv&gid={gid}"
            )

            response = requests.get(export_url, timeout=30)
            response.raise_for_status()

            # Confirm that Google returned CSV rather than an HTML
            # login or permission page.
            content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type.lower():
                raise ValueError(
                    "The sheet is not publicly accessible. "
                    "Check its sharing permissions."
                )

            csv_text = response.content.decode("utf-8-sig")

            # Validate that the response contains usable CSV data.
            rows = list(csv.reader(io.StringIO(csv_text)))
            if len(rows) < 2:
                raise ValueError(
                    "The sheet must contain a header and at least one question."
                )

            # Reuse the existing CSV import pipeline.
            self.import_questions(e=None, csv_text=csv_text)

        except Exception as error:
            self.message.value = f"Google Sheets import failed: {error}"
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
        
        
    def import_questions(self, e=None, csv_text=None):
        category_id = self.category_dropdown.value

        if not category_id:
            self.message.value = "Please select a category."
            self.message.color = ft.Colors.RED
            self.page.update()
            return

        if csv_text is None:
            if not self.selected_file:
                self.message.value = "Please select a CSV file."
                self.message.color = ft.Colors.RED
                self.page.update()
                return

            try:
                csv_text = self.selected_file.bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                self.message.value = "The CSV file must use UTF-8 encoding."
                self.message.color = ft.Colors.RED
                self.page.update()
                return

        try:
            imported_questions = self.import_service.import_csv(
                csv_text,
                category_id,
            )

            self.message.value = (
                f"Successfully imported {len(imported_questions)} questions."
            )
            self.message.color = ft.Colors.GREEN

        except Exception as error:
            self.message.value = f"Import failed: {error}"
            self.message.color = ft.Colors.RED

        finally:
            self.page.update()