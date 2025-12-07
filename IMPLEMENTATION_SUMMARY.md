# Stress Journal AI Agent
## Preliminary Implementation


## 1. System Overview

The Stress Journal AI Agent is a mental health support chatbot designed to provide compassionate stress monitoring, emotion analysis, and personalized guidance through a command-line interface. Built with Python, the Agno framework, and OpenAI's GPT-4o-mini model, it integrates persistent memory storage, advanced guardrails, and emotion detection to create a safe, supportive experience for users documenting their mental health journey.

### Key Components

**Memory System:** The agent uses Mem0 cloud API for persistent, categorized memory that spans across user sessions. All user entries are automatically stored with the consistent user ID "stress_journal_user," enabling the agent to recall previous conversations and provide contextual, personalized responses without requiring users to re-explain their situation.

**Agent Framework:** Built on the Agno framework, the agent leverages OpenAI's GPT-4o-mini model as its core language model. The framework integrates multiple tools including emotion analysis for sentiment detection, memory management for context retrieval, reasoning tools for deeper analysis, and Tavily web search for current information when needed.

**Guardrails System:** A comprehensive three-layer safety system protects users by validating input for harmful content, detecting crisis indicators, and filtering agent responses for sensitive information. The guardrails use pattern-based detection rather than fixed-phrase matching, allowing flexibility to catch variations in how users express harmful intent.

**Sentiment Analysis:** TextBlob provides polarity detection on a -1 to 1 scale, which is combined with keyword-based emotion classification to identify stress, joy, sadness, or neutral emotional states. Stress levels are calculated on a 0-100 scale with heuristic adjustments based on detected emotions.

**Database:** SQLite database (agno.db) stores agent conversation history, providing context for recent interactions and enabling the agent to recall important discussion points from the current session.

## 2. Core Implementation

### Guardrails Architecture

The guardrails implement a three-layer validation pipeline that processes both user inputs and agent responses:

**Input Validation Layer:** This layer performs preliminary safety checks on all user messages. It validates that input is not empty, falls within acceptable length constraints (2-5000 characters), and does not contain harmful content patterns. The validation uses regex patterns to detect variations of harmful intent rather than exact phrase matching, enabling detection of statements like "hurt my teacher" or "cut my wrist" even when phrased differently.

**Crisis Detection Layer:** When input passes validation, the system checks for crisis indicators across three severity levels. Severe self-harm indicators include keywords related to suicide, self-injury, and suicidal ideation. Severe harm-to-others indicators detect violent intent toward specific individuals like teachers, family members, or coworkers. Severe emotional crisis indicators identify expressions of hopelessness, worthlessness, and desire to give up. When a crisis is detected, the system returns appropriate resources rather than processing the message normally.

**Output Filtering Layer:** The agent's responses are filtered to remove or mask sensitive information including email addresses, phone numbers, Social Security numbers, and URLs. The system also flags medical diagnosis claims in responses, ensuring the agent does not make or reinforce medical diagnoses, while still allowing discussions about emotions related to existing diagnoses.

### Harm Detection Strategy

The system moved from fixed-phrase blocking to pattern-based detection for greater flexibility. Self-harm patterns capture variations like "cut my wrist," "hurt myself," "want to die," and related expressions. Harm-to-others patterns detect statements combining harm verbs (kill, hurt, attack) with specific targets (my teacher, my boss, my family). This approach significantly reduces false positives while catching genuine harmful content expressed in different ways.

**Medical Claim Detection:** A key refinement allows users to discuss their feelings about diagnoses while blocking new diagnosis assertions. The system blocks claims like "I was diagnosed with schizophrenia" or "I have Alzheimer," but allows discussions like "I'm worried about my Alzheimer diagnosis and how it will affect my family." This distinction is crucial for enabling therapeutic conversation about existing conditions while preventing the agent from making or reinforcing medical diagnoses.

### Memory Management

All user entries are automatically saved to persistent Mem0 storage. When users return in new sessions, the agent searches the memory system to recall relevant past conversations. This continuity eliminates the need for users to re-explain their situation and allows the agent to recognize patterns in their stress, emotional state, and life circumstances. The agent uses these memories to provide contextual responses that acknowledge the user's history and track their emotional progress.

## 3. Safety & Compliance

### Crisis Response Protocol

When the guardrails detect a crisis, the system responds appropriately based on severity. For self-harm crises, users receive information about the 988 National Suicide Prevention Lifeline, Crisis Text Line, and emergency services, along with reassuring messages about recovery and the value of their life. For harm-to-others crises, the response emphasizes the need for professional psychiatric evaluation and emergency intervention. For severe emotional crises, users receive information about mental health resources including therapist finders and crisis support lines.

These responses are formatted for immediate readability with clear calls-to-action and emphasize the importance of professional help. Rather than processing the user's message through the agent, the system prioritizes getting them to appropriate resources.

### Logging & Monitoring

The system maintains detailed logging for all safety-critical events. Crisis detections are logged at CRITICAL level for immediate visibility. Input validation failures and blocked content are logged at WARNING level. All logging is configured to suppress verbose external library noise (urllib3, httpx, openai, mem0) to keep the output clean and focused on application-level events.

### Limitations & Professional Care

The agent explicitly acknowledges its limitations. The agent cannot provide medical diagnoses, psychiatric treatment, or professional mental health care. All interactions are designed to complement professional mental health services, not replace them. Users are consistently directed toward healthcare professionals for medical concerns and crisis situations.

## 4. Future Implementations

### UI/UX Enhancements

**Web Dashboard:** A potential web interface could display conversation history, mood trend charts, and emotional patterns over time. Users could visualize their stress levels across weeks and months, identify patterns, and track progress.

### Enhanced Guardrails

**Advanced Pattern Detection:** Integration with machine learning-based toxicity detection could potentially improve accuracy in distinguishing genuine crises from casual language.

**Context-Aware Filtering:** Future versions might reduce false positives by better understanding context and nuance in user expressions.

**Emotion Tracking:** The system could potentially track emotional patterns across conversations to identify concerning trends early.

### Prompt & Response Improvements

**Personalized Responses:** Future iterations could generate responses more tailored to individual user history and preferred coping strategies.

**Structured Formatting:** Responses could potentially be better organized with clear sections for acknowledgment, validation, suggestions, and resources.
