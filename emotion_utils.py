from transformers import pipeline
from textblob import TextBlob
import warnings
warnings.filterwarnings('ignore')

# Initialize the emotion classifier
try:
    emotion_classifier = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=None
    )
    print("Transformer model loaded successfully")
except Exception as e:
    print(f"Warning: Could not load transformer model: {e}")
    print("Falling back to TextBlob-based analysis")
    emotion_classifier = None


def analyze_emotions(text: str):
    """Main emotion analysis function using transformer model.
    
    Returns dict with:
    - emotion (joy, sadness, anger, fear, stress, neutral)
    - polarity (-1..1)
    - stress_level (0..100)
    """
    polarity = TextBlob(text).sentiment.polarity
    
    # Use transformer model if available
    if emotion_classifier is not None:
        try:
            predictions = emotion_classifier(text[:512])[0]  # Limit to 512 tokens
            # Get emotion scores from transformer
            emotion_scores = {pred['label']: pred['score'] for pred in predictions}
            
            # Map transformer emotions to our categories
            # The model detects: anger, disgust, fear, joy, neutral, sadness, surprise
            stress_emotions = ['anger', 'fear', 'disgust']
            stress_score = sum(emotion_scores.get(e, 0) for e in stress_emotions)
            
            # Determine primary emotion
            top_emotion = max(predictions, key=lambda x: x['score'])
            
            if top_emotion['label'] in stress_emotions and top_emotion['score'] > 0.3:
                emotion = "stress"
                stress_level = min(100, int(stress_score * 100))
            elif top_emotion['label'] == 'joy' or top_emotion['label'] == 'surprise':
                emotion = "joy"
                stress_level = max(0, int((1 - emotion_scores.get('joy', 0)) * 50))
            elif top_emotion['label'] == 'sadness':
                emotion = "sadness"
                stress_level = int(emotion_scores.get('sadness', 0) * 70)
            else:
                emotion = "neutral"
                stress_level = int(stress_score * 60)
            
            # Also check for Romanian stress keywords
            text_l = text.lower()
            if any(w in text_l for w in ["stres", "anxiet", "îngrijorat", "panică"]):
                stress_level = max(stress_level, 75)
                if emotion == "neutral":
                    emotion = "stress"
                    
        except Exception as e:
            print(f"Transformer analysis failed: {e}, falling back to TextBlob")
            # Fallback to TextBlob-based analysis
            emotion, stress_level = _textblob_fallback(text, polarity)
    else:
        # Fallback to TextBlob-based analysis
        emotion, stress_level = _textblob_fallback(text, polarity)
    
    return {
        "emotion": emotion,
        "polarity": polarity,
        "stress_level": int(max(0, min(100, stress_level)))
    }


def _textblob_fallback(text: str, polarity: float):
    """Fallback emotion analysis using TextBlob."""
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
    return emotion, stress_level


def analyze_emotions_for_tool(text: str):
    """Helper that returns (emotion, stress_level, polarity) tuple for backwards compatibility."""
    result = analyze_emotions(text)
    return result['emotion'], result['stress_level'], result['polarity']
