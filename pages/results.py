import flet as ft

class ResultsPage:
    def __init__(
        self,
        page,
        quiz_service,
        local_db,
        on_back,
        on_history_back=None,
    ):
        self.page = page
        self.quiz_service = quiz_service
        self.local_db = local_db
        self.on_back = on_back
        self.on_history_back = on_history_back
        self.review_back_callback = None

        self.current_page = 0
        
    def get_random_quiz_title(self, attempt):
        try:
            saved_answers = attempt.get("answers") or []

            question_ids = [
                answer.get("question_id")
                for answer in saved_answers
                if answer.get("question_id")
            ]

            if not question_ids:
                return "Random Quiz"

            questions = self.quiz_service.get_questions_by_ids(
                question_ids
            )

            if not questions:
                return "Random Quiz"

            category_id = questions[0].get("category_id")

            if not category_id:
                return "Random Quiz"

            response = (
                self.quiz_service.supabase
                .table("categories")
                .select("name")
                .eq("id", str(category_id))
                .limit(1)
                .execute()
            )

            if response.data:
                category_name = response.data[0].get("name")

                if category_name:
                    return f"{category_name} — Random Quiz"

        except Exception:
            # A missing category label should not prevent displaying the result.
            pass

        return "Random Quiz"
    
    def review_attempt(self, attempt):
        try:
            attempt_id = attempt["id"]

            full_attempt = (
                self.local_db
                .get_attempt(attempt_id)
            )

            if not full_attempt:
                raise Exception(
                    "Could not find this quiz attempt."
                )

            saved_answers = (
                full_attempt.get("answers") or []
            )

            question_ids = [
                answer["question_id"]
                for answer in saved_answers
                if answer.get("question_id")
            ]

            if full_attempt.get("quiz_id"):
                questions = (
                    self.quiz_service
                    .get_questions(
                        full_attempt["quiz_id"]
                    )
                )
            else:
                questions = (
                    self.quiz_service
                    .get_questions_by_ids(
                        question_ids
                    )
                )

            answer_map = {
                answer["question_id"]: answer
                for answer in saved_answers
            }

            quiz_data = full_attempt.get("quizzes")

            quiz_title = "Unknown Quiz"

            if quiz_data:
                quiz_title = quiz_data.get(
                    "title",
                    "Unknown Quiz",
                )
            else:
                quiz_title = self.get_random_quiz_title(
                    full_attempt
                )

            score = full_attempt.get("score", 0)
            total = full_attempt.get(
                "total_questions",
                0,
            )

            controls = [
                ft.Button(
                    "← Back",
                    on_click=(
                        self.review_back_callback
                        if self.review_back_callback
                        else self.back_to_history
                    ),
                ),

                ft.Text(
                    "Review Answers",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Text(
                    quiz_title,
                    size=22,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Text(
                    f"Score: {score} / {total}",
                    size=20,
                ),
            ]

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
                        f"{option_text}"
                    )
                else:
                    selected_answer_text = "Not answered"

                question_controls = [
                    ft.Text(
                        f"{index}. "
                        f"{question['question_text']}",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(
                                selected_answer_text,
                                color=(
                                    ft.Colors.GREY_600
                                    if selected_option is None
                                    else ft.Colors.with_opacity(
                                        1,
                                        ft.Colors.ON_SURFACE,
                                    )
                                ),
                            ),
                            *(
                                [
                                    ft.Icon(
                                        ft.Icons.CHECK_CIRCLE
                                        if is_correct
                                        else ft.Icons.CANCEL,
                                        color=(
                                            ft.Colors.GREEN
                                            if is_correct
                                            else ft.Colors.RED
                                        ),
                                    )
                                ]
                                if selected_option is not None
                                else []
                            ),
                        ]
                    ),
                ]

                explanation = question.get(
                                    "explanation"
                                )
                
                if (
                    selected_option is not None
                    and explanation
                ):
                    question_controls.append(
                        ft.Text(
                            f"Explanation: {explanation}"
                        )
                    )

                controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                question_controls,
                                spacing=8,
                            ),
                            padding=15,
                            width=float("inf"),
                        )
                    )
                )

            self.page.clean()
            controls.append(
                ft.Button(
                    "← Back",
                    on_click=(
                        self.review_back_callback
                        if self.review_back_callback
                        else self.back_to_history
                    ),
                )
            )

            review_content = ft.Column(
                controls,
                spacing=15,
                width=float("inf"),
            )

            self.page.add(
                ft.Column(
                    [
                        ft.Container(
                            content=review_content,
                            width=float("inf"),
                            padding=20,
                        )
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                )
            )

            self.page.update()
        except Exception as error:
            self.page.clean()

            self.page.add(
                ft.Container(
                    expand=True,
                    width=float("inf"),
                    content=ft.Column(
                        [
                            ft.Button(
                                "← Back to History",
                                on_click=self.back_to_history,
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
                        scroll=ft.ScrollMode.AUTO,
                    ),
                )
            )

            self.page.update()
            

    def previous_page(self, e=None):
        if self.current_page > 0:
            self.current_page -= 1
            self.page.clean()
            self.page.add(self.build())
            self.page.update()


    def next_page(self, e=None):
        self.current_page += 1
        self.page.clean()
        self.page.add(self.build())
        self.page.update()
    
    def build(self):
        try:
            attempts = self.local_db.get_user_attempts(
                page=self.current_page,
                page_size=11,
            )

            has_next_page = len(attempts) > 10
            attempts = attempts[:10]

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

        history_cards = []

        for attempt in attempts:

            # Get quiz title
            quiz_id = attempt.get("quiz_id")

            quiz_title = attempt.get("quiz_title") or (
                "Random Quiz"
                if not attempt.get("quiz_id")
                else "Unknown Quiz"
            )

            score = attempt.get("score", 0)
            total = attempt.get("total_questions", 0)
            correct = attempt.get("correct_answers", 0)

            completed_at = attempt.get("completed_at", "")

            percentage = 0

            if total:
                percentage = round((correct / total) * 100)

            time_taken = attempt.get("time_taken_seconds")

            if time_taken is not None:
                minutes = time_taken // 60
                seconds = time_taken % 60
                time_text = f"Time taken: {minutes}:{seconds:02d}"
            else:
                time_text = "Time taken: N/A"

            history_cards.append(
            ft.Card(
                content=ft.Container(
                    on_click=lambda e, a=attempt: self.review_attempt(a),
                    ink=True,
                    content=ft.Column(
                        [
                            ft.Text(
                                quiz_title,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(f"Score: {score} / {total} [{percentage}%]"),
                            ft.Text(time_text),
                            ft.Text(f"Completed: {completed_at}"),
                        ],
                        spacing=5,
                    ),
                    padding=15,
                )
            )
        )

        controls.append(
            ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=card,
                        col={
                            "xs": 12,  # Mobile: full width
                            "md": 6,   # Tablet and desktop: half width
                        },
                    )
                    for card in history_cards
                ],
                spacing=15,
                run_spacing=15,
            )
        )

        controls.append(
            ft.Row(
                [
                    ft.Button(
                        "Previous",
                        disabled=self.current_page == 0,
                        on_click=self.previous_page,
                    ),
                    ft.Text(f"Page {self.current_page + 1}"),
                    ft.Button(
                        "Next",
                        disabled=not has_next_page,
                        on_click=self.next_page,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )
        return ft.Container(
            expand=True,
            width=float("inf"),
            content=ft.ListView(
                controls=controls,
                spacing=15,
                expand=True,
                width=float("inf"),
                padding=20,
            ),
        )

    def go_back(self, e=None):
        self.on_back()

    def back_to_history(self, e=None):
        self.page.clean()
        self.page.add(self.build())
        self.page.update()