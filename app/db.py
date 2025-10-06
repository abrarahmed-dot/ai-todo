import sqlite3
import logging
from typing import List
from .models import Task


class TodoApp:
    def __init__(self, db_name: str = "todo.db"):
        logging.info(f"Initializing TodoApp with DB: {db_name}")
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self) -> None:
        logging.debug("Creating tasks table if not exists.")
        self.cursor.execute(
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
        logging.info("Tasks table ready.")

    def add_task(self, title: str, description: str | None, due_date: str | None) -> int:
        logging.info(f"Adding task: title='{title}', due_date='{due_date}'")
        self.cursor.execute(
            "INSERT INTO tasks (title, description, due_date, completed) VALUES (?, ?, ?, ?)",
            (title, description, due_date, False),
        )
        self.conn.commit()
        task_id = self.cursor.lastrowid
        logging.debug(f"Task added with ID {task_id}")
        return task_id

    def get_all_tasks(self) -> List[Task]:
        logging.info("Retrieving all tasks from DB")
        self.cursor.execute("SELECT * FROM tasks")
        rows = self.cursor.fetchall()
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
            updates.append("title = ?")
            values.append(title)
        if description is not None:
            updates.append("description = ?")
            values.append(description)
        if due_date is not None:
            updates.append("due_date = ?")
            values.append(due_date)
        if completed is not None:
            updates.append("completed = ?")
            values.append(1 if completed else 0)

        if updates:
            values.append(task_id)
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            logging.debug(f"Executing UPDATE: {query} with {values}")
            self.cursor.execute(query, values)
            self.conn.commit()
            rowcount = self.cursor.rowcount
            logging.debug(f"Updated {rowcount} row(s)")
            return rowcount > 0

        logging.warning(f"No updates provided for task ID {task_id}")
        return False

    def delete_task(self, task_id: int) -> bool:
        logging.info(f"Deleting task ID {task_id}")
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        rowcount = self.cursor.rowcount
        if rowcount > 0:
            logging.info(f"Task ID {task_id} deleted")
        else:
            logging.warning(f"Task ID {task_id} not found to delete")
        return rowcount > 0

    def close(self) -> None:
        logging.info("Closing database connection")
        self.conn.close()