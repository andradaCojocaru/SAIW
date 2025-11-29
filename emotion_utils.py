from textblob import TextBlob

def analyze_emotions(text: str):
    """
    Returnează:
    - emotion (joy, sadness, anger, fear, stress, neutral)
    - sentiment polarity (-1..1)
    - stress level (0..100)
    """
    tb = TextBlob(text)
    polarity = tb.sentiment.polarity

    # Heuristică simplă pentru emoție
    text_l = text.lower()
    if any(w in text_l for w in ["stres", "anxiet", "îngrijorat", "panică"]):
        emotion = "stress"
    elif polarity > 0.4:
        emotion = "joy"
    elif polarity < -0.4:
        emotion = "sadness"
    else:
        emotion = "neutral"

    # calcul nivel stres
    stress = 50 - (polarity * 50)
    if emotion == "stress":
        stress = 80

    return {
        "emotion": emotion,
        "polarity": polarity,
        "stress_level": int(max(0, min(100, stress)))
    }
