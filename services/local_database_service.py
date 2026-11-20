"""Local SQLite database for device-specific quiz data."""

import os
import json
import uuid
import sqlite3
from pathlib import Path


class LocalDatabaseService:
    def __init__(self):
        import platform
        print("PLATFORM:", platform.platform())

        data_dir = os.getenv("FLET_APP_STORAGE_DATA")

        print("FLET STORAGE:", repr(data_dir))

        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Development fallback for desktop.
            project_root = Path(__file__).resolve().parent.parent
            self.data_dir = project_root / ".flet" / "storage" / "data"

        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.data_dir / "quiz_app.db"

        print("SQLite database path:", self.db_path)

    def initialize(self):
        """Create local tables if they do not already exist."""

        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=30000")


        try:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS question_first_attempts (
                    question_id TEXT PRIMARY KEY,
                    category_id TEXT,
                    selected_answer TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    attempted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    statistics_synced INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS question_attempt_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id TEXT NOT NULL,
                    selected_answer TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    attempted_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS
                    idx_local_history_question
                ON question_attempt_history (
                    question_id,
                    attempted_at DESC,
                    id DESC
                );

                CREATE TABLE IF NOT EXISTS question_saves (
                    question_id TEXT PRIMARY KEY,
                    saved_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT DEFAULT NULL,
                    quiz_id TEXT DEFAULT NULL,
                    score INTEGER DEFAULT 0,
                    total_questions INTEGER NOT NULL,
                    correct_answers INTEGER DEFAULT 0,
                    time_taken_seconds INTEGER DEFAULT NULL,
                    completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    answers TEXT NOT NULL DEFAULT '[]',
                    category_id TEXT DEFAULT NULL
                );

                 CREATE TABLE IF NOT EXISTS question_save_sync (
                    question_id TEXT PRIMARY KEY,
                    is_saved INTEGER NOT NULL,
                    synced_state INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                """
            )
            cursor = connection.cursor()

            cursor.execute(
                "PRAGMA table_info(question_first_attempts)"
            )

            columns = [
                row[1] for row in cursor.fetchall()
            ]

            if "category_id" not in columns:
                cursor.execute(
                    """
                    ALTER TABLE question_first_attempts
                    ADD COLUMN category_id TEXT
                    """
                )

            connection.commit()
            
        finally:
            connection.close()


    
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
        quiz_title=None,
    ):
        attempt_id = str(uuid.uuid4())

        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO quiz_attempts (
                        id,
                        user_id,
                        quiz_id,
                        category_id,
                        quiz_title,
                        score,
                        total_questions,
                        correct_answers,
                        time_taken_seconds,
                        answers
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        attempt_id,
                        str(user_id) if user_id else None,
                        str(quiz_id) if quiz_id else None,
                        str(category_id) if category_id else None,
                        quiz_title,
                        int(score or 0),
                        int(total_questions),
                        int(correct_answers or 0),
                        time_taken_seconds,
                        json.dumps(answers or []),
                    ),
                )

            return attempt_id

        finally:
            connection.close()

    
    def record_first_attempt(
        self,
        question_id,
        category_id,
        selected_answer,
        is_correct,
    ):
        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        try:
            cursor = connection.execute(
                """
                INSERT INTO question_first_attempts (
                    question_id,
                    category_id,
                    selected_answer,
                    is_correct
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(question_id) DO NOTHING
                """,
                (
                    str(question_id),
                    str(category_id),
                    str(selected_answer),
                    int(is_correct),
                ),
            )

            connection.commit()

            return cursor.rowcount == 1

        finally:
            connection.close()

    
    def record_question_history(
        self,
        question_id,
        selected_answer,
        is_correct,
    ):
        """Store an answer and retain only the latest 5 attempts."""

        connection = sqlite3.connect(self.db_path,timeout=30)

        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO question_attempt_history (
                        question_id,
                        selected_answer,
                        is_correct
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        str(question_id),
                        str(selected_answer),
                        int(is_correct),
                    ),
                )

                connection.execute(
                    """
                    DELETE FROM question_attempt_history
                    WHERE question_id = ?
                    AND id NOT IN (
                        SELECT id
                        FROM question_attempt_history
                        WHERE question_id = ?
                        ORDER BY attempted_at DESC, id DESC
                        LIMIT 5
                    )
                    """,
                    (str(question_id), str(question_id)),
                )

        finally:
            connection.close()

    
    def get_question_attempt_history(self, question_id):
        """Return the latest 5 attempts for a question."""

        connection = sqlite3.connect(self.db_path,timeout=30,)
        connection.row_factory = sqlite3.Row

        try:
            cursor = connection.execute(
                """
                SELECT
                    selected_answer,
                    is_correct,
                    attempted_at
                FROM question_attempt_history
                WHERE question_id = ?
                ORDER BY attempted_at DESC, id DESC
                LIMIT 5
                """,
                (str(question_id),),
            )

            return [dict(row) for row in cursor.fetchall()]

        finally:
            connection.close()

    def get_attempt(self, attempt_id):
        connection = sqlite3.connect(self.db_path,timeout=30,)
        connection.row_factory = sqlite3.Row

        try:
            cursor = connection.execute(
                """
                SELECT *
                FROM quiz_attempts
                WHERE id = ?
                LIMIT 1
                """,
                (str(attempt_id),),
            )

            row = cursor.fetchone()

            if not row:
                return None

            attempt = dict(row)
            attempt["answers"] = json.loads(
                attempt["answers"] or "[]"
            )

            return attempt

        finally:
            connection.close()

    def get_user_attempts(self, user_id=None, page=0, page_size=20):
        start = page * page_size

        connection = sqlite3.connect(self.db_path, timeout=30,)
        connection.row_factory = sqlite3.Row

        try:
            cursor = connection.execute(
                """
                SELECT *
                FROM quiz_attempts
                ORDER BY completed_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (page_size, start),
            )

            attempts = []

            for row in cursor.fetchall():
                attempt = dict(row)
                attempt["answers"] = json.loads(
                    attempt["answers"] or "[]"
                )
                attempts.append(attempt)

            return attempts

        finally:
            connection.close()

    def get_attempted_question_ids(self, category_id=None):
        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        try:
            cursor = connection.execute(
                """
                SELECT question_id
                FROM question_first_attempts
                WHERE category_id = ?
                """,
                (str(category_id),),
            )

            return [row[0] for row in cursor.fetchall()]

        finally:
            connection.close()

    def get_pending_question_statistics(self):
        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        try:
            cursor = connection.execute(
                """
                SELECT
                    question_id,
                    is_correct
                FROM question_first_attempts
                WHERE statistics_synced = 0
                ORDER BY attempted_at ASC
                """
            )

            return [
                dict(row)
                for row in cursor.fetchall()
            ]

        finally:
            connection.close()

    def mark_question_statistics_synced(self, question_id):
        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        try:
            with connection:
                connection.execute(
                    """
                    UPDATE question_first_attempts
                    SET statistics_synced = 1
                    WHERE question_id = ?
                    """,
                    (str(question_id),),
                )

        finally:
            connection.close()

    def is_question_saved(self, question_id):
        connection = sqlite3.connect(self.db_path, timeout=30,)
        try:
            cursor = connection.execute(
                """
                SELECT 1
                FROM question_saves
                WHERE question_id = ?
                """,
                (str(question_id),),
            )
            return cursor.fetchone() is not None
        finally:
            connection.close()


    
    def toggle_question_save(self, question_id):
        question_id = str(question_id)

        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        try:
            connection.execute("BEGIN IMMEDIATE")

            cursor = connection.execute(
                """
                SELECT 1
                FROM question_saves
                WHERE question_id = ?
                """,
                (question_id,),
            )

            is_saved = cursor.fetchone() is not None

            if is_saved:
                # Always allow unsaving.
                connection.execute(
                    """
                    DELETE FROM question_saves
                    WHERE question_id = ?
                    """,
                    (question_id,),
                )

                saved = False

            else:
                # Check the current number of saved questions.
                cursor = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM question_saves
                    """
                )

                saved_count = cursor.fetchone()[0]

                if saved_count >= 200:
                    connection.rollback()
                    return None

                connection.execute(
                    """
                    INSERT INTO question_saves (question_id)
                    VALUES (?)
                    """,
                    (question_id,),
                )

                saved = True

            connection.execute(
                """
                INSERT INTO question_save_sync (
                    question_id,
                    is_saved,
                    synced_state,
                    updated_at
                )
                VALUES (
                    ?,
                    ?,
                    COALESCE(
                        (
                            SELECT synced_state
                            FROM question_save_sync
                            WHERE question_id = ?
                        ),
                        0
                    ),
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT(question_id)
                DO UPDATE SET
                    is_saved = excluded.is_saved,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    question_id,
                    int(saved),
                    question_id,
                ),
            )

            connection.commit()
            return saved

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def get_saved_question_count(self):
        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        try:
            cursor = connection.execute(
                """
                SELECT COUNT(*)
                FROM question_saves
                """
            )

            return cursor.fetchone()[0]

        finally:
            connection.close()

    def get_saved_question_ids(self, page=0, page_size=20):
        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        try:
            cursor = connection.execute(
                """
                SELECT question_id
                FROM question_saves
                ORDER BY saved_at DESC
                LIMIT ? OFFSET ?
                """,
                (page_size, page * page_size),
            )

            return [row[0] for row in cursor.fetchall()]

        finally:
            connection.close()

    def get_saved_questions(self, quiz_service, page=0, page_size=20):
        question_ids = self.get_saved_question_ids(
            page=page,
            page_size=page_size,
        )

        if not question_ids:
            return []

        try:
            return quiz_service.get_questions_by_ids(question_ids)

        except Exception as error:
            print("COULD NOT LOAD SAVED QUESTIONS:", error)
            return []

    
    def get_pending_question_saves(self):
        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )
        connection.row_factory = sqlite3.Row

        try:
            cursor = connection.execute(
                """
                SELECT
                    question_id,
                    is_saved,
                    synced_state,
                    (is_saved - synced_state) AS delta
                FROM question_save_sync
                WHERE is_saved != synced_state
                ORDER BY updated_at ASC
                """
            )

            return [
                dict(row)
                for row in cursor.fetchall()
            ]

        finally:
            connection.close()

    def mark_question_save_synced(self, question_id, synced_state):
        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        try:
            with connection:
                connection.execute(
                    """
                    UPDATE question_save_sync
                    SET synced_state = ?
                    WHERE question_id = ?
                    AND is_saved = ?
                    """,
                    (
                        int(synced_state),
                        str(question_id),
                        int(synced_state),
                    ),
                )

        finally:
            connection.close()


    def update_attempt_category_ids(self, question_categories):
        """
        Update category IDs for existing first-attempt records.

        question_categories: {
            question_id: category_id
        }
        """
        if not question_categories:
            return

        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        try:
            connection.executemany(
                """
                UPDATE question_first_attempts
                SET category_id = ?
                WHERE question_id = ?
                AND category_id IS NULL
                """,
                [
                    (str(category_id), str(question_id))
                    for question_id, category_id
                    in question_categories.items()
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def get_attempts_missing_category(self):
        connection = sqlite3.connect(
            self.db_path,
            timeout=30,
        )

        try:
            cursor = connection.execute(
                """
                SELECT question_id
                FROM question_first_attempts
                WHERE category_id IS NULL
                """
            )

            return [row[0] for row in cursor.fetchall()]

        finally:
            connection.close()


if __name__ == "__main__":
    local_db = LocalDatabaseService()
    # quiz_service = QuizService(supabase)

    missing_ids = local_db.get_attempts_missing_category()

    print(f"Records to update: {len(missing_ids)}")

