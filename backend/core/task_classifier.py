"""
Task Classifier - Layer 3 of the Processing Pipeline
======================================================
Per README (line 171-174):
  ┌─────────────────────────────────────┐
  │ 3. TASK CLASSIFIER                  │ ← Categorize: shopping, meeting,
  │    Type, complexity, risk level     │   email, search, booking, etc.
  └──────────────┬──────────────────────┘

This module:
1. Classifies tasks into categories
2. Determines complexity (simple/medium/complex)
3. Assigns risk level (none/low/medium/high/critical)
4. Routes to appropriate execution path

Author: Super Manager AI
"""

import re
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TaskCategory(Enum):
    """Task categories for routing"""
    # Core categories per README
    SHOPPING = "shopping"
    MEETING = "meeting"
    EMAIL = "email"
    SEARCH = "search"
    BOOKING = "booking"
    PAYMENT = "payment"
    
    # Extended categories
    REMINDER = "reminder"
    CALENDAR = "calendar"
    CREATIVE = "creative"       # Logo, image, design
    DOCUMENT = "document"       # Docs, PDFs, spreadsheets
    AUTOMATION = "automation"   # Workflows, bots
    VERIFICATION = "verification"  # OTP, identity
    TRAVEL = "travel"
    FOOD = "food"               # Restaurant, delivery
    COMMUNICATION = "communication"  # Messages, notifications
    INFORMATION = "information"  # Queries, lookups
    UNKNOWN = "unknown"


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"      # Single step, auto-execute
    MEDIUM = "medium"      # 2-5 steps, may need confirmation
    COMPLEX = "complex"    # Multi-step, needs planning and confirmation


class TaskRiskLevel(Enum):
    """Risk levels for task execution"""
    NONE = 0        # Info queries, safe reads
    LOW = 1         # Creating content, reminders
    MEDIUM = 2      # Sending messages, creating meetings
    HIGH = 3        # Payments < 5000, bookings
    CRITICAL = 4    # Large payments, identity verification


@dataclass
class TaskClassification:
    """Result of task classification"""
    category: TaskCategory
    complexity: TaskComplexity
    risk_level: TaskRiskLevel
    confidence: float  # 0.0 to 1.0
    sub_category: Optional[str] = None
    requires_confirmation: bool = False
    requires_verification: bool = False
    estimated_steps: int = 1
    required_integrations: List[str] = None
    routing_hint: Optional[str] = None  # Hint for capability router
    
    def __post_init__(self):
        if self.required_integrations is None:
            self.required_integrations = []
        
        # Auto-set confirmation based on risk
        if self.risk_level.value >= TaskRiskLevel.MEDIUM.value:
            self.requires_confirmation = True
        
        # Auto-set verification for high/critical
        if self.risk_level.value >= TaskRiskLevel.HIGH.value:
            self.requires_verification = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "complexity": self.complexity.value,
            "risk_level": self.risk_level.name,
            "risk_level_value": self.risk_level.value,
            "confidence": self.confidence,
            "sub_category": self.sub_category,
            "requires_confirmation": self.requires_confirmation,
            "requires_verification": self.requires_verification,
            "estimated_steps": self.estimated_steps,
            "required_integrations": self.required_integrations,
            "routing_hint": self.routing_hint,
        }


