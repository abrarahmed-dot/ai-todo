import os
from datetime import date
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from .tools import get_weather, create_task_tools
from .db import TodoApp


def create_agent_executor(api_key: str, app: TodoApp) -> AgentExecutor:
    os.environ["OPENAI_API_KEY"] = api_key

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    tools = [get_weather, *create_task_tools(app)]

    today_iso = date.today().isoformat()
    tool_help = (
        "You can call these tools when helpful:\n"
        f"Today is {today_iso}. If a user gives a date without a year, assume the current year "
        f"and prefer ISO YYYY-MM-DD when you return due dates.\n"
        "- add_task_tool(title, description, due_date)\n"
        "- get_all_tasks_tool()\n"
        "- update_task_tool(task_id, title, description, due_date, completed)\n"
        "- delete_task_tool(task_id)\n"
        "- get_weather(location, date='today'|'tomorrow')\n"
        "If the user asks for CRUD on tasks, pick the matching tool."
        "Rules: Before creating a new task, first check if it already exists (by title, allow fuzzy match) using get_task_status_tool or by listing tasks."
        "If it exists, prefer update_task_tool over add_task_tool. If it's already completed and the user asks to complete it again, just confirm."
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an AI assistant for a CLI Todo app.\n"
            "Your job is to convert any actionable or scheduled request—anything the user says they want or need to do—"
            "into a todo task, unless the request clearly asks for something else (like weather info).\n\n"

            "Never ask the user what they mean if you can take a reasonable guess. "
            "If the user is vague, make a task with the information you have, and note what is missing if needed.\n"
            "For example: If the user says 'I need to watch a movie,' create a task titled 'Watch a movie'. "
            "If the date or details are missing, leave them blank or as None. Use today’s date for immediate tasks "
            "unless another date is specified.\n"
            
            + tool_help,
            
        ),
        ("human", "{input}"),
        # REQUIRED for tool-calling agent
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True)
    return executor