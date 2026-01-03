import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.tools.tavily import TavilyTools
from agno.db.sqlite.sqlite import SqliteDb
from agno.tools.reasoning import ReasoningTools
from agent.memory_controller import StressMemory
from agent.guardrails import Guardrails, create_safe_process_entry
from textblob import TextBlob
from agent.prompts import COMBINED_PROMPT as combined_prompt
from emotion_utils import analyze_emotions_for_tool
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
# 5️⃣ CLI Loop
if __name__ == "__main__":
    agent_os.serve(app="main:app", reload=True)
# # Create safe process_entry with guardrails
# process_entry = create_safe_process_entry(memory, agent, guardrails)


# # 5️⃣ CLI Loop
# if __name__ == "__main__":
#     print("╔════════════════════════════════════════════════════╗")
#     print("║        💭 Stress Journal Agent - SAIW 💭          ║")
#     print("║              Type 'exit' to quit                   ║")
#     print("╚════════════════════════════════════════════════════╝\n")
    
#     while True:
#         try:
#             user_input = input("You: ").strip()
            
#             # Handle special commands
#             if user_input.lower() == "exit":
#                 print("\n👋 Goodbye! Remember to take care of yourself.\n")
#                 break
            
#             if not user_input:
#                 continue
            
#             # Process with guardrails
#             response = process_entry(user_input)
            
#             # Handle crisis detection (None return value)
#             if response is None:
#                 # Crisis detected - display appropriate resources
#                 is_crisis, crisis_type = guardrails.check_crisis(user_input)
#                 if crisis_type == "severe_self_harm":
#                     print("""
# ╔══════════════════════════════════════════════════════════════╗
# ║              🚨 IMMEDIATE CRISIS SUPPORT 🚨                  ║
# ║           YOU ARE NOT ALONE - HELP IS AVAILABLE NOW          ║
# ╚══════════════════════════════════════════════════════════════╝

# ⚠️  THIS IS A MENTAL HEALTH EMERGENCY ⚠️

# Your safety is the priority. Please reach out to a trained crisis counselor IMMEDIATELY:

# 📞 CALL 988 (National Suicide Prevention Lifeline)
#    • Available 24/7 • Free • Confidential
#    • Call or text 988 from any phone

# 📞 INTERNATIONAL Crisis Support:
#    • Crisis Text Line: Text HOME to 741741
#    • International Association for Suicide Prevention:
#      https://www.iasp.info/resources/Crisis_Centres/

# 🚑 IF IN IMMEDIATE DANGER:
#    • CALL 911 (US Emergency Services)
#    • GO TO YOUR NEAREST EMERGENCY ROOM
#    • Tell someone you trust right now

# 💙 REMEMBER:
#    • Your life has value and meaning
#    • These feelings can change with proper support
#    • Mental health professionals are trained to help
#    • You deserve to live and feel better
# """)
#                 elif crisis_type == "severe_harm_others":
#                     print("""
# ╔══════════════════════════════════════════════════════════════╗
# ║              🚨 CRISIS - URGENT ACTION NEEDED 🚨             ║
# ║              THOUGHTS OF HARMING OTHERS DETECTED             ║
# ╚══════════════════════════════════════════════════════════════╝

# ⚠️  THIS IS A SERIOUS MENTAL HEALTH EMERGENCY ⚠️

# If you are having thoughts of harming others, professional help is critical:

# 📞 CALL 911 or go to the Emergency Room immediately

# 📞 Crisis Support Lines:
#    • National Suicide Prevention Lifeline: 988
#    • Crisis Text Line: Text HOME to 741741
#    • SAMHSA National Helpline: 1-800-662-4357

# 🏥 IN-PERSON HELP:
#    • Go to your nearest Emergency Room
#    • Tell them about your thoughts and feelings
#    • They have trained professionals to help

# 💙 IMPORTANT:
#    • Violent thoughts are a symptom that treatment can help
#    • Professional intervention prevents tragedy
#    • Many people recover with proper care
# """)
#                 elif crisis_type == "severe_crisis":
#                     print("""
# ╔══════════════════════════════════════════════════════════════╗
# ║                  💙 CRISIS SUPPORT 💙                        ║
# ║            YOU ARE EXPERIENCING SEVERE DISTRESS              ║
# ║          PROFESSIONAL HELP CAN MAKE A DIFFERENCE             ║
# ╚══════════════════════════════════════════════════════════════╝

# ⚠️  YOU NEED PROFESSIONAL MENTAL HEALTH SUPPORT ⚠️

# The feelings you're experiencing require professional care. Please reach out:

# 📞 CALL 988 (National Suicide Prevention Lifeline)
#    • Talk to a trained counselor
#    • Available 24/7, free, confidential
#    • Call or text

# 📞 Other Support:
#    • Crisis Text Line: Text HOME to 741741
#    • SAMHSA National Helpline: 1-800-662-4357

# 🏥 MENTAL HEALTH PROFESSIONALS:
#    • Call your local emergency room
#    • Find a therapist/psychiatrist
#    • Contact NAMI: nami.org
#    • Find treatment: findhelp.org
# """)
#             else:
#                 print(f"\nAgent: {response}\n")
            
#         except KeyboardInterrupt:
#             print("\n\n👋 Goodbye! Take care of yourself.\n")
#             break
#         except Exception as e:
#             print(f"\n❌ An unexpected error occurred: {str(e)}")
#             print("Please try again or contact support.\n")
