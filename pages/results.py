import flet as ft


class ResultsPage:
    def __init__(
        self,
        page,
        attempt_service,
        quiz_service,
        on_back,
        on_history_back=None,
    ):
        self.page = page
        self.attempt_service = attempt_service
        self.quiz_service = quiz_service
        self.on_back = on_back
        self.on_history_back = on_history_back
        
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

        except Exception as error:
            print(
                "RANDOM QUIZ TITLE ERROR:",
                error,
            )

        return "Random Quiz"
    
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
                    "← Back to History",
                    on_click=self.back_to_history,
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
                        f"{selected_option}. "
                        f"{option_text}"
                    )
                else:
                    selected_answer_text = "Not answered"

                status = (
                    "Correct"
                    if is_correct
                    else "Incorrect"
                )

                explanation = question.get(
                    "explanation"
                )

                question_controls = [
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
                        f"Status: {status}"
                    ),
                ]

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

            review_content = ft.Column(
                controls,
                spacing=15,
                width=float("inf"),
            )

            self.page.add(
                ft.Container(
                    content=review_content,
                    width=float("inf"),
                    padding=20,
                )
            )

            self.page.scroll = ft.ScrollMode.AUTO
            self.page.update()
            self.page.run_task(self.reset_scroll)

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
            
    async def reset_scroll(self):
        await self.page.scroll_to(
            offset=0,
            duration=0,
        )
    
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

            # 1. Load all attempts with ONE query
            attempts = (
                self.attempt_service
                .get_user_attempts(user_id)
            )

            # 2. Load categories ONCE
            categories_response = (
                self.quiz_service.supabase
                .table("categories")
                .select("id, name")
                .execute()
            )

            categories = (
                categories_response.data or []
            )

            category_map = {
                str(category["id"]): category["name"]
                for category in categories
            }

            # 3. Collect question IDs only for old
            #    random attempts that have no category_id.
            legacy_question_ids = set()

            for attempt in attempts:
                if attempt.get("quizzes"):
                    continue

                if attempt.get("category_id"):
                    continue

                answers = attempt.get("answers") or []

                for answer in answers:
                    question_id = answer.get("question_id")

                    if question_id:
                        legacy_question_ids.add(
                            str(question_id)
                        )

            # 4. One batch query for legacy random attempts
            legacy_questions = {}

            if legacy_question_ids:
                questions = (
                    self.quiz_service
                    .get_questions_by_ids(
                        list(legacy_question_ids)
                    )
                )

                legacy_questions = {
                    str(question["id"]): question
                    for question in questions
                }

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

            # Normal quiz
            if quiz_data:
                quiz_title = quiz_data.get(
                    "title",
                    "Unknown Quiz",
                )

            # Random quiz
            else:
                category_id = attempt.get(
                    "category_id"
                )

                # New random attempts
                if category_id:
                    category_name = category_map.get(
                        str(category_id),
                        "Unknown Category",
                    )

                    quiz_title = (
                        f"{category_name} — Random Quiz"
                    )

                # Old random attempts
                else:
                    category_name = None

                    answers = (
                        attempt.get("answers") or []
                    )

                    for answer in answers:
                        question_id = answer.get(
                            "question_id"
                        )

                        if not question_id:
                            continue

                        question = legacy_questions.get(
                            str(question_id)
                        )

                        if question:
                            category_id = question.get(
                                "category_id"
                            )

                            if category_id:
                                category_name = (
                                    category_map.get(
                                        str(category_id)
                                    )
                                )

                                if category_name:
                                    break

                    if category_name:
                        quiz_title = (
                            f"{category_name} — Random Quiz"
                        )
                    else:
                        quiz_title = "Random Quiz"

            score = attempt.get(
                "score",
                0,
            )

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
                        on_click=lambda e, a=attempt:
                            self.review_attempt(a),
                        ink=True,
                        content=ft.Column(
                            [
                                ft.Text(
                                    quiz_title,
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"Score: {score} / "
                                    f"{total} "
                                    f"[{percentage}]%",
                                ),
                                ft.Text(
                                    (
                                        f"Time taken: "
                                        f"{attempt['time_taken_seconds'] // 60}:"
                                        f"{attempt['time_taken_seconds'] % 60:02d}"
                                    )
                                    if attempt.get(
                                        "time_taken_seconds"
                                    ) is not None
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