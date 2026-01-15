# Stress Journal AI Agent
## Preliminary Implementation


## 1. System Overview

The Stress Journal AI Agent is a mental health support chatbot designed to provide compassionate stress monitoring, emotion analysis, and personalized guidance. Built with Python, the Agno framework, and OpenAI's GPT-4o-mini model, it integrates persistent memory storage, advanced guardrails, and emotion detection to create a safe, supportive experience for users documenting their mental health journey.

### Interface & Framework

**Agno Framework & UI**

The application is built on the Agno framework, which provides a powerful agent orchestration system with built-in UI capabilities. Agno handles agent initialization, tool management, and conversation flow management. The framework exposes a FastAPI-based web interface (accessible via Agno's UI) that provides a user-friendly chat interface for interacting with the agent. Users access the agent through Agno's web portal [[1]], where they can engage in real-time conversations, view memory retrieval context, and access crisis resources. The framework also provides REST API endpoints for programmatic access and integrates CORS middleware to support multiple client origins.

### Key Components

**Agent Framework & Tool System**

Built on the Agno framework, the agent leverages OpenAI's GPT-4o-mini model as its core language model. The framework manages a comprehensive tool ecosystem including: emotion analysis for sentiment detection, memory management for context retrieval, content safety checking, reasoning tools for deeper analysis, and Tavily web search for current information. The Agno framework automatically exposes these tools to the LLM, allowing the agent to decide when and how to use them during conversations.

**Guardrails System**

A comprehensive safety system protects users by validating input for harmful content, detecting crisis indicators, and filtering agent responses for sensitive information. Beyond the input/output wrapper layer, guardrails are also exposed as an LLM tool function (`check_content_safety`) that allows the agent to proactively check content before processing and provide informed, empathetic responses when safety concerns are detected.

**Database:** SQLite database (agno.db) stores agent conversation history, providing context for recent interactions and enabling the agent to recall important discussion points from the current session.

## 2. Core Implementation

### Memory Controller Architecture

The agent uses Mem0 cloud API [[2]] for persistent, categorized memory that spans across user sessions. All user entries are automatically stored with the consistent user ID "stress_journal_user," enabling the agent to recall previous conversations and provide contextual, personalized responses without requiring users to re-explain their situation.

For storing the memory, the user entries are saved using `save(text, user)` which converts text into Mem0 message format with a consistent user ID ("stress_journal_user"). This ensures all entries are attributed to the same user across sessions, enabling continuous context accumulation without fragmentation across multiple user accounts.

Memory's retrieval is done by the `search(query, user)` method, performing semantic similarity searches across all stored memories. When a user submits new text, the agent searches for relevant past entries using natural language queries. This returns the most contextually similar previous conversations, enabling the agent to recognize patterns, remember previous discussions, and provide responses that acknowledge historical context.

The system is also making use of an SQLite database that stores the current conversation history. This provides immediate context for recent interactions within the Agno framework, enabling the agent to reference what was discussed minutes ago without requiring memory searches.

### Emotion Analysis System

The emotion analysis is an important part for the agent's purpose and it is also done by tool calling. The emotion analysis tool has defined two layers of inspecting the user's input.

At first, the tool starts by determining a category for the input using a transformer-based classification. The system uses the a transformer model to classify text into detailed emotion categories: anger, disgust, fear, joy, neutral, sadness, and surprise. This DistilRoBERTa-based model provides nuanced emotion detection beyond simple keyword matching, capturing context and linguistic subtleties. 

Continuing with a TextBlob's sentiment analysis in order to provide polarity scores (-1 to 1, where -1 is highly negative and 1 is highly positive). The system combines transformer predictions with polarity to calculate: primary emotion - the highest-confidence emotion from the transformer model,stress level: a 0-100 scale score calculated by aggregating stress-inducing emotions (anger, fear, disgust) and adjusted by overall sentiment polarity, emotion categories: mapped to five user-facing categories (stress, joy, sadness, anger, neutral) for clarity.

If the transformer model fails to load, the system gracefully falls back to TextBlob-only analysis, ensuring the agent remains functional with reduced emotion detection capability.

The emotion analysis is exposed as the `analyze_emotions_tool` that the LLM can invoke, returning JSON with `emotion`, `polarity`, and `stress_level` for informed decision-making during conversations.

### Tavily Web Search Integration

The Tavily search tool [[3]] is integrated into the Agno framework's tool ecosystem, allowing the agent to fetch different types of information when needed, such as new definitions for affections or therapy guidelines. The agent can use Tavily to: find current mental health resources, therapy techniques, or coping strategies, locate crisis hotlines, support groups, or local mental health services, retrieve information about specific mental health topics, stress management techniques, or wellness practices, access recent research or evidence-based recommendations.

Tavily requires an API key stored in the enviroment configuration. The tool is conditionally available to the agent - if the API key is not configured, the agent still functions without search capability but loses access to real-time information retrieval.

### Safetiness

The safetiness of the conversation is mentained by the  guardrails' implementation,  a comprehensive validation system with a LLM-accessible tools. In order to have a reliable tool that offers a good feedback on the direction where the conversation is heading, there are two layers of analysis.

Starting with an input validation layer, it performs preliminary safety checks on all user messages. It validates that input is not empty, falls within acceptable length constraints (2-5000 characters), and does not contain harmful content patterns. The validation uses regex patterns to detect variations of harmful intent rather than exact phrase matching, enabling detection of statements like "hurt my teacher" or "cut my wrist" even when phrased differently.

When input passes validation, the system checks for crisis indicators across three severity levels: severe self-harm indicators include keywords related to suicide, self-injury, and suicidal ideation, severe harm-to-others indicators detect violent intent toward specific individuals like teachers, family members, or coworkers, severe emotional crisis indicators identify expressions of hopelessness, worthlessness, and desire to give up. When a crisis is detected, the system returns appropriate helpline information and resources rather than processing the message normally.

Another key refinement of the response, possible with the help of the guardrails, allows users to discuss their feelings about diagnoses while blocking new diagnosis assertions. The system blocks claims like "I was diagnosed with schizophrenia" or "I have Alzheimer," but allows discussions like "I'm worried about my Alzheimer diagnosis and how it will affect my family." This distinction is crucial for enabling therapeutic conversation about existing conditions while preventing the agent from making or reinforcing medical diagnoses.

The `check_content_safety(text: str)` tool function is exposed to the LLM, allowing the agent to proactively check content safety during conversations. This enables the agent to intelligently respond to safety concerns with empathy, provide crisis resources proactively, and adjust its communication style based on detected content severity.

## 3. Key Takeaways

The Stress Journal AI Agent represents a comprehensive mental health support system that successfully integrates multiple advanced technologies into a coherent, safe platform. 

The guardrails system operates at two levels - input validation, crisis detection - all wrapped in a LLM-accessible tool that enables intelligent, context-aware safety responses.

By persisting memories across sessions, the system eliminates the need for users to repeatedly provide context. The agent can recognize a returning user, recall their previous concerns, and track emotional progress over weeks or months.

The agent intelligently searches memory only when contextually relevant. For new topics, it searches for related entries. For follow-ups, it uses session history. This balances context richness with computational efficiency.

By calling the tavily tool, the agent could access better information that could help the approach, considering that the user could display different affections that need to be treated individually, but all with empaty.

## 4. Conclusion & Future Directions

This implementation establishes a robust foundation for AI-driven mental health support, demonstrating how advanced technologies — persistent memory, multi-layered safety systems, transformer-based emotion analysis, and intelligent tool orchestration — can be seamlessly integrated to create a responsible, compassionate mental health companion. The system successfully balances user safety with genuine support, combining proactive crisis detection with empathetic engagement, all while respecting privacy and maintaining clear boundaries about its role as a supportive tool rather than a medical service.

Improvements include adding mood trend visualization to help users recognize patterns in their emotional cycles, implementing context-aware crisis protocols that leverage user history, and building a library of personalized coping strategies based on detected emotions. These additions would enhance the agent's ability to provide targeted, historically-informed support.

## References

1: https://os.agno.com

2: https://mem0.ai/pricing

3: https://www.tavily.com/


