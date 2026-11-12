
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

    def load_saved_questions(self):
        self.saved_questions = (
            self.local_db.get_saved_questions(
                self.quiz_service
            )
        )

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
                    ft.ElevatedButton(
                        "Back",
                        on_click=lambda e: self.on_back(),
                    ),
                ]
            )

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

        return ft.Column(
            controls,
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
