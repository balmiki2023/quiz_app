import flet as ft

from admin.categories import AdminCategories
from admin.quizzes import AdminQuizzes
from admin.questions import AdminQuestions
from admin.question_import import QuestionImport


class AdminDashboard:
    def __init__(
        self,
        page,
        admin_service,
        quiz_service,
        supabase,
        on_back,
    ):
        self.page = page
        self.admin_service = admin_service
        self.quiz_service = quiz_service
        self.supabase = supabase
        self.on_back = on_back

    def build(self):
        return ft.Column(
            [
                ft.Button(
                    "← Back to Profile",
                    on_click=self.on_back,
                ),

                ft.Text(
                    "Admin Dashboard",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Text(
                    "Manage categories, quizzes, and questions."
                ),

                ft.Divider(),

                ft.Button(
                    "Categories",
                    on_click=self.open_categories,
                ),

                ft.Button(
                    "Quizzes",
                    on_click=self.open_quizzes,
                ),

                ft.Button(
                    "Questions",
                    on_click=self.open_questions,
                ),
                
                ft.Button(
                    "Bulk Import Questions",
                    on_click=self.open_question_import,
                ),
            ],
            width=500,
            spacing=15,
        )
    
    def open_question_import(self, e=None):
        import_page = QuestionImport(
            self.page,
            self.quiz_service,
            self.supabase,
            self.show_dashboard,
        )

        self.page.clean()
        self.page.add(import_page.build())
        self.page.update()
    
    def open_categories(self, e=None):
        categories_page = AdminCategories(
            self.page,
            self.quiz_service,
            self.show_dashboard,
        )

        self.page.clean()
        self.page.add(categories_page.build())
        self.page.update()

    def open_quizzes(self, e=None):
        quizzes_page = AdminQuizzes(
            self.page,
            self.quiz_service,
            self.show_dashboard,
        )

        self.page.clean()
        self.page.add(quizzes_page.build())
        self.page.update()

    def open_questions(self, e=None):
        questions_page = AdminQuestions(
            self.page,
            self.quiz_service,
            self.show_dashboard,
        )

        self.page.clean()
        self.page.add(questions_page.build())
        self.page.update()

    def show_dashboard(self):
        self.page.clean()
        self.page.add(self.build())
        self.page.update()