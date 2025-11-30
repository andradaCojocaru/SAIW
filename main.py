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

combined_prompt = f"""
Tool specification (available functions):
- `analyze_emotions_tool(text: str) -> str` : Analyze the given `text` and return a JSON string with keys `emotion`, `polarity`, and `stress_level` (e.g. `{{"emotion":"joy","polarity":0.34,"stress_level":33}}`). Use this when you need a precise emotion label or numeric stress estimate.
- `memory_search(query: str) -> list` : Search persistent memory for similar entries. Returns a list of strings (past entries).
- `memory_save(text: str)` : Save a text entry to persistent memory. Use this to store summaries or findings you think will be useful later.

Guidelines for using tools:
- Decide whether to call `analyze_emotions_tool` on the user's entry. If you call it, include the tool output (the JSON) and then use that output in your analysis.
- Use `memory_search` when you want to reference past similar events; show the top matches you used.
- Use `memory_save` to persist helpful summaries or coping suggestions.
- Only call tools when they add value; do not call them redundantly.

Tasks (you may call tools as needed):
- Summarize today's emotional state (use `analyze_emotions_tool` if helpful).
- Detect likely stress triggers (you may use `memory_search` to find patterns).
- Suggest 2 coping strategies tailored to the detected emotion/stress level.
- Give an empathetic response.

Response format:
1) If you call tools, show each tool call and its output (verbatim). Example:
    TOOL CALL: analyze_emotions_tool("user_text")
    TOOL OUTPUT: {{"emotion":"...","polarity":...,"stress_level":...}}
2) Provide the analysis and final recommendations under the header `Final Response:`.

Act autonomously and choose tools as you see fit.
"""
    
agent = Agent(
    name="stress-journal-agent",
    model=chat_model,
    db=db,
    tools=[memory_save, memory_search, analyze_emotions_tool, 
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