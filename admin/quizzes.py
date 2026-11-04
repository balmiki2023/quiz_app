import flet as ft

class AdminQuizzes:
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
        )
        self.category_dropdown.on_select = self.on_category_change

        self.title_field = ft.TextField(
            label="Quiz title",
            width=400,
        )

        self.description_field = ft.TextField(
            label="Description",
            width=400,
            multiline=True,
        )

        self.difficulty_dropdown = ft.Dropdown(
            label="Difficulty",
            width=400,
            options=[
                ft.DropdownOption("Easy"),
                ft.DropdownOption("Medium"),
                ft.DropdownOption("Hard"),
            ],
        )

        self.time_limit_field = ft.TextField(
            label="Time limit (seconds)",
            width=400,
            value="300",
        )
        
        self.premium_checkbox = ft.Checkbox(
            label="Premium quiz",
            value=False,
        )

        self.published_checkbox = ft.Checkbox(
            label="Published",
            value=True,
        )

        self.message = ft.Text("")
        
        self.editing_quiz_id = None
        
        self.selected_quiz_id = None
        
        self.selected_question_ids = []        
        self.category_questions = []
        self.new_quiz_question_ids = []
        self.new_quiz_questions_section = None
        
        self.assigned_questions_section = None
        self.category_questions_section = ft.Container(
            content=ft.Text("Select a category to see its questions.")
        )

        self.load_categories()
        
    def category_changed(self, e=None):
        # Clear selections when switching categories.
        self.selected_question_ids.clear()

        self.category_questions_section.content = (
            self.build_category_questions()
        )

        self.page.update()

    def build_category_questions(self):
        category_id = self.category_dropdown.value

        if not category_id:
            return ft.Text("Select a category to see its questions.")

        try:
            questions = self.quiz_service.get_admin_questions_by_category(
                category_id
            )

            if not questions:
                return ft.Text("No questions found in this category.")

            controls = []

            for index, question in enumerate(questions, start=1):
                question_id = str(question["id"])

                checkbox = ft.Checkbox(
                    label="Select question",
                    value=question_id in self.selected_question_ids,
                    on_change=lambda e, qid=question_id:
                        self.toggle_question_selection(
                            qid,
                            e.control.value,
                        ),
                )

                controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        f"Question {index}",
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(question["question_text"]),
                                    checkbox,
                                ],
                                spacing=8,
                            ),
                            padding=12,
                        )
                    )
                )

            return ft.Column(
                controls=controls,
                spacing=10,
            )

        except Exception as error:
            self.message.value = (
                f"Could not load category questions: {error}"
            )
            return ft.Text(
                "Could not load questions. Check the message above."
            )
        
    def on_category_change(self, e=None):
        category_id = self.category_dropdown.value

        self.category_questions = []
        self.new_quiz_question_ids = []

        if category_id:
            self.category_questions = (
                self.quiz_service.get_admin_questions_by_category(
                    category_id
                )
            )

        if self.new_quiz_questions_section:
            self.new_quiz_questions_section.content = (
                self.build_new_quiz_question_picker()
            )

        self.page.update()

    def toggle_new_quiz_question(self, question_id, selected):
        question_id = str(question_id)

        if selected:
            if question_id not in self.new_quiz_question_ids:
                self.new_quiz_question_ids.append(question_id)
        elif question_id in self.new_quiz_question_ids:
            self.new_quiz_question_ids.remove(question_id)

        self.new_quiz_questions_section.content = (
            self.build_new_quiz_question_picker()
        )
        self.page.update()

    def move_new_quiz_question(self, question_id, direction):
        ids = self.new_quiz_question_ids
        index = ids.index(str(question_id))
        new_index = index + direction

        if not 0 <= new_index < len(ids):
            return

        ids[index], ids[new_index] = ids[new_index], ids[index]

        self.new_quiz_questions_section.content = (
            self.build_new_quiz_question_picker()
        )
        self.page.update()

    def build_new_quiz_question_picker(self):
        controls = [
            ft.Text(
                "Select questions and arrange their order",
                size=18,
                weight=ft.FontWeight.BOLD,
            )
        ]

        if not self.category_dropdown.value:
            controls.append(ft.Text("Choose a category first."))
            return ft.Column(controls, spacing=10)

        if not self.category_questions:
            controls.append(
                ft.Text("No questions found in this category.")
            )
            return ft.Column(controls, spacing=10)

        controls.append(ft.Text("Available Questions"))

        for question in self.category_questions:
            qid = str(question["id"])

            controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            [
                                ft.Text(question["question_text"]),
                                ft.Checkbox(
                                    label="Include in quiz",
                                    value=qid in self.new_quiz_question_ids,
                                    on_change=lambda e, question_id=qid:
                                        self.toggle_new_quiz_question(
                                            question_id,
                                            e.control.value,
                                        ),
                                ),
                            ],
                            spacing=5,
                        ),
                    )
                )
            )

        controls.append(ft.Divider())
        controls.append(ft.Text("Selected order"))

        for position, qid in enumerate(
            self.new_quiz_question_ids, start=1
        ):
            question = next(
                q for q in self.category_questions
                if str(q["id"]) == qid
            )

            index = position - 1

            controls.append(
                ft.Row(
                    [
                        ft.Text(f"{position}.", width=30),
                        ft.Text(
                            question["question_text"],
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ARROW_UPWARD,
                            disabled=index == 0,
                            on_click=lambda e, question_id=qid:
                                self.move_new_quiz_question(
                                    question_id, -1
                                ),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ARROW_DOWNWARD,
                            disabled=(
                                index == len(self.new_quiz_question_ids) - 1
                            ),
                            on_click=lambda e, question_id=qid:
                                self.move_new_quiz_question(
                                    question_id, 1
                                ),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        return ft.Column(controls, spacing=10)
                    
    
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
    
    def manage_questions(self, quiz):
        self.selected_quiz_id = quiz["id"]
        self.editing_quiz_id = quiz["id"]

        self.message.value = (
            f"Managing questions for: {quiz['title']}"
        )

        self.page.clean()
        self.page.add(self.build())
        self.page.update()    
        
    
    def build_available_questions(self, quiz):
        questions = self.quiz_service.get_available_questions_for_quiz(
            quiz_id=quiz["id"],
            category_id=quiz["category_id"],
        )

        if not questions:
            return ft.Text(
                "No available questions in this category."
            )

        controls = [
            ft.Button(
                "Add Selected Questions",
                on_click=lambda e, quiz_id=quiz["id"]:
                    self.add_selected_questions(quiz_id),
            )
        ]

        for index, question in enumerate(questions, start=1):
            question_id = str(question["id"])

            checkbox = ft.Checkbox(
                label="Select question",
                value=question_id in self.selected_question_ids,
                on_change=lambda e, qid=question_id:
                    self.toggle_question_selection(
                        qid, e.control.value
                    ),
            )

            controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    f"Question {index}",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    question["question_text"],
                                    size=16,
                                ),
                                checkbox,
                            ],
                            spacing=8,
                        ),
                        padding=15,
                    )
                )
            )

        return ft.Column(
            controls,
            spacing=10,
        )

    def toggle_question_selection(self, question_id, selected):
        question_id = str(question_id)

        if selected:
            if question_id not in self.selected_question_ids:
                self.selected_question_ids.append(question_id)
        else:
            if question_id in self.selected_question_ids:
                self.selected_question_ids.remove(question_id)

    def add_selected_questions(self, quiz_id):
        if not self.selected_question_ids:
            self.message.value = "Select at least one question first."
            self.page.update()
            return

        try:
            # Fetch the questions still available in this quiz's category.
            available_questions = (
                self.quiz_service.get_available_questions_for_quiz(
                    quiz_id=quiz_id,
                    category_id=next(
                        q["category_id"]
                        for q in self.quiz_service.get_admin_quizzes()
                        if str(q["id"]) == str(quiz_id)
                    ),
                )
            )

            questions_by_id = {
                str(question["id"]): question
                for question in available_questions
            }

            selected_questions = [
                questions_by_id[question_id]
                for question_id in self.selected_question_ids
                if question_id in questions_by_id
            ]

            assigned = self.quiz_service.get_assigned_questions(quiz_id)

            existing_orders = {
                int(item["question_order"])
                for item in assigned
            }

            added_count = 0

            for question in selected_questions:
                next_order = 1

                while next_order in existing_orders:
                    next_order += 1

                self.quiz_service.add_question_to_quiz(
                    quiz_id=quiz_id,
                    question_id=question["id"],
                    question_order=next_order,
                )

                existing_orders.add(next_order)
                added_count += 1

            self.selected_question_ids.clear()

            self.message.value = (
                f"Successfully added {added_count} question(s) to the quiz."
            )

            self.refresh_question_management()

        except Exception as error:
            self.message.value = f"Could not add questions: {error}"
            self.page.update()
        
    
    def add_question_to_quiz(
        self,
        quiz_id,
        question_id,
    ):
        try:
            assigned = (
                self.quiz_service.get_assigned_questions(
                    quiz_id
                )
            )

            existing_orders = {
                item["question_order"]
                for item in assigned
            }

            next_order = 1

            while next_order in existing_orders:
                next_order += 1

            self.quiz_service.add_question_to_quiz(
                quiz_id=quiz_id,
                question_id=question_id,
                question_order=next_order,
            )

            self.message.value = (
                "Question added to quiz successfully."
            )

            # Refresh only the question-management section.
            # The ListView itself is not rebuilt.
            self.refresh_question_management()

        except Exception as error:
            self.message.value = str(error)
            self.page.update()

    def build(self):
        self.assigned_questions_section = ft.Container(
            content=self.build_assigned_questions_section()
        )
        
        self.new_quiz_questions_section = ft.Container(
            content=self.build_new_quiz_question_picker(),
            visible=(
                self.selected_quiz_id is None
                and self.editing_quiz_id is None
            ),
        )

        self.main_column = ft.ListView(
            controls=[
                ft.Button(
                    "← Back",
                    on_click=self.on_back,
                ),

                ft.Text(
                    "Quiz Management",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),

                self.category_dropdown,
                ft.Text(
                    "Questions in Selected Category",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),
                
                self.new_quiz_questions_section,

                self.title_field,

                self.description_field,

                self.difficulty_dropdown,

                self.time_limit_field,

                self.premium_checkbox,

                self.published_checkbox,

                ft.Button(
                    "Create Quiz with Selected Questions",
                    on_click=self.create_quiz_with_selected_questions,
                ),

                ft.Button(
                    "Save Quiz Changes",
                    on_click=self.save_quiz,
                ),

                self.message,

                ft.Divider(),

                self.assigned_questions_section,

                ft.Text(
                    "Existing Quizzes",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),

                self.build_quiz_list(),
            ],
            width=600,
            spacing=15,
            expand=True,
        )

        return self.main_column

    def build_quiz_list(self):
        quizzes = self.quiz_service.get_quizzes()

        controls = []

        for quiz in quizzes:
            controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    quiz["title"],
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                ),

                                ft.Text(
                                    f"Difficulty: "
                                    f"{quiz.get('difficulty') or 'N/A'}"
                                ),

                                ft.Text(
                                    f"Time limit: "
                                    f"{quiz.get('time_limit_seconds') or 'N/A'} seconds"
                                ),

                                ft.Row(
                                    [
                                        ft.Button(
                                            "Edit",
                                            on_click=lambda e, q=quiz:
                                                self.edit_quiz(q),
                                        ),
                                        ft.Button(
                                            "Manage Questions",
                                            on_click=lambda e, q=quiz:
                                                self.manage_questions(q),
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

        if not controls:
            controls.append(
                ft.Text("No quizzes found.")
            )

        return ft.Column(
            controls,
            spacing=10,
        )
    
    def build_assigned_questions(self, quiz_id):
        assigned_questions = (
            self.quiz_service.get_assigned_questions(
                quiz_id
            )
        )

        if not assigned_questions:
            return ft.Text(
                "No questions assigned to this quiz."
            )

        controls = []

        for item in assigned_questions:
            question = item["questions"]

            controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    f"Question {item['question_order']}",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    question["question_text"],
                                    size=17,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Row(
                                    [
                                        ft.Button(
                                            "↑ Up",
                                            on_click=lambda e, q=question, quiz_id=quiz_id:
                                                self.move_question_up(
                                                    quiz_id,
                                                    q["id"],
                                                ),
                                        ),
                                        ft.Button(
                                            "↓ Down",
                                            on_click=lambda e, q=question, quiz_id=quiz_id:
                                                self.move_question_down(
                                                    quiz_id,
                                                    q["id"],
                                                ),
                                        ),
                                        ft.Button(
                                            "Remove from Quiz",
                                            on_click=lambda e, q=question, quiz_id=quiz_id:
                                                self.remove_question_from_quiz(
                                                    quiz_id,
                                                    q["id"],
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
    
    def move_question_up(self, quiz_id, question_id):
        assigned = self.quiz_service.get_assigned_questions(
            quiz_id
        )

        current_index = next(
            (
                i
                for i, item in enumerate(assigned)
                if str(item["question_id"]) == str(question_id)
            ),
            None,
        )

        if current_index is None or current_index == 0:
            return

        current = assigned[current_index]
        previous = assigned[current_index - 1]

        self.quiz_service.swap_question_order(
            quiz_id,
            current["question_id"],
            current["question_order"],
            previous["question_id"],
            previous["question_order"],
        )
        self.quiz_service.renumber_quiz_questions(quiz_id)

        self.refresh_question_management()

    def move_question_down(self, quiz_id, question_id):
        assigned = self.quiz_service.get_assigned_questions(
            quiz_id
        )

        current_index = next(
            (
                i
                for i, item in enumerate(assigned)
                if str(item["question_id"]) == str(question_id)
            ),
            None,
        )

        if current_index is None or current_index == len(assigned) - 1:
            return

        current = assigned[current_index]
        next_question = assigned[current_index + 1]

        self.quiz_service.swap_question_order(
            quiz_id,
            current["question_id"],
            current["question_order"],
            next_question["question_id"],
            next_question["question_order"],
        )
        self.quiz_service.renumber_quiz_questions(quiz_id)

        self.refresh_question_management()
    
    def remove_question_from_quiz(
        self,
        quiz_id,
        question_id,
    ):
        try:
            self.quiz_service.remove_question_from_quiz(
                quiz_id,
                question_id,
            )
            self.quiz_service.renumber_quiz_questions(quiz_id)

            self.message.value = (
                "Question removed from quiz successfully."
            )

            self.refresh_question_management()

        except Exception as error:
            self.message.value = str(error)
            self.page.update()
    
    
    def build_assigned_questions_section(self):
        if not self.selected_quiz_id:
            return ft.Container()

        quiz = next(
            (
                q
                for q in self.quiz_service.get_admin_quizzes()
                if str(q["id"]) == str(self.selected_quiz_id)
            ),
            None,
        )

        if not quiz:
            return ft.Text("Quiz not found.")

        return ft.Column(
            [
                ft.Divider(),

                ft.Text(
                    f"Managing Questions: {quiz['title']}",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Text(
                    "Assigned Questions",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),

                self.build_assigned_questions(
                    self.selected_quiz_id
                ),

                ft.Divider(),

                ft.Text(
                    "Available Questions",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),

                self.build_available_questions(
                    quiz
                ),
            ],
            spacing=10,
        )
        
    
    def refresh_question_management(self):
        if not self.assigned_questions_section:
            return

        self.assigned_questions_section.content = (
            self.build_assigned_questions_section()
        )

        self.page.update()
    
    
    def create_quiz(self, e=None):
        if not self.category_dropdown.value:
            self.message.value = (
                "Please select a category."
            )
            self.page.update()
            return

        title = self.title_field.value.strip()

        if not title:
            self.message.value = (
                "Quiz title is required."
            )
            self.page.update()
            return

        try:
            time_limit = int(
                self.time_limit_field.value
            )

            self.quiz_service.create_quiz(
                category_id=(
                    self.category_dropdown.value
                ),
                title=title,
                description=(
                    self.description_field.value.strip()
                ),
                difficulty=(
                    self.difficulty_dropdown.value
                ),
                time_limit_seconds=time_limit,
            )

            self.message.value = (
                "Quiz created successfully."
            )

            self.title_field.value = ""
            self.description_field.value = ""

            self.page.clean()
            self.page.add(self.build())
            self.page.update()

        except ValueError:
            self.message.value = (
                "Time limit must be a number."
            )
            self.page.update()

        except Exception as error:
            self.message.value = str(error)
            self.page.update()
            
    def edit_quiz(self, quiz):
        self.category_dropdown.value = str(
            quiz["category_id"]
        )

        self.title_field.value = quiz["title"]

        self.description_field.value = (
            quiz.get("description") or ""
        )

        self.difficulty_dropdown.value = (
            quiz.get("difficulty")
        )

        self.time_limit_field.value = str(
            quiz.get("time_limit_seconds") or ""
        )
        
        self.premium_checkbox.value = (
            quiz.get("is_premium", False)
        )

        self.published_checkbox.value = (
            quiz.get("is_published", True)
        )

        self.editing_quiz_id = quiz["id"]

        self.message.value = (
            "Editing quiz. Make your changes and save."
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
        
    def save_quiz(self, e=None):
        if not self.editing_quiz_id:
            self.message.value = (
                "Select a quiz to edit first."
            )
            self.page.update()
            return

        category_id = self.category_dropdown.value
        title = self.title_field.value.strip()
        description = self.description_field.value.strip()
        difficulty = self.difficulty_dropdown.value

        if not category_id:
            self.message.value = "Please select a category."
            self.page.update()
            return

        if not title:
            self.message.value = "Quiz title is required."
            self.page.update()
            return

        try:
            time_limit = int(
                self.time_limit_field.value
            )

            self.quiz_service.update_quiz(
                quiz_id=self.editing_quiz_id,
                category_id=category_id,
                title=title,
                description=description,
                difficulty=difficulty,
                is_premium=self.premium_checkbox.value,
                is_published=self.published_checkbox.value,
                time_limit_seconds=time_limit,
            )

            self.editing_quiz_id = None

            self.category_dropdown.value = None
            self.title_field.value = ""
            self.description_field.value = ""
            self.difficulty_dropdown.value = None
            self.time_limit_field.value = "300"
            
            self.premium_checkbox.value = False
            self.published_checkbox.value = True

            self.message.value = (
                "Quiz updated successfully."
            )

            self.page.clean()
            self.page.add(self.build())
            self.page.update()

        except ValueError:
            self.message.value = (
                "Time limit must be a number."
            )
            self.page.update()

        except Exception as error:
            self.message.value = str(error)
            self.page.update()
            
    def create_quiz_with_selected_questions(self, e=None):
            category_id = self.category_dropdown.value
            title = self.title_field.value.strip()
            description = self.description_field.value.strip()
            difficulty = self.difficulty_dropdown.value

            if not category_id:
                self.message.value = "Please select a category."
                self.page.update()
                return

            if not title:
                self.message.value = "Quiz title is required."
                self.page.update()
                return

            # This list must contain question IDs in the
            # exact order you want them saved.
            question_ids = list(self.new_quiz_question_ids)
            
            if not question_ids:
                self.message.value = "Select at least one question."
                self.page.update()
                return

            try:
                time_limit = int(self.time_limit_field.value)

                self.quiz_service.create_quiz_with_questions(
                    category_id=category_id,
                    title=title,
                    description=description,
                    difficulty=difficulty,
                    time_limit_seconds=time_limit,
                    is_premium=self.premium_checkbox.value,
                    is_published=self.published_checkbox.value,
                    question_ids=question_ids,
                )
                
                self.new_quiz_question_ids = []
                self.category_questions = []

                self.editing_quiz_id = None
                self.selected_question_ids = []

                self.category_dropdown.value = None
                self.title_field.value = ""
                self.description_field.value = ""
                self.difficulty_dropdown.value = None
                self.time_limit_field.value = "300"
                self.premium_checkbox.value = False
                self.published_checkbox.value = True

                self.message.value = "Quiz created successfully."

                self.page.clean()
                self.page.add(self.build())
                self.page.update()

            except ValueError:
                self.message.value = "Time limit must be a number."
                self.page.update()

            except Exception as error:
                self.message.value = str(error)
                self.page.update()
            