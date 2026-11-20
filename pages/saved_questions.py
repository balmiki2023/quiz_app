
import flet as ft

class SavedQuestionsPage:
    def __init__(
        self,
        page,
        local_db,
        quiz_service,
        on_back,
    ):
        self.page = page
        self.local_db = local_db
        self.quiz_service = quiz_service
        self.on_back = on_back

        self.saved_questions = []

        self.current_page = 0
        self.page_size = 20
        self.total_saved_questions = 0


    def load_saved_questions(self):
        self.total_saved_questions = (
            self.local_db.get_saved_question_count()
        )

        self.saved_questions = (
            self.local_db.get_saved_questions(
                self.quiz_service,
                page=self.current_page,
                page_size=self.page_size,
            )
        )

    def go_to_next_page(self, e):
        total_pages = (
            self.total_saved_questions + self.page_size - 1
        ) // self.page_size

        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.refresh_page()


    def go_to_previous_page(self, e):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_page()


    def refresh_page(self):
        try:
            self.load_saved_questions()

            self.page.controls.clear()
            self.page.add(self.build())
            self.page.update()

        except Exception as error:
            print("Could not change saved questions page:", error)

    def remove_saved_question(self, question_id):
        try:
            # Toggle removes the existing bookmark.
            is_saved = self.local_db.toggle_question_save(
                question_id
            )

            if is_saved:
                print("Question was unexpectedly saved again.")
                return

            self.load_saved_questions()

            self.page.controls.clear()
            self.page.add(self.build())
            self.page.update()

        except Exception as error:
            print("Could not remove saved question:", error)

    
    def build(self):
        try:
            self.load_saved_questions()

        except Exception as error:
            return ft.Column(
                [
                    ft.Text(
                        "Could not load saved questions",
                        color=ft.Colors.RED,
                    ),
                    ft.Text(str(error)),
                    ft.Button(
                        "Back",
                        on_click=lambda e: self.on_back(),
                    ),
                ]
            )

        # Header
        controls = [
            ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: self.on_back(),
                    ),
                    ft.Text(
                        "Saved Questions",
                        size=26,
                        weight=ft.FontWeight.BOLD,
                    ),
                ]
            )
        ]

        # Question cards
        if not self.saved_questions:
            controls.append(
                ft.Text("You haven't saved any questions yet.")
            )

        else:
            for question in self.saved_questions:
                controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=15,
                            content=ft.Column(
                                [
                                    ft.Text(
                                        question.get("question_text", ""),
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        "A. " + str(question.get("option_a", "")),
                                    ),
                                    ft.Text(
                                        "B. " + str(question.get("option_b", "")),
                                    ),
                                    ft.Text(
                                        "C. " + str(question.get("option_c", "")),
                                    ),
                                    ft.Text(
                                        "D. " + str(question.get("option_d", "")),
                                    ),
                                    ft.TextButton(
                                        "Remove from saved",
                                        icon=ft.Icons.BOOKMARK_REMOVE,
                                        on_click=lambda e, qid=question["id"]:
                                            self.remove_saved_question(qid),
                                    ),
                                ],
                                spacing=8,
                            ),
                        )
                    )
                )

        # Pagination
        total_pages = (
            self.total_saved_questions + self.page_size - 1
        ) // self.page_size

        if self.total_saved_questions > 0:
            controls.append(ft.Divider())

            controls.append(
                ft.Row(
                    [
                        ft.Button(
                            "Previous",
                            icon=ft.Icons.ARROW_BACK,
                            disabled=self.current_page == 0,
                            on_click=self.go_to_previous_page,
                        ),
                        ft.Text(
                            f"Page {self.current_page + 1} of {total_pages}"
                        ),
                        ft.Button(
                            "Next",
                            icon=ft.Icons.ARROW_FORWARD,
                            disabled=self.current_page >= total_pages - 1,
                            on_click=self.go_to_next_page,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        return ft.Column(
            controls,
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

