import flet as ft
import asyncio

from services.quiz_service import QuizService
from services.subscription_service import SubscriptionService


class HomePage:
    def __init__(
        self,
        page: ft.Page,
        quiz_service: QuizService,
        attempt_service,
        subscription_service,
        on_profile,
        device_session_id,
    ):
        self.page = page
        self.quiz_service = quiz_service
        self.attempt_service = attempt_service
        self.subscription_service = subscription_service
        self.on_profile=on_profile
        self.device_session_id=device_session_id
        
    def open_category(self, category_id, category_name):
        self.page.clean()

        quiz_page = QuizListPage(
            self.page,
            self.quiz_service,
            self.attempt_service,
            self.subscription_service,
            category_id,
            category_name,
            self.on_profile,
            self.device_session_id,
        )
        
        self.page.add(
            quiz_page.build()
        )
        
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
                ]
            )

        category_controls = []

        for category in categories:
            card_content = ft.Container(
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

        return ft.Column(
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
                ft.Text(
                    "Choose a Category",
                    size=22,
                ),
                ft.Column(
                    category_controls,
                    spacing=10,
                ),
            ],
            spacing=15,
        )
        
    def open_history(self, e):
        self.page.clean()

        from pages.results import ResultsPage

        results_page = ResultsPage(
            self.page,
            self.attempt_service,
            self.quiz_service,
            self.build_home,
        )

        self.page.add(
            results_page.build()
        )
    
    def open_profile(self, e):
        self.on_profile()

    def build_home(self):
        self.page.clean()
        
        print("CREATING HOME PAGE")


        home_page = HomePage(
            self.page,
            self.quiz_service,
            self.attempt_service,
            self.subscription_service,
            self.on_profile,
        )

        self.page.add(
            home_page.build()
        )
        
