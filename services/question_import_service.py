import csv
import io


class QuestionImportService:
    REQUIRED_COLUMNS = [
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_option",
        "explanation",
    ]

    def __init__(self, supabase):
        self.supabase = supabase

    def import_csv(self, csv_text, category_id):
        reader = csv.DictReader(io.StringIO(csv_text))

        if not reader.fieldnames:
            raise Exception("CSV file is empty.")

        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in reader.fieldnames
        ]

        if missing_columns:
            raise Exception(
                "Missing columns: "
                + ", ".join(missing_columns)
            )

        if not category_id:
            raise Exception("Category is required.")
            
        existing_questions = (
            self.supabase
            .table("questions")
            .select("id")
            .like("id", "q_%")
            .execute()
        )

        next_number = 1

        for existing_question in existing_questions.data or []:
            question_id = existing_question["id"]

            try:
                number = int(question_id.replace("q_", ""))
                next_number = max(next_number, number + 1)
            except ValueError:
                continue

        questions = []

        for row_number, row in enumerate(reader, start=2):
            question_text = row["question_text"].strip()
            option_a = row["option_a"].strip()
            option_b = row["option_b"].strip()
            option_c = row["option_c"].strip()
            option_d = row["option_d"].strip()
            correct_option = row["correct_option"].strip().upper()
            explanation = row["explanation"].strip()

            if not question_text:
                raise Exception(
                    f"Row {row_number}: question is empty."
                )

            if correct_option not in ["A", "B", "C", "D"]:
                raise Exception(
                    f"Row {row_number}: "
                    "correct_option must be A, B, C, or D."
                )

            question_id = f"q_{next_number:02d}"
            next_number += 1

            questions.append(
                {
                    "id": question_id,
                    "question_text": question_text,
                    "option_a": option_a,
                    "option_b": option_b,
                    "option_c": option_c,
                    "option_d": option_d,
                    "correct_option": correct_option,
                    "explanation": explanation,
                    "category_id": category_id,
                }
            )

        if not questions:
            raise Exception("No questions found in CSV.")

        response = (
            self.supabase
            .table("questions")
            .insert(questions)
            .execute()
        )

        return response.data