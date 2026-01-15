import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.tools.tavily import TavilyTools
from agno.db.sqlite.sqlite import SqliteDb
from agno.tools.reasoning import ReasoningTools
from agent.memory_controller import StressMemory
from agent.guardrails import Guardrails
from textblob import TextBlob
from agent.prompts import COMBINED_PROMPT as combined_prompt
from emotion_utils import analyze_emotions_for_tool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

load_dotenv()

# 1️⃣ Memorie
memory = StressMemory()
db = SqliteDb(db_file="agno.db")

# Initialize guardrails
guardrails = Guardrails()


# Expose callable functions (top-level) so AGNO can validate and add them as tools.
def analyze_emotions_tool(text: str) -> str:
    """Analyze text and return emotion, polarity and stress level as JSON string."""
    emotion, stress_level, polarity = analyze_emotions_for_tool(text)
    out = {"emotion": emotion, "polarity": polarity, "stress_level": stress_level}
    return json.dumps(out)


def memory_save(text: str, user: str = None) -> str:
    """Save a text entry to persistent memory."""
    return memory.save(text, user=user)


def memory_search(query: str, user: str = None) -> list:
    """Search memory for similar entries; returns a list-like result."""
    res = memory.search(query=query, user=user)
    try:
        return list(res)
    except Exception:
        return res


def memory_delete(query_or_id: str, user: str = None) -> list:
    """Delete memory entries by id or by searching for the provided query.

    Returns a list of deleted ids when possible, or raises NotImplementedError
    if the underlying memory client does not support deletion.
    """
    return memory.delete(query_or_id, user=user)


def check_content_safety(text: str) -> str:
    """
    Check if text is safe and get guardrails feedback.
    
    Use this tool to check if user content triggers any guardrail alerts:
    - Crisis detection (self-harm, suicide, harm to others)
    - Inappropriate content
    - Medical diagnosis claims
    
    Returns JSON with:
    - is_safe: true/false
    - crisis_detected: crisis type (if any)
    - crisis_message: helpful message if crisis detected
    - validation_errors: list of validation errors
    """
    return guardrails.check_content_safety(text)


# 2️⃣ Model OpenAI
chat_model = OpenAIChat(id="gpt-4o-mini")

def process_entry(user_text: str):
    # Save the raw user entry so the agent can use or augment it via the memory tool.
    memory.save(f"User entry: {user_text}")

    # Provide short context and tell the agent which tools are available and their outputs.
    # `analyze_emotions` returns JSON: {"emotion","polarity","stress_level"}
    similar = memory.search(query=user_text)
    similar_list = list(similar)
    similar_text = "\n".join(similar_list[:5]) if similar_list else "Niciun eveniment similar în memorie."
    
agent = Agent(
    name="stress-journal-agent",
    model=chat_model,
    db=db,
    tools=[
        memory_save,
        memory_search,
        memory_delete,
        analyze_emotions_tool,
        check_content_safety,
        ReasoningTools(add_instructions=True),
        TavilyTools(api_key=os.getenv("TAVILY_API_KEY"))
    ],
    instructions=combined_prompt,
    markdown=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=3
)

agent_os = AgentOS(
    id="my-first-os",
    description="My first AgentOS",
    agents=[agent],
)

app = agent_os.get_app()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://os.agno.com", "http://localhost:3000", "http://localhost:7777"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📝 Pydantic model for API input
class UserInput(BaseModel):
    text: str

if __name__ == "__main__":
    agent_os.serve(app="main:app", reload=True)
