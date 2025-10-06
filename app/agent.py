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
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an assistant for a CLI Todo app. "
            "Return succinct, user-friendly text. If input is unclear, make a best effort.\n\n"
            + tool_help,
        ),
        ("human", "{input}"),
        # REQUIRED for tool-calling agent
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True)
    return executor