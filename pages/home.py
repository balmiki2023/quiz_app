import flet as ft
import asyncio
import threading
import time
import random

from services.quiz_service import QuizService
from services.subscription_service import SubscriptionService

class HomePage:
    def __init__(
        self,
        page: ft.Page,
        quiz_service: QuizService,
        subscription_service,
        local_db,
        on_profile,
        on_home,
        device_session_id,
    ):
        self.page = page
        self.quiz_service = quiz_service
        self.subscription_service = subscription_service
        self.local_db = local_db
        self.on_profile=on_profile
        self.on_home=on_home
        self.device_session_id=device_session_id
        
    def open_category(self, category_id, category_name):
        self.page.clean()

        quiz_page = QuizListPage(
            self.page,
            self.quiz_service,
            self.subscription_service,
            self.local_db,
            category_id,
            category_name,
            self.on_profile,
            self.on_home,
            self.device_session_id,
        )
        
        self.page.add(
            quiz_page.build()
        )
        
        self.page.update()


    def sync_data_in_background(self):
        def sync():
            start = time.time()
            print("BACKGROUND SYNC STARTED")

            try:
                self.quiz_service.sync_pending_data(
                    self.local_db
                )
            except Exception as error:
                print("BACKGROUND SYNC ERROR:", error)

            print(
                "BACKGROUND SYNC FINISHED IN:",
                round(time.time() - start, 2),
                "seconds"
            )

        threading.Thread(
            target=sync,
            daemon=True,
        ).start()

    def open_saved_questions(self, e):
        from pages.saved_questions import SavedQuestionsPage

        saved_page = SavedQuestionsPage(
            self.page,
            self.local_db,
            self.quiz_service,
            self.on_home,
        )

        self.page.clean()
        self.page.add(saved_page.build())
        self.page.update()

    def build(self):
        try:
            categories = self.quiz_service.get_categories()
        except Exception as error:
            return ft.Column(
                [
                    ft.Text("Quiz App", size=32),
                    ft.Text(
                        f"Could not load categories: {error}",
                        color=ft.Colors.RED,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )

        category_controls = []

        for category in categories:
            card_content = ft.Container(
                width=float("inf"),
                content=ft.Column(
                    [
                        ft.Text(
                            category["name"],
                            size=20,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            category.get("description")
                            or "Explore quizzes",
                        ),
                    ],
                    spacing=5,
                ),
                padding=15,
                on_click=lambda e, c=category: self.open_category(
                    c["id"],
                    c["name"],
                ),
                ink=True,
            )

            category_controls.append(
                ft.Card(
                    content=card_content,
                )
            )

        return ft.Container(
            expand=True,
            width=float("inf"),
            content=ft.Column(
                [
                    ft.Text(
                        "Quiz App",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Button(
                        "My Quiz History",
                        on_click=self.open_history,
                    ),
                    ft.Button(
                        "Profile",
                        on_click=self.open_profile,
                    ),
                    ft.Button(
                        "Saved Questions",
                        icon=ft.Icons.BOOKMARK,
                        on_click=self.open_saved_questions,
                    ),
                    ft.Text(
                        "Choose a Category",
                        size=22,
                    ),
                    ft.Column(
                        category_controls,
                        spacing=10,
                        width=float("inf"),
                    ),
                ],
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                width=float("inf"),
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

        
    def open_history(self, e=None):
        self.page.clean()

        from pages.results import ResultsPage

        results_page = ResultsPage(
            self.page,
            self.quiz_service,
            self.local_db,
            self.on_home,
        )

        self.page.add(
            results_page.build()
        )

        self.page.update()
    
    def open_profile(self, e):
        self.on_profile()
        
class QuizListPage:
    def __init__(
        self,
        page,
        quiz_service,
        subscription_service,
        local_db,
        category_id,
        category_name,
        on_profile,
        on_home,
        device_session_id,
    ):
        self.page = page
        self.quiz_service = quiz_service
        self.subscription_service = subscription_service
        self.local_db = local_db
        self.category_id = category_id
        self.category_name = category_name
        self.on_profile = on_profile
        self.on_home = on_home
        self.device_session_id=device_session_id
        self.question_count = 20
        self.question_filter = "all"

    def question_filter_changed(self, e):
        self.question_filter = e.control.value
        
    def on_back(self, e):
        self.page.clean()

        home_page = HomePage(
            self.page,
            self.quiz_service,
            self.subscription_service,
            self.local_db,
            self.on_profile,
            self.on_home,
            self.device_session_id,
        )

        self.page.add(home_page.build())

    def select_question_count(self, count):
        self.question_count = count
        self.page.controls.clear()
        self.page.add(self.build())
        self.page.update()

    def build(self):
        try:
            quizzes = self.quiz_service.get_quizzes(
                self.category_id
            )
        except Exception as error:
            return ft.Column(
                [
                    ft.Button(
                        "← Back",
                        on_click=self.on_back,
                    ),
                    ft.Text(
                        f"Could not load quizzes: {error}",
                        color=ft.Colors.RED,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )

        quiz_controls = []

        for quiz in quizzes:
            difficulty = quiz.get("difficulty") or "Not specified"

            time_limit = quiz.get("time_limit_seconds")

            if time_limit:
                minutes = time_limit // 60
                time_text = f"{minutes} min"
            else:
                time_text = "No time limit"

            premium_text = (
                "Premium"
                if quiz.get("is_premium")
                else "Free"
            )

            quiz_content = ft.Container(
                        width=float("inf"),
                        content=ft.Column(
                            [
                                ft.Text(
                                    quiz["title"],
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    quiz.get("description")
                                    or "No description",
                                ),
                                ft.Text(
                                    f"Difficulty: {difficulty}"
                                ),
                                ft.Text(
                                    f"Time: {time_text}"
                                ),
                                ft.Text(
                                    premium_text
                                ),
                            ],
                            spacing=5,
                        ),
                        padding=15,
                        on_click=lambda e, q=quiz: self.open_quiz(
                            q["id"],
                            q["title"],
                            q.get("time_limit_seconds"),
                            q.get("is_premium", False),
                        ),
                        ink=True,
                    )
            quiz_controls.append(
                ft.Card(
                    content=quiz_content,
                )
            )

        if not quiz_controls:
            quiz_controls.append(
                ft.Text(
                    "No published quizzes in this category yet."
                )
            )
            
        question_count_cards = ft.Row(
            [
                ft.Container(
                    content=ft.Text(
                        str(count),
                        color=(
                            ft.Colors.WHITE
                            if self.question_count == count
                            else ft.Colors.ON_SURFACE
                        ),
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                    width=65,
                    height=60,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=(
                        ft.Colors.BLUE_900
                        if self.question_count == count
                        else ft.Colors.SURFACE
                    ),
                    border=ft.Border.all(
                        2 if self.question_count == count else 1,
                        ft.Colors.BLUE
                        if self.question_count == count
                        else ft.Colors.OUTLINE,
                    ),
                    border_radius=10,
                    on_click=lambda e, c=count: self.select_question_count(c),
                    ink=True,
                )
                for count in (10, 20, 30, 40)
            ],
            spacing=10,
        )

        # Check membership status
        is_premium = self.subscription_service.is_premium()

        question_filter_controls = []

        if is_premium:
            question_filter_dropdown = ft.Dropdown(
                label="Question selection",
                value=self.question_filter,
                options=[
                    ft.DropdownOption(
                        key="all",
                        text="All questions",
                    ),
                    ft.DropdownOption(
                        key="attempted",
                        text="Attempted questions",
                    ),
                    ft.DropdownOption(
                        key="not_attempted",
                        text="Non-attempted questions",
                    ),
                ],
                on_select=self.question_filter_changed,
            )

            question_filter_controls = [
                question_filter_dropdown,
            ]

        else:
            question_filter_controls = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Free Membership",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Only 40 questions available for this category."
                            ),
                            ft.Text(
                                "Upgrade to Premium to access the full "
                                "question bank and try new questions."
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=12,
                    border=ft.Border.all(
                        1,
                        ft.Colors.OUTLINE,
                    ),
                    border_radius=10,
                ),
            ]
        
        start_quiz_button = ft.Button(
            "Start Quiz",
            on_click=self.start_quiz,
        )

        return ft.Container(
            expand=True,
            width=float("inf"),
            content=ft.Column(
                [
                    ft.Button(
                        "← Back",
                        on_click=self.on_back,
                    ),

                    ft.Text(
                        self.category_name,
                        size=28,
                        weight=ft.FontWeight.BOLD,
                    ),

                    ft.ResponsiveRow(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        *question_filter_controls,
                                    ],
                                    spacing=10,
                                ),
                                col={"xs": 12, "md": 5},
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            "Number of questions:",
                                            size=14,
                                        ),
                                        question_count_cards,
                                    ],
                                    spacing=10,
                                ),
                                col={"xs": 12, "md": 7},
                            ),
                        ],
                        spacing=15,
                        run_spacing=15,
                    ),

                    start_quiz_button,

                    ft.Text(
                        "Available Quizzes",
                        size=20,
                    ),

                    ft.Column(
                        quiz_controls,
                        spacing=10,
                        width=float("inf"),
                    ),
                ],
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                width=float("inf"),
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )
        
            
    def start_quiz(self, e):
        is_premium = self.subscription_service.is_premium()

        attempted_ids = []

        if is_premium and self.question_filter in (
            "attempted",
            "not_attempted",
        ):
            attempted_ids = (
                self.local_db.get_attempted_question_ids(
                    self.category_id
                )
            )

        questions = self.quiz_service.get_random_questions(
            category_id=self.category_id,
            num_questions_show=self.question_count,
            question_filter=(
                self.question_filter if is_premium else "all"
            ),
            is_premium=is_premium,
            attempted_ids=attempted_ids,
        )

        # Case 1: No questions available
        if not questions:
            if self.question_filter == "not_attempted":
                message = (
                    "You have already attempted all questions "
                    "in this category."
                )
            elif self.question_filter == "attempted":
                message = (
                    "You haven't attempted any questions "
                    "in this category yet."
                )
            else:
                message = "No questions are currently available."

            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("No questions available"),
                    content=ft.Text(message),
                )
            )
            return

        # Case 2: Fewer questions than requested
        available_count = len(questions)

        content = self._build_quiz_page(
            quiz_id=None,
            quiz_title=f"{self.category_name} — Random Quiz",
            time_limit_seconds=available_count * 20,
            questions=questions,
            category_id=self.category_id,
        )

        if content is not None:
            self.page.clean()
            self.page.add(content)
            self.page.update()

            if available_count < self.question_count:
                self.page.show_dialog(
                    ft.AlertDialog(
                        title=ft.Text("Fewer questions available"),
                        content=ft.Text(
                            f"You requested {self.question_count} "
                            f"questions, but only {available_count} "
                            "are available. Your quiz will start "
                            "with the available questions."
                        ),
                    )
                )        

    def open_quiz(
        self,
        quiz_id,
        quiz_title,
        time_limit_seconds,
        is_premium=False,
    ):
        if is_premium:
            user_is_premium = (
                self.subscription_service.is_premium()
                and self.subscription_service.claim_device_session(
                    self.device_session_id
                )
            )

            if not user_is_premium:
                self.page.clean()

                self.page.add(
                    ft.Column(
                        [
                            ft.Text(
                                "Premium Quiz",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "This quiz is available to Premium members."
                            ),
                            ft.Button(
                                "← Back",
                                on_click=self.on_back,
                            ),
                        ],
                        spacing=15,
                    )
                )

                self.page.update()
                return

        try:
            questions = self.quiz_service.get_questions(quiz_id)

            if self.question_count is not None:
                questions = questions[:self.question_count]

            content = self._build_quiz_page(
                quiz_id=quiz_id,
                quiz_title=quiz_title,
                time_limit_seconds=time_limit_seconds,
                questions=questions,
            )

            if content is None:
                return

            self.page.clean()
            self.page.add(content)
            self.page.update()

        except Exception as error:
            self.page.clean()

            self.page.add(
                ft.Column(
                    [
                        ft.Text(
                            "Error opening quiz",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            str(error),
                            color=ft.Colors.RED,
                        ),
                        ft.Button(
                            "← Back",
                            on_click=self.on_back,
                        ),
                    ]
                )
            )

            self.page.update()

    def _build_quiz_page(
        self,
        quiz_id,
        quiz_title,
        time_limit_seconds,
        questions,
        category_id=None,
    ):
        if not questions:
            return None

        question_ids = [
            question["id"]
            for question in questions
        ]

        question_correct_rates = (
            self.quiz_service.get_question_correct_rates(
                question_ids
            )
        )


        quiz_page = QuizPage(
            self.page,
            self.quiz_service,
            self.subscription_service,
            self.local_db,
            quiz_id,
            quiz_title,
            time_limit_seconds,
            self.on_profile,
            self.on_home,
            self.device_session_id,
            self.question_count,
            category_id=category_id,
            questions=questions,
            question_correct_rates=question_correct_rates,
        )

        return quiz_page.build()
        
    
