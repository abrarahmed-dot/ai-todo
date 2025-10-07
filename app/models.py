from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    completed: int = 1 # SQLite stores booleans as 0/1

    def __str__(self) -> str:
        status = "✔" if bool(self.completed) else " "
        due = self.due_date if self.due_date else "—"
        desc = f" — {self.description}" if self.description else ""
        return f"[{status}] {self.id}. {self.title} (Due: {due}){desc}"
    
