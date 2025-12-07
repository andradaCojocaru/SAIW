from agno.tools.mem0 import Mem0Tools

def init_memory():
    return Mem0Tools(
        user_id="journal_user_1"
    )

def save_emotion_to_memory(mem0: Mem0Tools, entry: dict):
    """
    Salvează emoția + scor în memorie pentru a crea istoric.
    """
    mem_text = (
        f"Emoție detectată: {entry['emotion']} | "
        f"Polarity: {entry['polarity']:.2f} | "
        f"Stress: {entry['stress_level']}"
    )
    mem0.add_memory(mem_text)

def get_emotional_trend(mem0: Mem0Tools):
    """
    Extrage ultimele 10 emoții din memorie și analizează trendul.
    """
    memories = mem0.search_memory("Emoție detectată", top_k=10)

    if len(memories) < 3:
        return "Insuficiente date pentru trend."

    stress_values = []
    for m in memories:
        if "Stress:" in m["memory"]:
            val = int(m["memory"].split("Stress:")[1].strip())
            stress_values.append(val)

    if not stress_values:
        return "Nicio valoare de stres găsită."

    if stress_values[-1] > stress_values[0]:
        return "Trend stres: în creștere 📈"
    elif stress_values[-1] < stress_values[0]:
        return "Trend stres: în scădere 📉"
    else:
        return "Trend stres: stabil"