class QuizPage:
    def __init__(
        self,
        page,
        quiz_service,
        subscription_service,
        local_db,
        quiz_id,
        quiz_title,
        time_limit_seconds,
        on_profile,
        on_home,
        device_session_id,
        question_count,
        category_id=None,
        questions=None,
        question_correct_rates=None
    ):
        self.page = page
        self.quiz_service = quiz_service
        self.subscription_service = subscription_service
        self.local_db = local_db
        self.quiz_id = quiz_id
        self.quiz_title = quiz_title
        self.time_limit_seconds = time_limit_seconds
        self.on_profile = on_profile
        self.on_home = on_home
        self.device_session_id = device_session_id
        self.question_count = question_count
        self.category_id = category_id
        self.questions = questions or []
        self.question_correct_rates = question_correct_rates or {}
        

        
        self.remaining_seconds = time_limit_seconds
        self.time_taken_seconds = None
        self.timer = None
        self.timer_started = False
        
        self.timer_text = ft.Text(
            "",
            size=18,
            weight=ft.FontWeight.BOLD,
        )

        self.current_question_index = 0
        self.score = 0
        self.selected_answer = None

        # Keep track of every answer selected
        self.selected_answers = []
        self.attempt_id = None

        self.question_save_states = {}
        self.save_button = None
        self.save_count_text = ft.Text("0", size=14)
        self.current_attempt_correct = None
        self.option_orders = {}

    def get_question_save_state(self, question_id):
        question_id = str(question_id)

        if question_id in self.question_save_states:
            return self.question_save_states[question_id]

        try:
            is_saved = self.local_db.is_question_saved(question_id)

            self.question_save_states[question_id] = is_saved

            return is_saved

        except Exception as error:
            print("Could not load saved question state:", error)
            return False


    
    def toggle_question_save(self, question_id, button, count_text):
        try:
            is_saved = self.local_db.toggle_question_save(question_id)

            # Maximum saved-question limit reached.
            if is_saved is None:
                self.save_limit_message.value = (
                    "Save max. limit reached. Remove some saved questions."
                )
                self.save_limit_message.visible = True
                self.page.update()
                return

            # Clear any previous limit message.
            self.save_limit_message.value = ""
            self.save_limit_message.visible = False

            self.question_save_states[str(question_id)] = is_saved

            button.icon = (
                ft.Icons.BOOKMARK
                if is_saved
                else ft.Icons.BOOKMARK_BORDER
            )

            button.icon_color = (
                ft.Colors.BLUE
                if is_saved
                else ft.Colors.GREY
            )

            button.tooltip = (
                "Remove saved question"
                if is_saved
                else "Save question"
            )

            count_text.value = "1" if is_saved else "0"

            self.page.update()

        except Exception as error:
            print("Could not update saved question:", error)

    
    def load_questions(self):
        if self.question_count is not None:
            self.questions = self.questions[:self.question_count]

        question_ids = [
            question["id"]
            for question in self.questions
        ]

    def select_answer(self, question, option_key):
        is_correct = (
            option_key == question.get("correct_option")
        )

        # Remove the previous selection's score, if any.
        if self.selected_answer is not None:
            if self.selected_answer["is_correct"]:
                self.score -= 1

        self.current_attempt_correct = is_correct

        self.selected_answer = {
            "option": option_key,
            "is_correct": is_correct,
        }

        # Update score immediately.
        if is_correct:
            self.score += 1

        question_id = question.get("id")

        try:
            self.local_db.record_first_attempt(
                question_id=question_id,
                category_id=question.get("category_id") or self.category_id,
                selected_answer=option_key,
                is_correct=is_correct,
            )

            self.local_db.record_question_history(
                question_id=question_id,
                selected_answer=option_key,
                is_correct=is_correct,
            )

        except Exception as error:
            print(f"LOCAL QUESTION ATTEMPT ERROR: {error}")

        self.page.clean()
        self.page.add(self.build())
        self.page.update()
            

    def next_question(self, e=None):

        if self.selected_answer is None:
            return

        self.record_current_answer()

        self.current_question_index += 1


        self.current_attempt_correct = None
        self.selected_answer = None

        if self.current_question_index >= len(self.questions):
            self.save_attempt()
            return

        self.page.clean()
        self.page.add(self.build())
        self.page.update()
        
            
    async def start_timer(self):
        if self.time_limit_seconds is None:
            return

        while self.remaining_seconds > 0:
            await asyncio.sleep(1)

            if self.remaining_seconds <= 0:
                break

            self.remaining_seconds -= 1

            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60

            self.timer_text.value = (
                f"Time remaining: {minutes}:{seconds:02d}"
            )

            self.timer_text.update()

        if self.remaining_seconds <= 0:
            self.remaining_seconds = 0

            self.timer_text.value = "Time remaining: 0:00"
            self.timer_text.update()

            if self.timer:
                self.timer = None

            self.save_timeout_attempt()
    
    def save_timeout_attempt(self):
        try:
            answered_map = {
                answer["question_id"]: answer
                for answer in self.selected_answers
            }

            # Include the current question if an option was selected.
            if self.selected_answer is not None:
                question = self.questions[
                    self.current_question_index
                ]

                answered_map[question["id"]] = {
                    "question_id": question["id"],
                    "selected_option": self.selected_answer["option"],
                    "is_correct": self.selected_answer["is_correct"],
                }

            timeout_answers = []

            for question in self.questions:
                saved_answer = answered_map.get(
                    question["id"]
                )

                if saved_answer:
                    timeout_answers.append(saved_answer)
                else:
                    timeout_answers.append(
                        {
                            "question_id": question["id"],
                            "selected_option": None,
                            "is_correct": False,
                        }
                    )

            self.selected_answers = timeout_answers

            self.save_attempt()

        except Exception as error:
            self.show_save_error(str(error))
            
    
    def save_attempt(self):
        self.time_taken_seconds = (
            self.time_limit_seconds - self.remaining_seconds
            if self.time_limit_seconds is not None
            else None
        )

        # First, save the attempt locally.
        try:
            print("SAVING ATTEMPT...")
            self.attempt_id = self.local_db.create_attempt(
                user_id=None,
                quiz_id=self.quiz_id,
                quiz_title=self.quiz_title,
                category_id=self.category_id,
                score=self.score,
                total_questions=len(self.questions),
                correct_answers=self.score,
                time_taken_seconds=self.time_taken_seconds,
                answers=self.selected_answers,
            )

            print("LOCAL QUIZ ATTEMPT SAVED:", self.attempt_id)

        except Exception as error:
            self.attempt_id = None
            print("LOCAL QUIZ ATTEMPT ERROR:", repr(error))

        # Synchronization is independent of local saving.
        if self.attempt_id is not None:
            try:
                self.quiz_service.sync_pending_data(self.local_db)
            except Exception as error:
                print("BACKGROUND SYNC ERROR:", repr(error))

        self.show_result()

            
    def show_save_error(self, error):
        self.page.clean()

        self.page.add(
            ft.Column(
                [
                    ft.Text(
                        "Quiz Complete",
                        size=30,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"Score: {self.score} / "
                        f"{len(self.questions)}",
                        size=24,
                    ),
                    ft.Text(
                        "Could not save your attempt.",
                        color=ft.Colors.RED,
                    ),
                    ft.Text(
                        str(error),
                        size=12,
                    ),
                ],
                spacing=15,
            )
        )

    def get_shuffled_options(self, question):
        question_id = str(question["id"])

        if question_id not in self.option_orders:
            original_options = [
                ("A", question.get("option_a", "")),
                ("B", question.get("option_b", "")),
                ("C", question.get("option_c", "")),
                ("D", question.get("option_d", "")),
            ]

            random.shuffle(original_options)

            self.option_orders[question_id] = [
                (display_key, original_key, option_text)
                for display_key, (original_key, option_text)
                in zip(["A", "B", "C", "D"], original_options)
            ]

        return self.option_orders[question_id]

    def open_saved_review(self):
        if self.attempt_id is None:
            return

        from pages.results import ResultsPage

        results_page = ResultsPage(
            self.page,
            self.quiz_service,
            self.local_db,
            self.on_home,
        )

        results_page.review_back_callback = self.back_to_result

        results_page.review_attempt({
            "id": self.attempt_id
        })

    def show_result(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None  

        if self.selected_answer is not None:
            self.record_current_answer()
            self.selected_answer = None
            
        total = len(self.questions)

        percentage = 0

        if total:
            percentage = round(
                (self.score / total) * 100
            )

        answered = sum(
            1 for answer in self.selected_answers
            if answer.get("selected_option") is not None
        )

        not_answered = total - answered
        incorrect = answered - self.score
        
        time_taken = (
            self.time_limit_seconds - self.remaining_seconds
            if self.time_limit_seconds is not None
            else None
        )

        self.page.clean()

        result_content = ft.Column(
            [
                ft.Text(
                    "Quiz Complete!",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Text(
                    self.quiz_title,
                    size=24,
                ),
                ft.Divider(),

                ft.Text(
                    f"{percentage}%",
                    size=42,
                    weight=ft.FontWeight.BOLD,
                ),
                
                ft.Text(
                    (
                        f"Time taken: "
                        f"{self.time_taken_seconds // 60}:"
                        f"{self.time_taken_seconds % 60:02d}"
                    )
                    if self.time_taken_seconds is not None
                    else "Time taken: N/A",
                    size=20,
                ),

                ft.Text(
                    f"Score: {self.score} / {total}",
                    size=24,
                ),

                ft.Row(
                    [
                        ft.Text(
                            f"Incorrect: {incorrect}",
                            size=18,
                        ),
                        ft.Text(
                            f"Not Answered: {not_answered}",
                            size=18,
                        ),
                    ],
                    spacing=30,
                ),

                ft.Divider(),

                ft.Text(
                    (
                        "Your result has been saved."
                        if self.attempt_id is not None
                        else "Your result could not be saved."
                    ),
                    color=(
                        ft.Colors.GREEN
                        if self.attempt_id is not None
                        else ft.Colors.RED
                    ),
                ),

                ft.Button(
                    "Try Again",
                    on_click=self.try_again,
                ),
                ft.Button(
                    "Review Answers",
                    on_click=lambda e: self.open_saved_review(),
                ),

                ft.Button(
                    "View Quiz History",
                    on_click=self.view_history,
                ),
                ft.Button(
                    "← Back to Home",
                    on_click= self.back_to_home,
                ),
            ],
            spacing=15,
        )

        self.page.add(
            ft.Column(
                [
                    ft.Container(
                        content=result_content,
                        width=500,
                        padding=30,
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        )

        self.page.update()
        
    
    
    def try_again(self, e=None):
        if self.timer:
            self.timer.cancel()
            self.timer = None

        # Reset attempt identity
        self.attempt_id = None

        # Reset timer
        self.remaining_seconds = self.time_limit_seconds
        self.timer_started = False
        self.time_taken_seconds = None

        # Reset quiz progress
        self.current_question_index = 0
        self.score = 0
        self.selected_answer = None
        self.selected_answers = []
        self.current_attempt_correct = None

        self.page.clean()
        self.page.add(self.build())
        self.page.update()

    
    def view_history(self, e=None):
        self.page.clean()

        from pages.results import ResultsPage

        # Keep the current Results page so we can return to it.
        results_page = ResultsPage(
            self.page,
            self.quiz_service,
            self.local_db,
            self.show_result,
        )
        self.page.update()

        def back_to_results():
            self.page.clean()
            self.page.add(results_page.build())
            self.page.update()

        results_page.on_history = back_to_results

        self.page.add(results_page.build())
        self.page.update()
        
    def back_to_home(self, e=None):
        if self.timer:
            self.timer.cancel()
            self.timer = None

        self.on_home()

    
    def build_question_attempt_indicator(self, question_id):
        if not question_id:
            return None

        try:
            history = self.local_db.get_question_attempt_history(
                question_id
            )

            # If the current answer has been selected,
            # exclude its newly saved database record.
            if self.current_attempt_correct is not None:
                history = history[1:]

            # Keep four previous attempts.
            history = history[:4]

            # Display oldest attempt on the left,
            # most recent previous attempt on the right.
            history = list(reversed(history))

            indicators = [
                ft.Icon(
                    ft.Icons.CHECK_CIRCLE
                    if attempt["is_correct"]
                    else ft.Icons.CANCEL,
                    color=(
                        ft.Colors.GREEN
                        if attempt["is_correct"]
                        else ft.Colors.RED
                    ),
                    size=18,
                )
                for attempt in history
            ]

            # Empty indicator for the current attempt.
            if self.current_attempt_correct is None:
                current_indicator = ft.Icon(
                    ft.Icons.CIRCLE_OUTLINED,
                    color=ft.Colors.GREY,
                    size=18,
                )
            else:
                current_indicator = ft.Icon(
                    ft.Icons.CHECK_CIRCLE_OUTLINE
                    if self.current_attempt_correct
                    else ft.Icons.CANCEL_OUTLINED,
                    color=(
                        ft.Colors.GREEN
                        if self.current_attempt_correct
                        else ft.Colors.RED
                    ),
                    size=18,
                )
            return ft.Row(
                [
                    ft.Text("Attempts:", size=12),
                    *indicators,
                    current_indicator,
                ],
                spacing=5,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        except Exception as error:
            print(f"Error loading question history: {error}")
            return None

    def record_current_answer(self):
        if self.selected_answer is None:
            return

        question = self.questions[self.current_question_index]

        self.selected_answers.append({
            "question_id": question["id"],
            "selected_option": self.selected_answer["option"],
            "is_correct": self.selected_answer["is_correct"],
        })
    
    def build(self):
        if not self.questions:
            try:
                self.load_questions()
            except Exception as error:
                return ft.Container(
                    expand=True,
                    content=ft.Column(
                        [
                            ft.Text(
                                self.quiz_title,
                                size=28,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                f"Could not load questions: {error}",
                                color=ft.Colors.RED,
                            ),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                )

        if not self.questions:
            return ft.Container(
                expand=True,
                content=ft.Column(
                    [
                        ft.Button(
                            "← Back",
                            on_click=self.on_back,
                        ),
                        ft.Text(
                            self.quiz_title,
                            size=28,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "This quiz does not have any questions yet."
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            )

        question = self.questions[
            self.current_question_index
        ]
        
        options = [
            ("A", question.get("option_a")),
            ("B", question.get("option_b")),
            ("C", question.get("option_c")),
            ("D", question.get("option_d")),
        ]

        if self.remaining_seconds is not None:
            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60

            self.timer_text.value = (
                f"Time remaining: {minutes}:{seconds:02d}"
            )
        else:
            self.timer_text.value = "No time limit"
        
        controls = [
            ft.Row(
                controls=[
                    ft.Text(
                        self.quiz_title,
                        size=28,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"[ {self.current_question_index + 1}"
                        f" / {len(self.questions)} ]",
                        size=18,
                    ),
                ],
                wrap=True,
            ),
            self.timer_text,
            ft.Text(
                question["question_text"],
                size=22,
                weight=ft.FontWeight.BOLD,
            ),
        ]
        # Get the current question ID
        question_id = question.get("id")

        correct_rate = self.question_correct_rates.get(
            question_id
        )

        row_controls = []

        if correct_rate is not None:
            row_controls.append(
                ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.BAR_CHART,
                            size=16,
                            color=ft.Colors.GREEN,
                            tooltip="Percentage of users who answered this question correctly",
                        ),
                        ft.Text(
                            f"{correct_rate * 100:.1f}%",
                            size=14,
                            color=ft.Colors.GREEN,
                        ),
                    ],
                    spacing=4,
                )
            )

        history_indicator = (
            self.build_question_attempt_indicator(
                question_id
            )
        )

        if row_controls or history_indicator is not None:
            controls.append(
                ft.Row(
                    controls=[
                        *row_controls,
                        *(
                            [history_indicator]
                            if history_indicator is not None
                            else []
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    wrap=False,
                    tight=True,
                )
            )
        
        if question_id is not None:
            save_count = 1 if self.local_db.is_question_saved(question_id) else 0
            save_count_text = ft.Text(str(save_count), size=14)

            is_saved = self.get_question_save_state(question_id)

            save_button = ft.IconButton(
                icon=(
                    ft.Icons.BOOKMARK
                    if is_saved
                    else ft.Icons.BOOKMARK_BORDER
                ),
                icon_color=(
                    ft.Colors.BLUE
                    if is_saved
                    else ft.Colors.GREY
                ),
                tooltip=(
                    "Remove saved question"
                    if is_saved
                    else "Save question"
                ),
            )

            save_button.on_click = lambda e, qid=question_id, btn=save_button, count=save_count_text: (
                self.toggle_question_save(qid, btn, count)
            )
            self.save_limit_message = ft.Text(
                "",
                color=ft.Colors.RED,
                size=12,
                visible=False,
            )

            controls.append(
                ft.Column(
                    [
                        ft.Row(
                            [
                                save_button,
                                save_count_text,
                            ],
                            spacing=5,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        self.save_limit_message,
                    ],
                    spacing=3,
                )
            )

        options = self.get_shuffled_options(question)

        for display_key, original_key, option_text in options:

            is_selected = (
                self.selected_answer is not None
                and self.selected_answer["option"] == original_key
            )

            is_correct_option = (
                original_key == question.get("correct_option")
            )

            if self.selected_answer is not None and is_correct_option:
                border_color = ft.Colors.GREEN
            elif is_selected and not self.selected_answer["is_correct"]:
                border_color = ft.Colors.RED
            else:
                border_color = ft.Colors.OUTLINE

            option_container = ft.Container(
                content=ft.Text(
                    f"{display_key}. {option_text}",
                    size=18,
                ),
                padding=15,
                border=ft.Border.all(
                    2 if is_selected or (
                        self.selected_answer is not None
                        and is_correct_option
                    ) else 1,
                    border_color,
                ),
                border_radius=10,
                on_click=(
                    None
                    if self.selected_answer is not None
                    else lambda e, key=original_key:
                        self.select_answer(question, key)
                ),
                ink=True,
            )
            controls.append(
                option_container
            )

        # Explanation
        explanation = question.get("explanation")

        if explanation and self.selected_answer is not None:
            controls.append(
                ft.Container(
                    content=ft.Text(
                        explanation,
                        size=17,
                        selectable=True,
                    ),
                    width=float("inf"),
                    padding=15,
                    border_radius=10,
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                )
            )
        
        # Navigation button
        if self.current_question_index == len(self.questions) - 1:
            navigation_button = ft.Button(
                "Show Result",
                icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                disabled=self.selected_answer is None,
                on_click=self.next_question,
            )
        else:
            navigation_button = ft.Button(
                "Next Question",
                icon=ft.Icons.ARROW_FORWARD,
                disabled=self.selected_answer is None,
                on_click=self.next_question,
            )

        controls.append(navigation_button)
        
        if not self.timer_started:
            self.timer_started = True
            self.timer = self.page.run_task(
                self.start_timer
            )
            
        return ft.Container(
            expand=True,
            width=float("inf"),
            content=ft.Column(
                controls,
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                width=float("inf"),
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )
    
    def back_to_result(self, e=None):
        self.show_result()