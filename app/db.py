# app/db.py
import sqlite3
import logging
import threading
from typing import List, Optional, Tuple
from .models import Task
import re

class TodoApp:
    def __init__(self, db_name: str = "todo.db"):
        logging.info(f"Initializing TodoApp with DB: {db_name}")
        # One shared connection; no shared cursor
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        # Suggested pragmas for better concurrency on SQLite
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self._writelock = threading.Lock()
        self.create_table()

    def create_table(self) -> None:
        logging.debug("Creating tasks table if not exists.")
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT,
                    completed BOOLEAN NOT NULL
                )
                """
            )
            self.conn.commit()
        finally:
            cur.close()
        logging.info("Tasks table ready.")

    # ---------------- Core CRUD ----------------
    def add_task(self, title: str, description: str | None, due_date: str | None) -> int:
        logging.info(f"Adding task: title='{title}', due_date='{due_date}'")
        with self._writelock:
            cur = self.conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO tasks (title, description, due_date, completed) VALUES (?, ?, ?, ?)",
                    (title, description, due_date, False),
                )
                self.conn.commit()
                task_id = cur.lastrowid
            finally:
                cur.close()
        logging.debug(f"Task added with ID {task_id}")
        return task_id

    def get_all_tasks(self) -> List[Task]:
        logging.info("Retrieving all tasks from DB")
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT * FROM tasks")
            rows = cur.fetchall()
        finally:
            cur.close()
        logging.debug(f"Retrieved {len(rows)} tasks")
        return [Task(*row) for row in rows]

    def update_task(
        self,
        task_id: int,
        title: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
        completed: bool | None = None,
    ) -> bool:
        logging.info(f"Updating task ID {task_id} with new values")
        updates, values = [], []

        if title is not None:
            updates.append("title = ?"); values.append(title)
        if description is not None:
            updates.append("description = ?"); values.append(description)
        if due_date is not None:
            updates.append("due_date = ?"); values.append(due_date)
        if completed is not None:
            updates.append("completed = ?"); values.append(1 if completed else 0)

        if not updates:
            logging.warning(f"No updates provided for task ID {task_id}")
            return False

        values.append(task_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"

        with self._writelock:
            cur = self.conn.cursor()
            try:
                logging.debug(f"Executing UPDATE: {query} with {values}")
                cur.execute(query, values)
                self.conn.commit()
                rowcount = cur.rowcount
            finally:
                cur.close()
        logging.debug(f"Updated {rowcount} row(s)")
        return rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        logging.info(f"Deleting task ID {task_id}")
        with self._writelock:
            cur = self.conn.cursor()
            try:
                cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                self.conn.commit()
                rowcount = cur.rowcount
            finally:
                cur.close()
        if rowcount > 0:
            logging.info(f"Task ID {task_id} deleted")
        else:
            logging.warning(f"Task ID {task_id} not found to delete")
        return rowcount > 0

    def close(self) -> None:
        logging.info("Closing database connection")
        self.conn.close()

    # ---------------- Matching / Idempotency ----------------
    @staticmethod
    def _tokenize(text: str) -> set[str]:
        tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
        stop = {"to", "a", "the", "for", "and", "go"}
        return {t for t in tokens if t not in stop}

    def find_task_by_title(self, title: str) -> Optional[Task]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT * FROM tasks WHERE LOWER(TRIM(title)) = LOWER(TRIM(?)) LIMIT 1",
                (title,),
            )
            row = cur.fetchone()
        finally:
            cur.close()
        return Task(*row) if row else None

    def find_task_by_title_fuzzy(self, title: str, threshold: float = 0.5) -> Optional[Task]:
        target = self._tokenize(title)
        if not target:
            return None
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT * FROM tasks")
            rows = cur.fetchall()
        finally:
            cur.close()
        best_row, best_score = None, 0.0
        for row in rows:
            t = self._tokenize(row[1])  # title
            union = target | t
            if not union:
                continue
            score = len(target & t) / len(union)
            if score > best_score:
                best_score, best_row = score, row
        if best_row and best_score >= threshold:
            logging.debug(f"Fuzzy match {best_score:.2f} for '{title}' -> '{best_row[1]}' (ID {best_row[0]})")
            return Task(*best_row)
        return None

    def upsert_task(
        self,
        title: str,
        description: str | None,
        due_date: str | None,
        completed: bool | None = None,
        use_fuzzy: bool = True,
    ) -> Tuple[int, bool, Task | None]:
        existing = self.find_task_by_title(title)
        if use_fuzzy and not existing:
            existing = self.find_task_by_title_fuzzy(title)

        if existing:
            new_desc = description if description is not None else existing.description
            new_due = due_date if due_date is not None else existing.due_date
            new_completed = existing.completed if completed is None else (1 if completed else 0)
            self.update_task(
                existing.id,
                description=new_desc,
                due_date=new_due,
                completed=bool(new_completed),
            )
            return existing.id, True, existing

        new_id = self.add_task(title, description, due_date)
        return new_id, False, None
