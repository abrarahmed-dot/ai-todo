import os
from dotenv import load_dotenv
from app.logging_config import configure_logging
from app.db import TodoApp
from app.cli import run_cli


def main() -> None:
    load_dotenv()
    configure_logging()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY not set. Exiting.")

    app = TodoApp(db_name="todo.db")
    run_cli(api_key, app)


if __name__ == "__main__":
    main()