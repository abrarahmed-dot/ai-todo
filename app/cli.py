import logging
from datetime import datetime
from .db import TodoApp
from .agent import create_agent_executor


def run_cli(api_key: str, app: TodoApp) -> None:
    agent_executor = create_agent_executor(api_key, app)

    while True:
        logging.info("Showing menu")
        print("\nTodo App Menu:")
        print("1. Add Task")
        print("2. View All Tasks")
        print("3. Update Task")
        print("4. Delete Task")
        print("5. Exit")
        print("6. AI-Assisted Todo Command")
        choice_raw = input("Enter 1-6 **or type a command**: ").strip()

        # Natural-language command directly from the menu
        if not choice_raw.isdigit() or choice_raw not in {"1", "2", "3", "4", "5", "6"}:
            user_input = choice_raw
            response = agent_executor.invoke({"input": user_input})
            logging.info(f"AI-assisted command (direct) result: {response.get('output')}")
            print(response.get("output"))
            continue

        choice = choice_raw

        try:
            if choice == "1":
                title = input("Enter task title: ")
                description = input("Enter task description: ")
                due_date = input("Enter due date (YYYY-MM-DD): ")
                result = agent_executor.invoke({
                    "input": f"Add a task with title '{title}', description '{description}', due date {due_date}",
                })
                logging.info(f"Add task result: {result['output']}")
                print(result["output"])

            elif choice == "2":
                result = agent_executor.invoke({"input": "Show all tasks"})
                logging.info("Show all tasks result:")
                print(result["output"])

            elif choice == "3":
                task_id = int(input("Enter task ID to update: "))
                title = input("New title (or blank): ") or None
                description = input("New description (or blank): ") or None
                due_date = input("New due date (YYYY-MM-DD or blank): ") or None
                completed_str = input("Mark as completed? (y/n or blank): ").lower()
                completed = True if completed_str == 'y' else False if completed_str == 'n' else None
                input_text = f"Update task {task_id}"
                if title:
                    input_text += f" with title '{title}'"
                if description:
                    input_text += f", description '{description}'"
                if due_date:
                    input_text += f", due date {due_date}"
                if completed is not None:
                    input_text += f", completed {completed}"
                result = agent_executor.invoke({"input": input_text})
                logging.info(f"Update task result: {result['output']}")
                print(result["output"])

            elif choice == "4":
                task_id = int(input("Enter task ID to delete: "))
                result = agent_executor.invoke({"input": f"Delete task {task_id}"})
                logging.info(f"Delete task result: {result['output']}")
                print(result["output"])

            elif choice == "5":
                logging.info("User exited the app")
                app.close()
                print("Goodbye!")
                break

            elif choice == "6":
                user_input = input("Enter your task or command in natural language: ")
                current_date = datetime.today().strftime("%Y-%m-%d")
                response = agent_executor.invoke({"input": user_input, "current_date": current_date})
                logging.info(f"AI-assisted command result: {response['output']}")
                print(response["output"])

            else:
                logging.warning(f"Invalid user choice: {choice}")
                print("Invalid choice. Please try again.")

        except Exception as e:
            logging.error(f"Exception in main loop: {e}", exc_info=True)
            print(f"Error: {e}")