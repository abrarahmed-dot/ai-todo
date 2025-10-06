import logging
import requests
from langchain_core.tools import tool
from .date_utils import normalize_due_date
from .db import TodoApp


@tool
def get_weather(location: str, date: str = "today") -> str:
    """Get the weather forecast for a location on a specific date. Supports 'today' and 'tomorrow'."""
    logging.info(f"Fetching weather for {location} on {date}")
    param = "1" if date == "tomorrow" else "0"
    url = f"https://wttr.in/{location}?{param}&format=Condition:+%C%0ATemperature:+%t"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        logging.debug(f"Weather response: {response.text.strip()}")
        return response.text
    except Exception as e:
        logging.error(f"Failed to get weather: {e}")
        return "Failed to get weather."


def create_task_tools(app: TodoApp):
    """Return CRUD tools bound to the provided `TodoApp` instance."""

    @tool
    def add_task_tool(title: str, description: str = None, due_date: str = None) -> str:
        """Add a task with optional description and due date."""
        logging.info(f"Tool call: add_task_tool with title={title}")
        due_date_iso = normalize_due_date(due_date)
        task_id = app.add_task(title, description, due_date_iso)
        logging.info(f"Task added with ID {task_id} via tool.")
        return f"Task added with ID {task_id}" + (f" (due {due_date_iso})" if due_date_iso else "")

    @tool
    def get_all_tasks_tool() -> str:
        """Retrieve all tasks from the database."""
        logging.info("Tool call: get_all_tasks_tool")
        tasks = app.get_all_tasks()
        if not tasks:
            logging.info("No tasks found.")
            return "No tasks found."
        return "\n".join(str(task) for task in tasks)

    @tool
    def update_task_tool(
        task_id: int,
        title: str = None,
        description: str = None,
        due_date: str = None,
        completed: bool = None,
    ) -> str:
        """Update a task identified by task_id with optional fields."""
        logging.info(f"Tool call: update_task_tool for ID {task_id}")
        due_date_iso = normalize_due_date(due_date)
        success = app.update_task(task_id, title, description, due_date_iso, completed)
        if success:
            logging.info("Task updated successfully via tool.")
            return "Task updated successfully."
        else:
            logging.warning("Task update failed or no changes made via tool.")
            return "Task not found or no changes made."

    @tool
    def delete_task_tool(task_id: int) -> str:
        """Delete a task by task_id."""
        logging.info(f"Tool call: delete_task_tool for ID {task_id}")
        success = app.delete_task(task_id)
        if success:
            logging.info("Task deleted successfully via tool.")
            return "Task deleted successfully."
        else:
            logging.warning("Task delete failed - task not found via tool.")
            return "Task not found."

    return [add_task_tool, get_all_tasks_tool, update_task_tool, delete_task_tool]