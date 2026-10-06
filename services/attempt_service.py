from supabase import Client


class QuizAttemptService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def get_current_user_id(self):
        response = self.supabase.auth.get_user()

        if not response or not response.user:
            return None

        return response.user.id

    def create_attempt(
        self,
        user_id,
        quiz_id,
        category_id,
        score,
        total_questions,
        correct_answers,
        time_taken_seconds=None,
        answers=None,
    ):
        response = (
            self.supabase
            .table("quiz_attempts")
            .insert(
                {
                    "user_id": str(user_id),
                    "quiz_id": str(quiz_id) if quiz_id else None,
                    "category_id": str(category_id) if category_id else None,
                    "score": score,
                    "total_questions": total_questions,
                    "correct_answers": correct_answers,
                    "time_taken_seconds": time_taken_seconds,
                    "answers": answers or [],
                }
            )
            .execute()
        )

        stats_response = (
            self.supabase
            .rpc("update_question_statistics")
            .execute()
        )

    def save_answer(
        self,
        attempt_id,
        question_id,
        selected_answer_id,
        is_correct,
    ):
        response = (
            self.supabase
            .table("user_answers")
            .insert(
                {
                    "attempt_id": str(attempt_id),
                    "question_id": str(question_id),
                    "selected_answer_id": (
                        str(selected_answer_id)
                        if selected_answer_id
                        else None
                    ),
                    "is_correct": is_correct,
                }
            )
            .execute()
        )

        return response.data[0]
        
    def get_attempt(self, attempt_id):
        user_id = self.get_current_user_id()

        if not user_id:
            return None

        response = (
            self.supabase
            .table("quiz_attempts")
            .select("*, quizzes(title)")
            .eq("id", str(attempt_id))
            .eq("user_id", str(user_id))
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]
    
    def get_attempt_answers(self, attempt_id):
        response = (
            self.supabase
            .table("user_answers")
            .select("*")
            .eq("attempt_id", str(attempt_id))
            .execute()
        )

        return response.data

    def get_user_attempts(self, user_id):
        response = (
            self.supabase
            .table("quiz_attempts")
            .select(
                "*, quizzes(title)"
            )
            .eq(
                "user_id",
                str(user_id),
            )
            .order(
                "completed_at",
                desc=True,
            )
            .execute()
        )

        return response.data
    
    def get_quiz(self, quiz_id):
        response = (
            self.supabase
            .table("quizzes")
            .select("id, title")
            .eq("id", str(quiz_id))
            .single()
            .execute()
        )

        return response.data