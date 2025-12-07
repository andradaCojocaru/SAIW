"""
Guardrails module for Stress Journal Agent
Implements safety measures: input validation, crisis detection, and output filtering
"""

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
    
    def filter_output(self, response: str) -> str:
        """
        Filter response for sensitive information and inappropriate content.
        
        Removes/masks:
        - Email addresses
        - Phone numbers
        - URLs (except safe documentation links)
        - PII patterns
        
        Args:
            response: Raw agent response
            
        Returns:
            str: Filtered response
        """
        # Remove email addresses
        response = re.sub(r'\S+@\S+\.\S+', '[email address]', response)
        
        # Remove phone numbers (various formats)
        response = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[phone number]', response)
        response = re.sub(r'\+\d{1,3}\s?\d{1,14}', '[phone number]', response)
        
        # Remove most URLs (keep safe resource links if needed)
        response = re.sub(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            '[link]',
            response
        )
        
        # Mask SSN-like patterns
        response = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', response)
        
        # Check for medical diagnosis claims (non-compliant with agent rules)
        medical_diagnosis_patterns = [
            r'you have\s+\w+\s+disorder',
            r'diagnosed with',
            r'the\s+diagnosis\s+is',
        ]
        for pattern in medical_diagnosis_patterns:
            if re.search(pattern, response.lower()):
                logger.warning("Potential medical diagnosis claim detected in response")
                # Flag but don't remove - let human review
                response = "[⚠️ Medical claim flagged for review] " + response
        
        return response
    
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
        
        # Check for self-harm or suicide (HIGHEST PRIORITY)
        for keyword in self.crisis_keywords.get("severe_self_harm", []):
            if keyword in text_lower:
                logger.critical(f"🚨 SEVERE SELF-HARM/SUICIDE CRISIS DETECTED: '{keyword}'")
                return True, "severe_self_harm"
        
        # Check for harm to others (CRITICAL)
        for keyword in self.crisis_keywords.get("severe_harm_others", []):
            if keyword in text_lower:
                logger.critical(f"🚨 SEVERE HARM TO OTHERS CRISIS DETECTED: '{keyword}'")
                return True, "severe_harm_others"
        
        # Check for severe emotional crisis
        for keyword in self.crisis_keywords.get("severe_crisis", []):
            if keyword in text_lower:
                logger.critical(f"⚠️ SEVERE EMOTIONAL CRISIS DETECTED: '{keyword}'")
                return True, "severe_crisis"
        
        return False, ""
    

def create_safe_process_entry(memory, agent, guardrails: Guardrails):
    """
    Factory function to create a safe process_entry function with guardrails.
    
    Usage:
        guardrails = Guardrails()
        safe_process = create_safe_process_entry(memory, agent, guardrails)
        response = safe_process("user message")
    """
    def safe_process_entry(user_text: str) -> str:
        """
        Process user entry with guardrails protection.
        
        Pipeline:
        1. Input validation
        2. Crisis detection
        3. Memory save
        4. Agent processing
        5. Output filtering
        """
        
        try:
            # Step 1: Input validation
            is_valid, error_msg = guardrails.validate_input(user_text)
            if not is_valid:
                logger.warning(f"Input validation failed: {error_msg}")
                return f"❌ {error_msg}"
            
            # Step 2: Crisis detection
            is_crisis, crisis_type = guardrails.check_crisis(user_text)
            if is_crisis:
                logger.critical(f"CRISIS DETECTED - Type: {crisis_type}")
                # Return None to signal crisis - caller can handle with appropriate resources
                return None
            
            # Step 3: Save to memory
            memory.save(f"User entry: {user_text}")
            
            # Step 4: Process with agent
            response = agent.run(user_text)
            
            # Extract message content
            if hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, dict) and 'content' in response:
                response_text = response['content']
            else:
                response_text = str(response)
            
            # Step 5: Filter output
            filtered_response = guardrails.filter_output(response_text)
            
            return filtered_response
            
        except Exception as e:
            logger.error(f"Error in safe_process_entry: {str(e)}", exc_info=True)
            return "⚠️ An error occurred while processing your request. Please try again or contact support."
    
    return safe_process_entry
