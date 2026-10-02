import flet as ft


class AdminQuestions:
    def __init__(
        self,
        page,
        quiz_service,
        on_back,
    ):
        self.page = page
        self.quiz_service = quiz_service
        self.on_back = on_back

        self.category_dropdown = ft.Dropdown(
            label="Category",
            width=400,
            on_select=self.category_changed,
        )

        self.question_field = ft.TextField(
            label="Question",
            width=500,
            multiline=True,
        )
        
        self.explanation_field = ft.TextField(
            label="Explanation (optional)",
            width=500,
            multiline=True,
        )

        self.option_a = ft.TextField(
            label="Option A",
            width=500,
        )

        self.option_b = ft.TextField(
            label="Option B",
            width=500,
        )

        self.option_c = ft.TextField(
            label="Option C",
            width=500,
        )

        self.option_d = ft.TextField(
            label="Option D",
            width=500,
        )

        self.correct_dropdown = ft.Dropdown(
            label="Correct option",
            width=300,
            options=[
                ft.DropdownOption(
                    key="A",
                    text="A",
                ),
                ft.DropdownOption(
                    key="B",
                    text="B",
                ),
                ft.DropdownOption(
                    key="C",
                    text="C",
                ),
                ft.DropdownOption(
                    key="D",
                    text="D",
                ),
            ],
        )
        
        self.editing_question_id = None

        self.message = ft.Text("")

        self.load_categories()

        self.category_dropdown.on_change = (
            self.category_changed
        )
        
    
    def load_categories(self):
        categories = (
            self.quiz_service.get_categories()
        )

        self.category_dropdown.options = [
            ft.DropdownOption(
                key=str(category["id"]),
                text=category["name"],
            )
            for category in categories
        ]
        
        
    def category_changed(self, e=None):
        self.page.clean()
        self.page.add(self.build())
        self.page.update()
    

    def build(self):
        self.main_column = ft.Column(
            [
                ft.Button(
                    "← Back",
                    on_click=self.on_back,
                ),

                ft.Text(
                    "Question Management",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),

                self.category_dropdown,

                self.question_field,

                self.explanation_field,

                self.option_a,

                self.option_b,

                self.option_c,

                self.option_d,

                self.correct_dropdown,

                ft.Button(
                    "Add Question",
                    on_click=self.add_question,
                ),

                self.message,

                ft.Divider(),

                ft.Text(
                    "Question Bank",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                ),

                self.build_question_list(),
            ],
            width=600,
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        return self.main_column

    def add_question(self, e=None):
        category_id = self.category_dropdown.value

        question_text = self.question_field.value.strip()
        explanation = self.explanation_field.value.strip()

        option_a = self.option_a.value.strip()
        option_b = self.option_b.value.strip()
        option_c = self.option_c.value.strip()
        option_d = self.option_d.value.strip()

        correct_option = self.correct_dropdown.value

        if not category_id:
            self.message.value = "Please select a category."
            self.page.update()
            return

        if not question_text:
            self.message.value = "Question is required."
            self.page.update()
            return

        if not all([
            option_a,
            option_b,
            option_c,
            option_d,
        ]):
            self.message.value = (
                "All four options are required."
            )
            self.page.update()
            return

        if not correct_option:
            self.message.value = (
                "Please select the correct option."
            )
            self.page.update()
            return

        try:
            self.quiz_service.create_question(
                category_id=category_id,
                question_text=question_text,
                explanation=explanation,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_option=correct_option,
            )

            self.message.value = (
                "Question added successfully."
            )

            self.question_field.value = ""
            self.explanation_field.value = ""
            self.option_a.value = ""
            self.option_b.value = ""
            self.option_c.value = ""
            self.option_d.value = ""
            self.correct_dropdown.value = None

            self.page.clean()
            self.page.add(self.build())
            self.page.update()

        except Exception as error:
            self.message.value = str(error)
            self.page.update()
    
    def save_question(self, e=None):
        if not self.editing_question_id:
            self.message.value = (
                "Select a question to edit first."
            )
            self.page.update()
            return

        question_text = self.question_field.value.strip()
        explanation = self.explanation_field.value.strip()

        option_a = self.option_a.value.strip()
        option_b = self.option_b.value.strip()
        option_c = self.option_c.value.strip()
        option_d = self.option_d.value.strip()

        correct_option = self.correct_dropdown.value

        if not question_text:
            self.message.value = "Question is required."
            self.page.update()
            return

        if not all([
            option_a,
            option_b,
            option_c,
            option_d,
        ]):
            self.message.value = (
                "All four options are required."
            )
            self.page.update()
            return

        if not correct_option:
            self.message.value = (
                "Please select the correct option."
            )
            self.page.update()
            return

        try:
            self.quiz_service.update_question(
                question_id=self.editing_question_id,
                question_text=question_text,
                explanation=explanation,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_option=correct_option,
            )

            self.editing_question_id = None

            self.question_field.value = ""
            self.explanation_field.value = ""
            self.option_a.value = ""
            self.option_b.value = ""
            self.option_c.value = ""
            self.option_d.value = ""
            self.correct_dropdown.value = None

            self.message.value = (
                "Question updated successfully."
            )

            self.page.clean()
            self.page.add(self.build())
            self.page.update()

        except Exception as error:
            self.message.value = str(error)
            self.page.update()
    
    def delete_question(self, question_id):
        try:
            deleted = self.quiz_service.delete_question(
                question_id
            )

            if not deleted:
                self.message.value = (
                    "Delete failed: no question was deleted."
                )
                self.page.update()
                return

            self.message.value = (
                "Question deleted successfully."
            )

            self.page.clean()
            self.page.add(self.build())
            self.page.update()

        except Exception as error:
            self.message.value = str(error)
            self.page.update()
                
    def build_question_list(self):
        category_id = self.category_dropdown.value

        if not category_id:
            return ft.Text(
                "Select a category to view its questions."
            )

        questions = (
            self.quiz_service.get_admin_questions_by_category(
                category_id
            )
        )

        if not questions:
            return ft.Text("No questions found.")

        controls = []

        for question in questions:
            controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    f"Question {question.get('quiz_question_order')}",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                ),

                                ft.Text(
                                    question["question_text"],
                                    size=17,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"A. {question['option_a']}"
                                ),
                                ft.Text(
                                    f"B. {question['option_b']}"
                                ),
                                ft.Text(
                                    f"C. {question['option_c']}"
                                ),
                                ft.Text(
                                    f"D. {question['option_d']}"
                                ),
                                ft.Text(
                                    f"Correct: "
                                    f"{question['correct_option']}"
                                ),
                                ft.Text(
                                    "Explanation: "
                                    f"{question.get('explanation') or 'None'}"
                                ),
                                ft.Row(
                                    [
                                        ft.Button(
                                            "Edit",
                                            on_click=lambda e, q=question:
                                                self.edit_question(q),
                                        ),
                                        ft.Button(
                                            "Delete",
                                            on_click=lambda e, question_id=question["id"]:
                                                self.delete_question(
                                                    question_id
                                                ),
                                        ),
                                    ]
                                ),
                            ],
                            spacing=5,
                        ),
                        padding=15,
                    )
                )
            )

        return ft.Column(
            controls,
            spacing=10,
        )
        
    def edit_question(self, question):
        self.question_field.value = (
            question["question_text"]
        )

        self.explanation_field.value = (
            question.get("explanation") or ""
        )

        self.option_a.value = question["option_a"]
        self.option_b.value = question["option_b"]
        self.option_c.value = question["option_c"]
        self.option_d.value = question["option_d"]

        self.correct_dropdown.value = (
            question["correct_option"]
        )

        self.editing_question_id = question["id"]

        self.message.value = (
            "Editing question. Make your changes and save."
        )

        self.page.update()
        
        self.page.run_task(
            self.scroll_to_top
        )
    
    async def scroll_to_top(self):
        await self.main_column.scroll_to(
            offset=0,
            duration=300,
        )
    
        
    