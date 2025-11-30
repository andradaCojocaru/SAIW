import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.tools.tavily import TavilyTools
from agno.db.sqlite.sqlite import SqliteDb
from agno.tools.reasoning import ReasoningTools
from agent.memory_controller import StressMemory
from textblob import TextBlob
from agent.prompts import COMBINED_PROMPT as combined_prompt
import json

load_dotenv()

# 1️⃣ Memorie
memory = StressMemory()
db = SqliteDb(db_file="agno.db")


# Expose callable functions (top-level) so AGNO can validate and add them as tools.
def analyze_emotions_tool(text: str) -> str:
    """Analyze text and return emotion, polarity and stress level as JSON string."""
    emotion, stress_level, polarity = analyze_emotions_for_tool(text)
    out = {"emotion": emotion, "polarity": polarity, "stress_level": stress_level}
    return json.dumps(out)


def memory_save(text: str, user: str = "default") -> str:
    """Save a text entry to persistent memory."""
    return memory.save(text, user=user)


def memory_search(query: str, user: str = "default") -> list:
    """Search memory for similar entries; returns a list-like result."""
    res = memory.search(query=query, user=user)
    try:
        return list(res)
    except Exception:
        return res


def memory_delete(query_or_id: str, user: str = "default") -> list:
    """Delete memory entries by id or by searching for the provided query.

    Returns a list of deleted ids when possible, or raises NotImplementedError
    if the underlying memory client does not support deletion.
    """
    return memory.delete(query_or_id, user=user)


# 2️⃣ Model OpenAI
chat_model = OpenAIChat(id="gpt-4o-mini")


# 4️⃣ Funcții utilitare
def analyze_emotions(text):
    """Backward-compatible function used locally.

    Returns (emotion, stress_level) as before.
    """
    polarity = TextBlob(text).sentiment.polarity
    text_l = text.lower()
    if any(w in text_l for w in ["stres", "anxiet", "îngrijorat", "panică"]):
        emotion = "stress"
    elif polarity > 0.4:
        emotion = "joy"
    elif polarity < -0.4:
        emotion = "sadness"
    else:
        emotion = "neutral"
    stress_level = 50 - (polarity * 50)
    if emotion == "stress":
        stress_level = 80
    return emotion, round(stress_level)


def analyze_emotions_for_tool(text: str):
    """Helper that returns (emotion, stress_level, polarity) for the tool wrapper."""
    polarity = TextBlob(text).sentiment.polarity
    text_l = text.lower()
    if any(w in text_l for w in ["stres", "anxiet", "îngrijorat", "panică"]):
        emotion = "stress"
    elif polarity > 0.4:
        emotion = "joy"
    elif polarity < -0.4:
        emotion = "sadness"
    else:
        emotion = "neutral"
    stress_level = 50 - (polarity * 50)
    if emotion == "stress":
        stress_level = 80
    return emotion, round(stress_level), polarity

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
        tools=[memory_save, memory_search, memory_delete, analyze_emotions_tool, 
            ReasoningTools(add_instructions=True), TavilyTools(api_key=os.getenv("TAVILY_API_KEY"))],
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


# 5️⃣ CLI Loop
if __name__ == "__main__":
    agent_os.serve(app="main:app", reload=True)