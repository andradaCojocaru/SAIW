"""
Guardrails module for Stress Journal Agent
Implements safety measures: input validation, crisis detection, and output filtering
"""

import json
import re
import logging
from collections import defaultdict
from typing import Tuple

# Configure logging - suppress verbose external libraries
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress noisy external libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("mem0").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class Guardrails:
    """Comprehensive guardrails for Stress Journal Agent"""
    
    def __init__(self):
        self.blocked_count = defaultdict(int)
        self.crisis_detected_callbacks = []  # List of functions to call when crisis is detected
        
        # Helpline numbers for crisis support
        self.crisis_helplines = {
            "us": "988",  # US Suicide & Crisis Lifeline
            "uk": "116 123",  # Samaritans UK
            "eu": "+386 4 280 60 60",  # EU Crisis Helpline
            "generic": "988",  # Default/Generic
        }
        
        # Crisis indicators (with severity levels)
        self.crisis_keywords = {
            "severe_self_harm": [
                "suicide", "suicidal", "kill myself", "kill me", 
                "want to die", "end it all", "don't want to live",
                "self-harm", "self harm", "cut myself", "cut myself",
                "hurt myself", "stab myself", "hang myself",
                "poison myself", "overdose", "jump",
            ],
            "severe_harm_others": [
                "hurt someone", "kill someone", "harm someone",
                "violence", "violent", "attack", "hit someone",
                "punch someone", "knife", "gun", "weapon",
            ],
            "severe_crisis": [
                "hopeless", "worthless", "burden", "better off dead",
                "no point", "nothing matters", "give up",
            ]
        }
    
    def register_crisis_callback(self, callback):
        """
        Register a callback function to be called when a crisis is detected.
        
        Args:
            callback: Function that takes (crisis_type: str, text: str) as parameters
        """
        self.crisis_detected_callbacks.append(callback)
    
    def get_crisis_response(self, crisis_type: str) -> str:
        """
        Generate crisis response with helpline information.
        
        Args:
            crisis_type: Type of crisis detected (severe_self_harm, severe_harm_others, severe_crisis)
            
        Returns:
            str: Crisis response message with helpline number
        """
        crisis_messages = {
            "severe_self_harm": (
                "🚨 CRISIS ALERT: SELF-HARM/SUICIDE RISK DETECTED 🚨\n\n"
                "I'm deeply concerned about your safety. Please reach out for immediate support:\n\n"
                "📞 HELPLINE: 988 (US Suicide & Crisis Lifeline)\n"
                "   Text 'HELLO' to 741741 (Crisis Text Line)\n"
                "   International: findahelpline.com\n\n"
                "If you're in immediate danger, please call emergency services (911 in US) or go to the nearest emergency room.\n\n"
                "You matter, and help is available. Please reach out now."
            ),
            "severe_harm_others": (
                "🚨 CRISIS ALERT: HARM TO OTHERS RISK DETECTED 🚨\n\n"
                "This is a serious situation. Please reach out for immediate support:\n\n"
                "📞 HELPLINE: 988 (US Suicide & Crisis Lifeline)\n"
                "   Text 'HELLO' to 741741 (Crisis Text Line)\n"
                "   International: findahelpline.com\n\n"
                "If someone is in immediate danger, please call emergency services (911 in US).\n\n"
                "Support is available. Please reach out now."
            ),
            "severe_crisis": (
                "⚠️ CRISIS ALERT: SEVERE EMOTIONAL CRISIS DETECTED ⚠️\n\n"
                "I'm concerned about your emotional wellbeing. Please reach out for support:\n\n"
                "📞 HELPLINE: 988 (US Suicide & Crisis Lifeline)\n"
                "   Text 'HELLO' to 741741 (Crisis Text Line)\n"
                "   International: findahelpline.com\n\n"
                "Trained counselors are available 24/7 to listen and help.\n\n"
                "You don't have to face this alone. Please reach out now."
            )
        }
        return crisis_messages.get(crisis_type, crisis_messages["severe_crisis"])
    
    def check_crisis(self, text: str) -> Tuple[bool, str]:
        """
        Detect crisis indicators and return crisis type.
        
        Checks for:
        - Self-harm or suicide indicators
        - Harm to others
        - Severe emotional crisis
        
        Returns:
            Tuple[bool, str]: (is_crisis, crisis_type)
        """
        text_lower = text.lower()
        detected_crisis_type = None
        
        # Check for self-harm or suicide (HIGHEST PRIORITY)
        for keyword in self.crisis_keywords.get("severe_self_harm", []):
            if keyword in text_lower:
                logger.critical(f"🚨 SEVERE SELF-HARM/SUICIDE CRISIS DETECTED: '{keyword}'")
                detected_crisis_type = "severe_self_harm"
                break
        
        # Check for harm to others (CRITICAL)
        if not detected_crisis_type:
            for keyword in self.crisis_keywords.get("severe_harm_others", []):
                if keyword in text_lower:
                    logger.critical(f"🚨 SEVERE HARM TO OTHERS CRISIS DETECTED: '{keyword}'")
                    detected_crisis_type = "severe_harm_others"
                    break
        
        # Check for severe emotional crisis
        if not detected_crisis_type:
            for keyword in self.crisis_keywords.get("severe_crisis", []):
                if keyword in text_lower:
                    logger.critical(f"⚠️ SEVERE EMOTIONAL CRISIS DETECTED: '{keyword}'")
                    detected_crisis_type = "severe_crisis"
                    break
        
        # If crisis detected, trigger callbacks
        if detected_crisis_type:
            for callback in self.crisis_detected_callbacks:
                try:
                    callback(detected_crisis_type, text)
                except Exception as e:
                    logger.error(f"Error in crisis callback: {str(e)}")
        
        # Pattern-based detection for harmful content (catches variations)
        self.harm_patterns = {
            # Self-harm patterns
            "self_harm": [
                r"(kill|hurt|harm|cut|stab|poison|overdose|hang|jump).*?(myself|me|my\s+(?:body|wrist|head|arm|leg))",
                r"(want\s+to\s+die|suicide|suicidal|end\s+it\s+all|don't?\s+want\s+to\s+live)",
            ],
            # Harm to others patterns
            "harm_others": [
                r"(kill|hurt|harm|attack|stab|punch|hit|shoot|poison|knife).*?(someone|my\s+(?:teacher|boss|parent|friend|family|partner|colleague|roommate|neighbor|sibling|brother|sister|mother|father|mom|dad)|\w+)",
                r"(want\s+to\s+(?:kill|hurt|harm|attack)|thinking\s+about\s+(?:killing|hurting|harming))",
            ],
        }
    
    def validate_input(self, text: str) -> Tuple[bool, str]:
        """
        Validate user input for safety and quality.
        
        Checks:
        - Not empty
        - Length constraints (2-5000 chars)
        - No harmful patterns (self-harm or harm to others)
        - No suspicious patterns
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Check for empty or whitespace-only input
        if not text or len(text.strip()) == 0:
            return False, "Input cannot be empty."
        
        # Check maximum length (prevent DoS attacks)
        if len(text) > 5000:
            return False, "Input exceeds maximum length (5000 characters). Please shorten your message."
        
        # Check minimum length (prevent noise)
        if len(text) <= 2:
            return False, "Input too short. Please provide more context."
        
        # Check for harmful content patterns
        text_lower = text.lower()
        
        # Check self-harm patterns
        for pattern in self.harm_patterns.get("self_harm", []):
            if re.search(pattern, text_lower):
                logger.warning(f"Self-harm pattern detected in input")
                return False, "This content cannot be processed. If you need support, please reach out to emergency services."
        
        # Check harm-to-others patterns
        for pattern in self.harm_patterns.get("harm_others", []):
            if re.search(pattern, text_lower):
                logger.warning(f"Harm-to-others pattern detected in input")
                return False, "This content cannot be processed. If you need support, please reach out to emergency services."
        
        # Check for medical diagnosis claims (agent cannot diagnose)
        # Only block claims like "I have been diagnosed" or "I have X disease"
        # Allow discussions about existing diagnoses and feelings
        medical_diagnosis_patterns = [
            r'diagnosed?\s+with\s+\w+',  # "diagnosed with X" or "diagnosis with X"
            r'(doctor|physician)\s+(?:told|said|diagnosed).*?(?:with|have)\s+\w+',  # "doctor diagnosed me with X"
            r'i\s+(?:have|got)\s+(?:the\s+)?(?:alzheimer|dementia|parkinson|autism|adhd|bipolar|schizophrenia)',  # Specific diagnoses
        ]
        for pattern in medical_diagnosis_patterns:
            if re.search(pattern, text_lower):
                logger.warning("Medical diagnosis claim detected in user input")
                return False, "⚠️ I cannot provide medical diagnoses. Please consult with a healthcare professional for medical concerns."
        
        return True, ""
    
    def check_crisis(self, text: str) -> Tuple[bool, str]:
        """
        Detect crisis indicators and return crisis type.
        
        Checks for:
        - Self-harm or suicide indicators
        - Harm to others
        - Severe emotional crisis
        
        Returns:
            Tuple[bool, str]: (is_crisis, crisis_type)
        """
        text_lower = text.lower()
        detected_crisis_type = None
        
        # Check for self-harm or suicide (HIGHEST PRIORITY)
        for keyword in self.crisis_keywords.get("severe_self_harm", []):
            if keyword in text_lower:
                logger.critical(f"🚨 SEVERE SELF-HARM/SUICIDE CRISIS DETECTED: '{keyword}'")
                detected_crisis_type = "severe_self_harm"
                break
        
        # Check for harm to others (CRITICAL)
        if not detected_crisis_type:
            for keyword in self.crisis_keywords.get("severe_harm_others", []):
                if keyword in text_lower:
                    logger.critical(f"🚨 SEVERE HARM TO OTHERS CRISIS DETECTED: '{keyword}'")
                    detected_crisis_type = "severe_harm_others"
                    break
        
        # Check for severe emotional crisis
        if not detected_crisis_type:
            for keyword in self.crisis_keywords.get("severe_crisis", []):
                if keyword in text_lower:
                    logger.critical(f"⚠️ SEVERE EMOTIONAL CRISIS DETECTED: '{keyword}'")
                    detected_crisis_type = "severe_crisis"
                    break
        
        # If crisis detected, trigger callbacks
        if detected_crisis_type:
            for callback in self.crisis_detected_callbacks:
                try:
                    callback(detected_crisis_type, text)
                except Exception as e:
                    logger.error(f"Error in crisis callback: {str(e)}")
        
        return bool(detected_crisis_type), detected_crisis_type or ""
    


    def check_content_safety(self, text: str) -> str:
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
        try:
            # Check input validation
            is_valid, error_msg = self.validate_input(text)
            
            # Check crisis status
            is_crisis, crisis_type = self.check_crisis(text)
            
            result = {
                "is_safe": is_valid and not is_crisis,
                "is_valid": is_valid,
                "validation_errors": [error_msg] if not is_valid and error_msg else [],
                "crisis_detected": is_crisis,
                "crisis_type": crisis_type if is_crisis else None,
                "crisis_message": self.get_crisis_response(crisis_type) if is_crisis else None,
            }
            
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "is_safe": False
            })