class QuizListPage:
    def __init__(
        self,
        page,
        quiz_service,
        attempt_service,
        subscription_service,
        category_id,
        category_name,
        on_profile,
        device_session_id,
    ):
        self.page = page
        self.quiz_service = quiz_service
        self.attempt_service = attempt_service
        self.subscription_service = subscription_service
        self.category_id = category_id
        self.category_name = category_name
        self.on_profile = on_profile
        self.device_session_id=device_session_id
        self.question_count = 20
        
    def go_back(self, e):
        self.page.clean()

        home_page = HomePage(
            self.page,
            self.quiz_service,
            self.attempt_service,
            self.subscription_service,
            self.on_profile,
            self.device_session_id,
        )

        self.page.add(home_page.build())

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
                        on_click=self.go_back,
                    ),
                    ft.Text(
                        f"Could not load quizzes: {error}",
                        color=ft.Colors.RED,
                    ),
                ]
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
            print("QUIZ:",
                quiz["title"],
                "IS PREMIUM:",
                quiz.get("is_premium"),
            )

            quiz_content = ft.Container(
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
            
        question_count_dropdown = ft.Dropdown(
            label="Number of questions",
            value=str(self.question_count),
            options=[
                ft.DropdownOption(key="5", text="5 questions"),
                ft.DropdownOption(key="10", text="10 questions"),
                ft.DropdownOption(key="20", text="20 questions"),
                ft.DropdownOption(key="30", text="30 questions"),
                ft.DropdownOption(key="50", text="50 questions"),
                ft.DropdownOption(key="all", text="All questions"),
            ],
        )

        question_count_dropdown.on_select = (
            self.question_count_changed
        )
        
        start_quiz_button = ft.Button(
            "Start Quiz",
            on_click=self.start_quiz,
        )

        return ft.Column(
            [
                ft.Button(
                    "← Back",
                    on_click=self.go_back,
                ),

                ft.Text(
                    self.category_name,
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Text(
                    "How many questions do you want to try?",
                    size=18,
                ),

                question_count_dropdown,
                
                start_quiz_button,

                ft.Text(
                    "Available Quizzes",
                    size=20,
                ),

                ft.Column(
                    quiz_controls,
                    spacing=10,
                ),
            ],
            spacing=15,
        )
        
    def question_count_changed(self, e):
        print("DROPDOWN EVENT FIRED")
        print("SELECTED VALUE:", e.control.value)

        if e.control.value == "all":
            self.question_count = None
        else:
            self.question_count = int(e.control.value)
            
    def start_quiz(self, e):
        print("START QUIZ CLICKED")
        print("QUESTION COUNT:", self.question_count)
        print("CATEGORY ID:", self.category_id)

        questions = self.quiz_service.get_random_questions(
            self.category_id,
            self.question_count,
        )

        print("QUESTIONS FOUND:", len(questions))

        if not questions:
            print("NO QUESTIONS FOUND")
            return

        quiz_page = QuizPage(
            self.page,
            self.quiz_service,
            self.attempt_service,
            self.subscription_service,
            None,
            "Random Quiz",
            None,
            self.on_profile,
            self.device_session_id,
            None,
            questions=questions,
        )
        
        print("QUIZ PAGE QUESTIONS:", len(quiz_page.questions))
        print("FIRST QUESTION:", quiz_page.questions[0] if quiz_page.questions else None)


        self.page.clean()
        self.page.add(quiz_page.build())
        self.page.update()        

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
                                "Back",
                                on_click=self.go_back,
                            ),
                        ],
                        spacing=15,
                    )
                )

                self.page.update()
                return

        try:
            print("OPEN QUIZ STARTED")
            print("QUIZ ID:", quiz_id)
            print("QUIZ TITLE:", quiz_title)
            print("TIME LIMIT:", time_limit_seconds)

            self.page.clean()

            quiz_page = QuizPage(
                self.page,
                self.quiz_service,
                self.attempt_service,
                self.subscription_service,
                quiz_id,
                quiz_title,
                time_limit_seconds,
                self.on_profile,
                self.device_session_id,
                self.question_count
            )

            print("QUIZ PAGE CREATED")

            content = quiz_page.build()

            print("QUIZ PAGE BUILT")

            self.page.add(content)

            print("QUIZ PAGE ADDED")

        except Exception as error:
            print("OPEN QUIZ ERROR:", repr(error))

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
                            "Back",
                            on_click=self.go_back,
                        ),
                    ]
                )
            )

            self.page.update()
        
    
