from supabase import Client


class QuizService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def get_categories(self):
        response = (
            self.supabase
            .table("categories")
            .select("*")
            .eq("is_published", True)
            .order("name")
            .execute()
        )

        return response.data

    def get_quizzes(self, category_id=None):
        query = (
            self.supabase
            .table("quizzes")
            .select("*")
            .eq("is_published", True)
        )

        if category_id:
            query = query.eq("category_id", str(category_id))

        response = query.order("title").execute()

        return response.data

    def get_quiz(self, quiz_id):
        response = (
            self.supabase
            .table("quizzes")
            .select("*")
            .eq("id", str(quiz_id))
            .eq("is_published", True)
            .single()
            .execute()
        )

        return response.data

    def get_questions(self, quiz_id):
        response = (
            self.supabase
            .table("quiz_questions")
            .select(
                "question_id, question_order, questions(*)"
            )
            .eq("quiz_id", str(quiz_id))
            .order("question_order")
            .execute()
        )

        questions = []

        for row in response.data or []:
            question = row.get("questions")

            if question:
                question["question_order"] = row["question_order"]
                questions.append(question)

        return questions    
        
    def create_category(
        self,
        name,
        description=None,
    ):
        existing_categories = (
            self.supabase
            .table("categories")
            .select("id")
            .like("id", "ch_%")
            .execute()
        )

        next_number = 1

        for category in existing_categories.data or []:
            category_id = category["id"]

            try:
                number = int(category_id.replace("ch_", ""))
                next_number = max(next_number, number + 1)
            except ValueError:
                continue

        category_id = f"ch_{next_number:02d}"

        response = (
            self.supabase
            .table("categories")
            .insert(
                {
                    "id": category_id,
                    "name": name,
                    "description": description,
                    "is_premium": False,
                    "is_published": True,
                }
            )
            .execute()
        )

        return response.data[0]

        return response.data[0]
        
    def create_quiz(
        self,
        category_id,
        title,
        description=None,
        difficulty=None,
        is_premium=False,
        is_published=True,
        time_limit_seconds=None,
    ):
        existing = (
            self.supabase
            .table("quizzes")
            .select("id")
            .like("id", "qz_%")
            .execute()
        )

        next_number = 1

        for quiz in existing.data or []:
            quiz_id = quiz["id"]

            try:
                number = int(
                    quiz_id.replace("qz_", "")
                )
                next_number = max(
                    next_number,
                    number + 1,
                )
            except ValueError:
                continue

        new_id = f"qz_{next_number:02d}"

        response = (
            self.supabase
            .table("quizzes")
            .insert(
                {
                    "id": new_id,
                    "category_id": str(category_id),
                    "title": title,
                    "description": description,
                    "difficulty": difficulty,
                    "is_premium": is_premium,
                    "is_published": is_published,
                    "time_limit_seconds": time_limit_seconds,
                }
            )
            .execute()
        )

        return response.data[0]
        
    def create_category_quiz(
        self,
        category_id,
    ):
        category = (
            self.supabase
            .table("categories")
            .select("id, name")
            .eq("id", str(category_id))
            .single()
            .execute()
        )

        if not category.data:
            raise Exception("Category not found.")

        category_name = category.data["name"]

        existing = (
            self.supabase
            .table("quizzes")
            .select("id")
            .eq("category_id", str(category_id))
            .eq("title", f"{category_name} - All Questions")
            .execute()
        )

        if existing.data:
            return existing.data[0]

        if existing.data:
            return existing.data[0]

        questions = (
            self.supabase
            .table("questions")
            .select("id")
            .eq("category_id", str(category_id))
            .order("question_order")
            .execute()
        )

        question_rows = questions.data or []

        quiz = self.create_quiz(
            category_id=category_id,
            title=f"{category_name} - All Questions",
            description=(
                f"Complete {category_name} question bank."
            ),
            difficulty=None,
            is_premium=True,
            is_published=True,
            time_limit_seconds=None,
        )

        for index, question in enumerate(
            question_rows,
            start=1,
        ):
            self.add_question_to_quiz(
                quiz_id=quiz["id"],
                question_id=question["id"],
                question_order=index,
            )

        return quiz
        
    def create_question(
        self,
        category_id,
        question_text,
        explanation,
        option_a,
        option_b,
        option_c,
        option_d,
        correct_option,
    ):
        existing_ids = (
            self.supabase
            .table("questions")
            .select("id")
            .execute()
        )

        existing_numbers = []

        for question in existing_ids.data:
            question_id = question["id"]

            if question_id.startswith("q_"):
                try:
                    existing_numbers.append(
                        int(question_id.split("_")[1])
                    )
                except ValueError:
                    pass

        next_number = (
            max(existing_numbers) + 1
            if existing_numbers
            else 1
        )

        new_id = f"q_{next_number:02d}"

        existing = (
            self.supabase
            .table("questions")
            .select("question_order")
            .eq("category_id", str(category_id))
            .order("question_order", desc=True)
            .limit(1)
            .execute()
        )

        if existing.data:
            next_order = existing.data[0]["question_order"] + 1
        else:
            next_order = 1

        response = (
            self.supabase
            .table("questions")
            .insert(
                {
                    "id": new_id,
                    "category_id": str(category_id),
                    "question_text": question_text,
                    "explanation": explanation,
                    "option_a": option_a,
                    "option_b": option_b,
                    "option_c": option_c,
                    "option_d": option_d,
                    "correct_option": correct_option,
                    "question_order": next_order,
                }
            )
            .execute()
        )

        return response.data[0]
        
    def add_question_to_quiz(
        self,
        quiz_id,
        question_id,
        question_order,
    ):
        response = (
            self.supabase
            .table("quiz_questions")
            .insert(
                {
                    "quiz_id": str(quiz_id),
                    "question_id": str(question_id),
                    "question_order": question_order,
                }
            )
            .execute()
        )

        return response.data[0]
        
    def remove_question_from_quiz(
        self,
        quiz_id,
        question_id,
    ):
        response = (
            self.supabase
            .table("quiz_questions")
            .delete()
            .eq("quiz_id", str(quiz_id))
            .eq("question_id", str(question_id))
            .execute()
        )

        return response.data
        
    def swap_question_order(
        self,
        quiz_id,
        question_id_1,
        question_order_1,
        question_id_2,
        question_order_2,
    ):
        self.supabase.table("quiz_questions").update({
            "question_order": 0,
        }).eq(
            "quiz_id", str(quiz_id)
        ).eq(
            "question_id", str(question_id_1)
        ).execute()

        self.supabase.table("quiz_questions").update({
            "question_order": question_order_1,
        }).eq(
            "quiz_id", str(quiz_id)
        ).eq(
            "question_id", str(question_id_2)
        ).execute()

        self.supabase.table("quiz_questions").update({
            "question_order": question_order_2,
        }).eq(
            "quiz_id", str(quiz_id)
        ).eq(
            "question_id", str(question_id_1)
        ).execute()

    def get_admin_questions_by_category(self, category_id):
        response = (
            self.supabase
            .table("questions")
            .select("*")
            .eq("category_id", str(category_id))
            .order("question_order")
            .execute()
        )

        return response.data
    

    def get_random_questions(
        self,
        category_id,
        limit=20,
    ):
        response = (
            self.supabase
            .table("questions")
            .select("*")
            .eq("category_id", str(category_id))
            .execute()
        )

        questions = response.data or []

        if len(questions) <= limit:
            return questions

        import random

        return random.sample(
            questions,
            limit,
        )

    
    def get_quiz_questions(self, quiz_id):
        response = (
            self.supabase
            .table("quiz_questions")
            .select(
                "question_id, question_order, "
                "questions(*)"
            )
            .eq("quiz_id", str(quiz_id))
            .order("question_order")
            .execute()
        )

        return response.data
        
    def get_admin_quizzes(self, category_id=None):
        query = (
            self.supabase
            .table("quizzes")
            .select("*")
        )

        if category_id:
            query = query.eq(
                "category_id",
                str(category_id),
            )

        response = (
            query
            .order("title")
            .execute()
        )

        return response.data
        
    def get_admin_questions(self, quiz_id):
        response = (
            self.supabase
            .table("questions")
            .select("*")
            .eq("quiz_id", str(quiz_id))
            .order("question_order")
            .execute()
        )

        return response.data
        
    def delete_question(self, question_id):
        response = (
            self.supabase
            .table("questions")
            .delete()
            .eq("id", str(question_id))
            .select("id")
            .execute()
        )

        print("DELETE RESPONSE:", response.data)

        return response.data
        
    def reorder_questions(self, quiz_id):
        questions = (
            self.supabase
            .table("questions")
            .select("id")
            .eq("quiz_id", str(quiz_id))
            .order("question_order")
            .execute()
        )

        for index, question in enumerate(questions.data, start=1):
            self.supabase \
                .table("questions") \
                .update({
                    "question_order": index
                }) \
                .eq("id", question["id"]) \
                .execute()
    
    def update_question(
        self,
        question_id,
        question_text,
        explanation,
        option_a,
        option_b,
        option_c,
        option_d,
        correct_option,
    ):
        response = (
            self.supabase
            .table("questions")
            .update({
                "question_text": question_text,
                "explanation": explanation,
                "option_a": option_a,
                "option_b": option_b,
                "option_c": option_c,
                "option_d": option_d,
                "correct_option": correct_option,
            })
            .eq("id", str(question_id))
            .execute()
        )

        return response.data
        
    def update_quiz(
        self,
        quiz_id,
        category_id,
        title,
        description,
        difficulty,
        is_premium,
        is_published,
        time_limit_seconds,
    ):
        response = (
            self.supabase
            .table("quizzes")
            .update({
                "category_id": str(category_id),
                "title": title,
                "description": description,
                "difficulty": difficulty,
                "is_premium": is_premium,
                "is_published": is_published,
                "time_limit_seconds": time_limit_seconds,
            })
            .eq("id", str(quiz_id))
            .execute()
        )

        return response.data
    
    def delete_quiz(self, quiz_id):
        response = (
            self.supabase
            .table("quizzes")
            .delete()
            .eq("id", str(quiz_id))
            .execute()
        )

        return response.data
        
    def get_assigned_questions(self, quiz_id):
        response = (
            self.supabase
            .table("quiz_questions")
            .select(
                "question_id, question_order, questions(*)"
            )
            .eq("quiz_id", str(quiz_id))
            .order("question_order")
            .execute()
        )

        return response.data
        
    def get_available_questions_for_quiz(
        self,
        quiz_id,
        category_id,
    ):
        assigned = (
            self.supabase
            .table("quiz_questions")
            .select("question_id")
            .eq("quiz_id", str(quiz_id))
            .execute()
        )

        assigned_ids = [
            row["question_id"]
            for row in assigned.data
        ]

        query = (
            self.supabase
            .table("questions")
            .select("*")
            .eq("category_id", str(category_id))
            .order("question_order")
        )

        if assigned_ids:
            query = query.not_.in_(
                "id",
                assigned_ids,
            )

        response = query.execute()

        return response.data
        
    