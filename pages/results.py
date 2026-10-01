import flet as ft


class ResultsPage:
    def __init__(
        self,
        page,
        attempt_service,
        quiz_service,
        on_back,
    ):
        self.page = page
        self.attempt_service = attempt_service
        self.quiz_service = quiz_service
        self.on_back = on_back
    
    def review_attempt(self, attempt):
        try:
            attempt_id = attempt["id"]

            full_attempt = (
                self.attempt_service
                .get_attempt(attempt_id)
            )

            if not full_attempt:
                raise Exception(
                    "Could not find this quiz attempt."
                )

            questions = (
                self.quiz_service
                .get_questions(
                    full_attempt["quiz_id"]
                )
            )

            saved_answers = (
                full_attempt.get("answers") or []
            )

            self.page.clean()

            controls = [
                ft.Button(
                    "← Back",
                    on_click=self.go_back,
                ),
                ft.Text(
                    "Review Answers",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),
            ]

            quiz_data = full_attempt.get("quizzes")
            quiz_title = "Unknown Quiz"

            if quiz_data:
                quiz_title = quiz_data.get(
                    "title",
                    "Unknown Quiz",
                )

            controls.append(
                ft.Text(
                    quiz_title,
                    size=22,
                    weight=ft.FontWeight.BOLD,
                )
            )

            score = full_attempt.get("score", 0)
            total = full_attempt.get(
                "total_questions",
                0,
            )

            controls.append(
                ft.Text(
                    f"Score: {score} / {total}",
                    size=20,
                )
            )

            answer_map = {
                answer["question_id"]: answer
                for answer in saved_answers
            }

            for index, question in enumerate(
                questions,
                start=1,
            ):
                saved_answer = answer_map.get(
                    question["id"]
                )

                selected_option = None
                is_correct = False

                if saved_answer:
                    selected_option = (
                        saved_answer.get(
                            "selected_option"
                        )
                    )

                    is_correct = (
                        saved_answer.get(
                            "is_correct",
                            False,
                        )
                    )

                if selected_option:
                    option_text = question.get(
                        f"option_{selected_option.lower()}"
                    )

                    selected_answer_text = (
                        f"{selected_option}. "
                        f"{option_text}"
                    )
                else:
                    selected_answer_text = (
                        "Not answered"
                    )

                status = "Correct" if is_correct else "Incorrect"

                controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        f"{index}. "
                                        f"{question['question_text']}",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        f"Your answer: "
                                        f"{selected_answer_text}"
                                    ),
                                    
                                    ft.Text(
                                        (
                                            f"Status: {status}\n"
                                            f"Explanation: "
                                            f"{question['explanation']}"
                                        )
                                        if (
                                            selected_option is not None
                                            and question.get("explanation")
                                        )
                                        else ""
                                    ),
                                ],
                                spacing=8,
                            ),
                            padding=15,
                        )
                    )
                )

            self.page.add(
                ft.Column(
                    controls,
                    spacing=15,
                )
            )

            self.page.update()

        except Exception as error:
            self.page.clean()

            self.page.add(
                ft.Column(
                    [
                        ft.Button(
                            "← Back",
                            on_click=self.go_back,
                        ),
                        ft.Text(
                            "Could not load review",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            str(error),
                            color=ft.Colors.RED,
                        ),
                    ],
                    spacing=15,
                )
            )

            self.page.update()
    
    def build(self):
        try:
            user_id = (
                self.attempt_service
                .get_current_user_id()
            )

            if not user_id:
                return ft.Column(
                    [
                        ft.Text(
                            "You are not logged in.",
                            color=ft.Colors.RED,
                        )
                    ]
                )

            attempts = (
                self.attempt_service
                .get_user_attempts(user_id)
            )

        except Exception as error:
            return ft.Column(
                [
                    ft.Text(
                        "Quiz History",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"Could not load history: {error}",
                        color=ft.Colors.RED,
                    ),
                ],
                spacing=15,
            )

        controls = [
            ft.Button(
                "← Back",
                on_click=self.go_back,
            ),
            ft.Text(
                "Quiz History",
                size=28,
                weight=ft.FontWeight.BOLD,
            ),
        ]

        if not attempts:
            controls.append(
                ft.Text(
                    "You haven't completed any quizzes yet."
                )
            )

        for attempt in attempts:
            quiz_data = attempt.get("quizzes")

            quiz_title = "Unknown Quiz"

            if quiz_data:
                quiz_title = quiz_data.get(
                    "title",
                    "Unknown Quiz",
                )            
            
            score = attempt.get("score", 0)
            total = attempt.get(
                "total_questions",
                0,
            )

            correct = attempt.get(
                "correct_answers",
                0,
            )

            completed_at = attempt.get(
                "completed_at",
                "",
            )

            percentage = 0

            if total:
                percentage = round(
                    (correct / total) * 100
                )

            controls.append(
                ft.Card(
                    content=ft.Container(
                        on_click=lambda e, a=attempt: self.review_attempt(a),
                        ink=True,
                        content=ft.Column(
                            [
                                ft.Text(
                                    quiz_title,
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"Score: {score} / {total} [{percentage}]%",
                                ),
                                ft.Text(
                                    (
                                        f"Time taken: "
                                        f"{attempt['time_taken_seconds'] // 60}:"
                                        f"{attempt['time_taken_seconds'] % 60:02d}"
                                    )
                                    if attempt.get("time_taken_seconds") is not None
                                    else "Time taken: N/A",
                                ),
                                ft.Text(
                                    f"Correct answers: {correct}",
                                ),
                                ft.Text(
                                    f"Completed: {completed_at}",
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
            spacing=15,
        )

    def go_back(self, e):
        self.on_back()