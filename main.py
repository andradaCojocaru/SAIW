import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agent.memory_controller import StressMemory
from textblob import TextBlob

load_dotenv()

# 1️⃣ Memorie
memory = StressMemory()

# 2️⃣ Model OpenAI
chat_model = OpenAIChat(id="gpt-4o-mini")

# 3️⃣ Creare Agent AGNO fără `rules` sau `system_prompt`
agent = Agent(
    name="stress-journal-agent",
    model=chat_model,
    tools=[memory]  # Memorie persistentă
)

# 4️⃣ Funcții utilitare
def analyze_emotions(text):
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

def process_entry(user_text: str):
    emotion, stress_level = analyze_emotions(user_text)
    print(f"\n👉 Emoție detectată: {emotion}")
    print(f"👉 Nivel stres: {stress_level}/100")

    # Salvează în memorie
    memory.save(f"User entry: {user_text} | Emotion: {emotion} | Stress: {stress_level}")

    # Recuperare ultimele 5 intrări similare
    similar = memory.search(query=user_text)
    similar_list = list(similar)
    similar_text = "\n".join(similar_list[:5]) if similar_list else "Niciun eveniment similar în memorie."

    # Prompt context
    combined_prompt = f"""
User journal entry:
{user_text}

Past similar emotional events:
{similar_text}

Tasks:
- Summarize today's emotional state
- Detect stress triggers
- Suggest 2 coping strategies
- Give empathetic response
"""
    result = agent.run(combined_prompt)
    print("\nAgent:", result.content, "\n")


# 5️⃣ CLI Loop
if __name__ == "__main__":
    print("Agent jurnal emoțional pornit. Scrie cum te simți (exit pentru ieșire).")
    while True:
        msg = input("\nTu: ")
        if msg.lower() in ["exit", "quit"]:
            break
        process_entry(msg)