class QuizPage:
    def __init__(
        self,
        page,
        quiz_service,
        attempt_service,
        subscription_service,
        quiz_id,
        quiz_title,
        time_limit_seconds,
        on_profile,
        device_session_id,
        question_count,
        questions=None,
    ):
        self.page = page
        self.quiz_service = quiz_service
        self.attempt_service = attempt_service
        self.subscription_service = subscription_service
        self.quiz_id = quiz_id
        self.quiz_title = quiz_title
        self.time_limit_seconds = time_limit_seconds
        self.on_profile = on_profile
        self.device_session_id = device_session_id
        self.question_count = question_count
        self.questions = questions or []
        
        print("QUIZPAGE INIT QUESTIONS ARG:", questions)
        print("QUIZPAGE INIT QUESTIONS COUNT:", len(questions or []))
        print("QUIZPAGE STORED QUESTIONS:", len(self.questions))
        
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

    def load_questions(self):
        self.questions = self.quiz_service.get_questions(
            self.quiz_id
        )
        if self.question_count is not None:
            self.questions = self.questions[:self.question_count]

    def select_answer(self, question, option_key):
        self.selected_answer = {
            "option": option_key,
            "is_correct": (
                option_key == question.get("correct_option")
            ),
        }

        self.page.clean()
        self.page.add(self.build())
        

    def next_question(self, e=None):
        if self.selected_answer is None:
            return

        question = self.questions[
            self.current_question_index
        ]

        self.selected_answers.append(
            {
                "question_id": question["id"],
                "selected_option": self.selected_answer["option"],
                "is_correct": self.selected_answer["is_correct"],
            }
        )

        if self.selected_answer["is_correct"]:
            self.score += 1

        self.current_question_index += 1
        self.selected_answer = None

        if (
            self.current_question_index
            >= len(self.questions)
        ):
            self.save_attempt()
            return

        self.page.clean()
        self.page.add(self.build())
        self.page.update()

    def next_question_t(self, e):
        print("NEXT QUESTION CLICKED")
        print("CURRENT INDEX:", self.current_question_index)
        print("TOTAL QUESTIONS:", len(self.questions))

        if not self.questions:
            print("NO QUESTIONS!")
            return

        if self.current_question_index >= len(self.questions) - 1:
            print("LAST QUESTION - CALLING SAVE_ATTEMPT")
            self.save_attempt()
            return

        self.current_question_index += 1

        print(
            "MOVING TO QUESTION:",
            self.current_question_index
        )

        self.render_question()
        
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

            timeout_answers = []

            for question in self.questions:
                saved_answer = answered_map.get(
                    question["id"]
                )

                if saved_answer:
                    timeout_answers.append(
                        saved_answer
                    )
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
            self.show_save_error(
                str(error)
            )
            
    def save_attempt(self):
        try:
            user_id = (
                self.attempt_service
                .get_current_user_id()
            )

            if not user_id:
                self.show_save_error(
                    "You are not logged in."
                )
                return

            self.time_taken_seconds = (
                self.time_limit_seconds - self.remaining_seconds
                if self.time_limit_seconds is not None
                else None
            )

            attempt = (
                self.attempt_service.create_attempt(
                    user_id=user_id,
                    quiz_id=self.quiz_id,
                    score=self.score,
                    total_questions=len(
                        self.questions
                    ),
                    correct_answers=self.score,
                    time_taken_seconds=self.time_taken_seconds,
                    answers=self.selected_answers,
                )
            )

            self.show_result()

        except Exception as error:
            self.show_save_error(
                str(error)
            )
            
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

    def show_result(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None
            
        total = len(self.questions)

        percentage = 0

        if total:
            percentage = round(
                (self.score / total) * 100
            )

        incorrect = total - self.score
        
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
                            f"Correct: {self.score}",
                            size=18,
                        ),
                        ft.Text(
                            f"Incorrect: {incorrect}",
                            size=18,
                        ),
                    ],
                    spacing=30,
                ),

                ft.Divider(),

                ft.Text(
                    "Your result has been saved.",
                    color=ft.Colors.GREEN,
                ),

                ft.Button(
                    "Try Again",
                    on_click=self.try_again,
                ),

                ft.Button(
                    "View Quiz History",
                    on_click=self.view_history,
                ),
                ft.Button(
                    "Review Answers",
                    on_click=self.review_answers,
                ),
                ft.Button(
                    "Back to Home",
                    on_click=self.back_to_home,
                ),
            ],
            spacing=15,
        )

        self.page.add(
            ft.Container(
                content=result_content,
                width=500,
                padding=30,
            )
        )
    
    def try_again(self, e=None):
        if self.timer:
            self.timer.cancel()
            self.timer = None

        self.remaining_seconds = self.time_limit_seconds
        self.timer_started = False

        self.current_question_index = 0
        self.score = 0
        self.selected_answer = None
        self.selected_answers = []

        self.page.clean()
        self.page.add(self.build())
        self.page.update()
    
    def view_history(self, e=None):
        self.page.clean()

        from pages.results import ResultsPage

        results_page = ResultsPage(
            self.page,
            self.attempt_service,
            self.quiz_service,
            self.back_to_home,
        )

        self.page.add(
            results_page.build()
        )
        
    def back_to_home(self, e=None):
        from pages.home import HomePage

        if self.timer:
            self.timer.cancel()
            self.timer = None

        self.page.clean()
        
        home_page = HomePage(
            self.page,
            self.quiz_service,
            self.attempt_service,
            self.subscription_service,
            self.on_profile,
            self.device_session_id,
        )

        self.page.add(
            home_page.build()
        )

        self.page.update()
    
    def build(self):
        if not self.questions:
            try:
                self.load_questions()
            except Exception as error:
                
                return ft.Column(
                    [
                        ft.Text(
                            self.quiz_title,
                            size=28,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            f"Could not load questions: "
                            f"{error}",
                            color=ft.Colors.RED,
                        ),
                    ]
                )

        if not self.questions:
            return ft.Column(
                [
                    ft.Text(
                        self.quiz_title,
                        size=28,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "This quiz does not have "
                        "any questions yet."
                    ),
                ]
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
            ft.Text(
                self.quiz_title,
                size=28,
                weight=ft.FontWeight.BOLD,
            ),
            self.timer_text,
            ft.Text(
                f"Question "
                f"{self.current_question_index + 1}"
                f" / {len(self.questions)}",
                size=18,
            ),
            ft.Text(
                question["question_text"],
                size=22,
                weight=ft.FontWeight.BOLD,
            ),
        ]

        for option_key, option_text in options:

            is_selected = (
                self.selected_answer is not None
                and self.selected_answer["option"]
                == option_key
            )

            option_container = ft.Container(
                content=ft.Text(
                    f"{option_key}. {option_text}",
                    size=18,
                ),
                padding=15,
                border=ft.Border.all(
                    2 if is_selected else 1
                ),
                border_radius=10,
                on_click=lambda e, key=option_key:
                    self.select_answer(
                        question,
                        key,
                    ),
                ink=True,
            )

            controls.append(
                option_container
            )

        controls.append(
            ft.Button(
                "Next Question",
                on_click=self.next_question,
                disabled=(
                    self.selected_answer
                    is None
                ),
            )
        )
        if not self.timer_started:
            self.timer_started = True
            self.timer = self.page.run_task(
                self.start_timer
            )
            
        return ft.Column(
            controls,
            spacing=15,
        )
    
    def review_answers(self, e=None):
        self.page.clean()

        controls = [
            ft.Text(
                "Review Answers",
                size=30,
                weight=ft.FontWeight.BOLD,
            ),

            ft.Text(
                self.quiz_title,
                size=22,
            ),

            ft.Divider(),
        ]

        for index, question in enumerate(self.questions):
            selected_option = None
            is_correct = False

            for saved_answer in self.selected_answers:
                if saved_answer["question_id"] == question["id"]:
                    selected_option = saved_answer["selected_option"]
                    is_correct = saved_answer["is_correct"]
                    break

            selected_answer_text = "Not answered"

            if selected_option:
                option_text = question.get(
                    f"option_{selected_option.lower()}"
                )

                selected_answer_text = (
                    f"{selected_option}. {option_text}"
                )

            if selected_option is None:
                result_text = "Not answered"
                result_color = ft.Colors.ORANGE
            elif is_correct:
                result_text = "Correct"
                result_color = ft.Colors.GREEN
            else:
                result_text = "Incorrect"
                result_color = ft.Colors.RED    
                
            question_controls = [
                ft.Text(
                    f"Question {index + 1}",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Text(
                    question["question_text"],
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Text(
                    f"Your answer: {selected_answer_text}",
                    size=17,
                ),

                ft.Text(
                    result_text,
                    size=17,
                    weight=ft.FontWeight.BOLD,
                    color=result_color,
                ),
            ]

            if question.get("explanation") and selected_option is not None:
                question_controls.append(
                    ft.Text(
                        f"Explanation: "
                        f"{question['explanation']}",
                        size=16,
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
                    )
                )
            )

        controls.append(
            ft.Button(
                "Back to Result",
                on_click=self.back_to_result,
            )
        )

        self.page.add(
            ft.Column(
                controls,
                spacing=15,
                scroll=ft.ScrollMode.AUTO,
            )
        )
    
    def back_to_result(self, e=None):
        self.show_result()