class TaskClassifier:
    """
    Classifies tasks by category, complexity, and risk level.
    
    Usage:
        classifier = TaskClassifier()
        result = classifier.classify("Book a flight to Mumbai tomorrow")
        print(result.category)  # TaskCategory.TRAVEL
        print(result.risk_level)  # TaskRiskLevel.CRITICAL
    """
    
    def __init__(self):
        self._init_patterns()
        self._init_risk_mappings()
    
    def _init_patterns(self):
        """Initialize category detection patterns"""
        self.category_patterns: Dict[TaskCategory, List[str]] = {
            TaskCategory.SHOPPING: [
                r"\b(buy|purchase|order|shop|get me|want to buy)\b",
                r"\b(shirt|shoes|phone|laptop|clothes|product)\b.*\b(buy|order)\b",
                r"\badd to cart\b",
                r"\bcheckout\b",
            ],
            
            TaskCategory.MEETING: [
                r"\b(schedule|create|book|set up|arrange)\b.*\b(meeting|call|zoom|video call|google meet)\b",
                r"\bzoom\b.*\b(meeting|call)\b",
                r"\bmeet(ing)?\b.*\b(tomorrow|today|now|at \d)\b",
                r"\b(instant|quick|start)\b.*\bmeeting\b",
            ],
            
            TaskCategory.EMAIL: [
                r"\b(send|compose|write|draft)\b.*\b(email|mail|message to)\b",
                r"\bemail\b.*\bto\b",
                r"\bmail\b.*\bto\b",
                r"\breply\b.*\b(email|mail)\b",
            ],
            
            TaskCategory.SEARCH: [
                r"\b(search|find|look up|google|look for|what is|who is)\b",
                r"\b(information about|tell me about|details of)\b",
                r"\bwhat('s| is)\b",
            ],
            
            TaskCategory.BOOKING: [
                r"\b(book|reserve|reservation)\b.*\b(ticket|seat|table|room)\b",
                r"\b(hotel|restaurant|flight|train|bus|movie)\b.*\b(book|reserve)\b",
                r"\bbook\b.*\b(at|for|on)\b",
            ],
            
            TaskCategory.PAYMENT: [
                r"\b(pay|payment|transfer|send money|upi)\b",
                r"\b(razorpay|gpay|phonepe|paytm)\b",
                r"\bcreate\b.*\bpayment link\b",
                r"\b₹?\d+\b.*\b(pay|send|transfer)\b",
            ],
            
            TaskCategory.REMINDER: [
                r"\bremind(er)?\b",
                r"\bset\b.*\b(reminder|alarm|alert)\b",
                r"\bdon't forget\b",
                r"\bnotify me\b",
            ],
            
            TaskCategory.CALENDAR: [
                r"\b(calendar|event|appointment)\b",
                r"\bschedule\b(?!.*meeting)",  # Schedule without meeting
                r"\badd\b.*\b(event|appointment)\b",
            ],
            
            TaskCategory.CREATIVE: [
                r"\b(create|make|design|generate)\b.*\b(logo|image|poster|banner|graphic)\b",
                r"\b(logo|image|design)\b.*\bfor\b",
                r"\bdall-?e\b",
                r"\b(ai|generate)\b.*\b(image|art|picture)\b",
            ],
            
            TaskCategory.DOCUMENT: [
                r"\b(create|make|generate|draft)\b.*\b(document|pdf|doc|spreadsheet|report)\b",
                r"\bwrite\b.*\b(letter|proposal|resume)\b",
            ],
            
            TaskCategory.TRAVEL: [
                r"\b(flight|train|bus|cab|taxi|uber|ola)\b",
                r"\btravel\b.*\bto\b",
                r"\b(trip|vacation|holiday)\b.*\b(plan|book)\b",
                r"\bbook\b.*\b(flight|train|bus)\b",
            ],
            
            TaskCategory.FOOD: [
                r"\b(order|get)\b.*\b(food|pizza|burger|dinner|lunch|breakfast)\b",
                r"\b(restaurant|cafe|dine|eat)\b",
                r"\b(swiggy|zomato|uber eats)\b",
                r"\b(book|reserve)\b.*\b(table|restaurant)\b",
            ],
            
            TaskCategory.COMMUNICATION: [
                r"\b(send|message|text|whatsapp|telegram|slack)\b",
                r"\bnotify\b.*\b(team|people|everyone)\b",
                r"\b(call|phone)\b.*\b(them|him|her|the)\b",
            ],
            
            TaskCategory.VERIFICATION: [
                r"\b(verify|verification|otp|authenticate)\b",
                r"\b(aadhaar|pan|kyc)\b",
            ],
            
            TaskCategory.INFORMATION: [
                r"\b(tell|explain|describe|summarize)\b",
                r"\bhow (do|to|can)\b",
                r"\bwhat('s| is|'re| are)\b",
            ],
        }
    
    def _init_risk_mappings(self):
        """Initialize category to risk level mappings"""
        self.category_risk: Dict[TaskCategory, TaskRiskLevel] = {
            TaskCategory.SEARCH: TaskRiskLevel.NONE,
            TaskCategory.INFORMATION: TaskRiskLevel.NONE,
            TaskCategory.REMINDER: TaskRiskLevel.LOW,
            TaskCategory.CREATIVE: TaskRiskLevel.LOW,
            TaskCategory.DOCUMENT: TaskRiskLevel.LOW,
            TaskCategory.CALENDAR: TaskRiskLevel.LOW,
            TaskCategory.EMAIL: TaskRiskLevel.MEDIUM,
            TaskCategory.MEETING: TaskRiskLevel.MEDIUM,
            TaskCategory.COMMUNICATION: TaskRiskLevel.MEDIUM,
            TaskCategory.FOOD: TaskRiskLevel.MEDIUM,
            TaskCategory.SHOPPING: TaskRiskLevel.HIGH,
            TaskCategory.BOOKING: TaskRiskLevel.HIGH,
            TaskCategory.TRAVEL: TaskRiskLevel.HIGH,
            TaskCategory.PAYMENT: TaskRiskLevel.HIGH,
            TaskCategory.VERIFICATION: TaskRiskLevel.CRITICAL,
            TaskCategory.UNKNOWN: TaskRiskLevel.MEDIUM,
        }
        
        self.category_complexity: Dict[TaskCategory, TaskComplexity] = {
            TaskCategory.SEARCH: TaskComplexity.SIMPLE,
            TaskCategory.INFORMATION: TaskComplexity.SIMPLE,
            TaskCategory.REMINDER: TaskComplexity.SIMPLE,
            TaskCategory.CREATIVE: TaskComplexity.SIMPLE,
            TaskCategory.DOCUMENT: TaskComplexity.MEDIUM,
            TaskCategory.CALENDAR: TaskComplexity.SIMPLE,
            TaskCategory.EMAIL: TaskComplexity.SIMPLE,
            TaskCategory.MEETING: TaskComplexity.MEDIUM,
            TaskCategory.COMMUNICATION: TaskComplexity.SIMPLE,
            TaskCategory.FOOD: TaskComplexity.MEDIUM,
            TaskCategory.SHOPPING: TaskComplexity.COMPLEX,
            TaskCategory.BOOKING: TaskComplexity.COMPLEX,
            TaskCategory.TRAVEL: TaskComplexity.COMPLEX,
            TaskCategory.PAYMENT: TaskComplexity.MEDIUM,
            TaskCategory.VERIFICATION: TaskComplexity.COMPLEX,
            TaskCategory.UNKNOWN: TaskComplexity.MEDIUM,
        }
        
        self.category_integrations: Dict[TaskCategory, List[str]] = {
            TaskCategory.MEETING: ["zoom", "google_calendar"],
            TaskCategory.EMAIL: ["gmail"],
            TaskCategory.CALENDAR: ["google_calendar"],
            TaskCategory.PAYMENT: ["razorpay", "stripe"],
            TaskCategory.SHOPPING: [],  # Web automation
            TaskCategory.BOOKING: [],   # Web automation
            TaskCategory.TRAVEL: [],    # Web automation
            TaskCategory.FOOD: [],      # Web automation
            TaskCategory.CREATIVE: [],  # Built-in (Pollinations)
            TaskCategory.SEARCH: [],    # Built-in (DuckDuckGo)
        }
    
    def classify(self, text: str) -> TaskClassification:
        """
        Classify a task from natural language text.
        
        Args:
            text: User's natural language input
            
        Returns:
            TaskClassification with category, complexity, risk, etc.
        """
        text_lower = text.lower().strip()
        
        # Match against patterns
        matched_category = TaskCategory.UNKNOWN
        best_confidence = 0.0
        sub_category = None
        
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    # Higher confidence for more specific patterns
                    confidence = 0.8 + (len(pattern) / 100)  # Longer = more specific
                    if confidence > best_confidence:
                        best_confidence = min(confidence, 1.0)
                        matched_category = category
        
        # If no match, use heuristics
        if matched_category == TaskCategory.UNKNOWN:
            matched_category = self._heuristic_classify(text_lower)
            best_confidence = 0.5
        
        # Get risk and complexity
        risk_level = self.category_risk.get(matched_category, TaskRiskLevel.MEDIUM)
        complexity = self.category_complexity.get(matched_category, TaskComplexity.MEDIUM)
        integrations = self.category_integrations.get(matched_category, [])
        
        # Adjust risk based on keywords
        risk_level = self._adjust_risk(text_lower, risk_level)
        
        # Estimate steps
        estimated_steps = self._estimate_steps(matched_category, complexity)
        
        # Generate routing hint
        routing_hint = self._get_routing_hint(matched_category, text_lower)
        
        classification = TaskClassification(
            category=matched_category,
            complexity=complexity,
            risk_level=risk_level,
            confidence=best_confidence,
            sub_category=sub_category,
            estimated_steps=estimated_steps,
            required_integrations=integrations,
            routing_hint=routing_hint,
        )
        
        logger.info(f"[TASK_CLASSIFIER] '{text[:50]}...' → {matched_category.value} "
                   f"(risk={risk_level.name}, complexity={complexity.value}, conf={best_confidence:.2f})")
        
        return classification
    
    def _heuristic_classify(self, text: str) -> TaskCategory:
        """Fallback heuristic classification"""
        # Check for action verbs
        if any(verb in text for verb in ["send", "email", "mail"]):
            return TaskCategory.EMAIL
        if any(verb in text for verb in ["search", "find", "look"]):
            return TaskCategory.SEARCH
        if any(verb in text for verb in ["buy", "order", "purchase"]):
            return TaskCategory.SHOPPING
        if any(verb in text for verb in ["book", "reserve"]):
            return TaskCategory.BOOKING
        if any(verb in text for verb in ["meet", "call", "zoom"]):
            return TaskCategory.MEETING
        if any(verb in text for verb in ["pay", "transfer", "send money"]):
            return TaskCategory.PAYMENT
        if any(verb in text for verb in ["remind", "reminder", "alert"]):
            return TaskCategory.REMINDER
        if any(verb in text for verb in ["create", "make", "generate"]):
            return TaskCategory.CREATIVE
        
        return TaskCategory.INFORMATION
    
    def _adjust_risk(self, text: str, base_risk: TaskRiskLevel) -> TaskRiskLevel:
        """Adjust risk based on specific keywords"""
        # Check for high-value amounts
        amount_match = re.search(r'₹?\s*(\d[\d,]*)', text)
        if amount_match:
            amount = int(amount_match.group(1).replace(',', ''))
            if amount >= 5000:
                return TaskRiskLevel.CRITICAL
            elif amount >= 1000:
                return max(base_risk, TaskRiskLevel.HIGH)
        
        # Check for sensitive keywords
        if any(word in text for word in ["aadhaar", "pan", "passport", "password"]):
            return TaskRiskLevel.CRITICAL
        
        return base_risk
    
    def _estimate_steps(self, category: TaskCategory, complexity: TaskComplexity) -> int:
        """Estimate number of execution steps"""
        base_steps = {
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MEDIUM: 3,
            TaskComplexity.COMPLEX: 5,
        }
        
        # Category adjustments
        category_steps = {
            TaskCategory.SHOPPING: 5,  # Search + Compare + Select + Cart + Checkout
            TaskCategory.BOOKING: 4,   # Search + Select + Fill + Confirm
            TaskCategory.TRAVEL: 6,    # Multiple bookings possible
            TaskCategory.SEARCH: 1,
            TaskCategory.EMAIL: 1,
            TaskCategory.MEETING: 2,   # Create + Send invites
        }
        
        return category_steps.get(category, base_steps[complexity])
    
    def _get_routing_hint(self, category: TaskCategory, text: str) -> str:
        """Get hint for capability router"""
        hints = {
            TaskCategory.SHOPPING: "browser_automation",
            TaskCategory.BOOKING: "browser_automation",
            TaskCategory.TRAVEL: "browser_automation",
            TaskCategory.MEETING: "api:zoom,jitsi",
            TaskCategory.EMAIL: "api:gmail,smtp",
            TaskCategory.SEARCH: "api:duckduckgo",
            TaskCategory.CREATIVE: "api:pollinations",
            TaskCategory.PAYMENT: "api:razorpay,stripe",
            TaskCategory.CALENDAR: "api:google_calendar",
            TaskCategory.FOOD: "browser_automation",
        }
        return hints.get(category, "adaptive")
    
    def get_confirmation_message(self, classification: TaskClassification, details: Dict[str, Any]) -> str:
        """Generate confirmation message based on classification"""
        category = classification.category
        risk = classification.risk_level
        
        if risk == TaskRiskLevel.CRITICAL:
            return (f"⚠️ **CRITICAL ACTION** - {category.value.upper()}\n\n"
                   f"This requires additional verification.\n"
                   f"Details: {details}\n\n"
                   f"Please confirm with verification code.")
        
        elif risk == TaskRiskLevel.HIGH:
            return (f"⚡ **High-Risk Action** - {category.value}\n\n"
                   f"Details: {details}\n\n"
                   f"Do you want to proceed?")
        
        elif risk == TaskRiskLevel.MEDIUM:
            return (f"📋 **Confirmation Required** - {category.value}\n\n"
                   f"Details: {details}\n\n"
                   f"Proceed?")
        
        else:
            return f"Ready to execute: {category.value}\nDetails: {details}"


# Global instance
_task_classifier: Optional[TaskClassifier] = None


def get_task_classifier() -> TaskClassifier:
    """Get global TaskClassifier instance"""
    global _task_classifier
    if _task_classifier is None:
        _task_classifier = TaskClassifier()
    return _task_classifier


# Convenience function
def classify_task(text: str) -> TaskClassification:
    """Convenience function to classify a task"""
    return get_task_classifier().classify(text)
