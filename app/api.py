# app/api.py
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from app.logging_config import configure_logging
from app.db import TodoApp
from app.agent import create_agent_executor

class CommandRequest(BaseModel):
    input: str

class CommandResponse(BaseModel):
    output: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    configure_logging()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    db_path = os.getenv("TODO_DB", "todo.db")
    app.state.db = TodoApp(db_name=db_path)
    app.state.agent = create_agent_executor(api_key, app.state.db)
    try:
        yield
    finally:
        app.state.db.close()

app = FastAPI(title="AI Todo API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "hello": "AI Todo API",
        "try": {
            "health": "GET /health",
            "docs": "GET /docs",
            "agent": "POST /agent  body: {\"input\": \"show all tasks\"}"
        }
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/agent", response_model=CommandResponse)
async def agent_endpoint(req: CommandRequest):
    try:
        result = await app.state.agent.ainvoke({"input": req.input})
        output = result.get("output")
        if output is None:
            # Be defensive in case the agent returns something unexpected
            output = str(result)
        return CommandResponse(output=output)
    except Exception as e:
        logging.exception("Agent invocation failed")
        raise HTTPException(status_code=500, detail=str(e))
