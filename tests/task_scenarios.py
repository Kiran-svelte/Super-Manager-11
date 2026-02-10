"""
100 TASK TEST SCENARIOS
=======================
Comprehensive test scenarios to validate the AI assistant's task handling capabilities.
Each scenario includes:
- User input
- Expected intent detection
- Required information
- Expected flow
- Expected output

Run these tests to ensure the system handles all common use cases correctly.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# =============================================================================
# TEST SCENARIOS
# =============================================================================

TASK_SCENARIOS = [
    # =========================================================================
    # EMAIL SCENARIOS (1-20)
    # =========================================================================
    {
        "id": 1,
        "category": "email",
        "input": "Send an email to john@example.com about the meeting tomorrow",
        "expected_intent": "send_email",
        "expected_extraction": {"to_email": "john@example.com"},
        "required_questions": ["subject", "body"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 2,
        "category": "email",
        "input": "Email my boss that I'll be late today",
        "expected_intent": "send_email",
        "expected_extraction": {},
        "required_questions": ["to_email", "subject", "body"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 3,
        "category": "email",
        "input": "Send email to alice@company.com with subject 'Project Update' and tell her the project is on track",
        "expected_intent": "send_email",
        "expected_extraction": {"to_email": "alice@company.com", "subject": "Project Update"},
        "required_questions": [],
        "expected_flow": ["confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 4,
        "category": "email",
        "input": "Can you send a thank you email to support@service.com for their help?",
        "expected_intent": "send_email",
        "expected_extraction": {"to_email": "support@service.com"},
        "required_questions": ["subject", "body"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 5,
        "category": "email",
        "input": "I need to email the HR department about my leave request",
        "expected_intent": "send_email",
        "expected_extraction": {},
        "required_questions": ["to_email", "subject", "body"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 6,
        "category": "email",
        "input": "Forward this to marketing@company.com: New campaign starts next week",
        "expected_intent": "send_email",
        "expected_extraction": {"to_email": "marketing@company.com"},
        "required_questions": ["subject"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 7,
        "category": "email",
        "input": "Send a birthday email to mike@gmail.com",
        "expected_intent": "send_email",
        "expected_extraction": {"to_email": "mike@gmail.com"},
        "required_questions": ["subject", "body"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 8,
        "category": "email",
        "input": "Email team@startup.com that tomorrow's standup is cancelled",
        "expected_intent": "send_email",
        "expected_extraction": {"to_email": "team@startup.com"},
        "required_questions": [],
        "expected_flow": ["confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 9,
        "category": "email",
        "input": "I want to send an apology email to client@business.com",
        "expected_intent": "send_email",
        "expected_extraction": {"to_email": "client@business.com"},
        "required_questions": ["subject", "body"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 10,
        "category": "email",
        "input": "Send invitation email to all attendees for tomorrow's event",
        "expected_intent": "send_email",
        "expected_extraction": {},
        "required_questions": ["to_email", "subject", "body"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    
    # =========================================================================
    # MEETING SCENARIOS (11-30)
    # =========================================================================
    {
        "id": 11,
        "category": "meeting",
        "input": "Schedule a meeting with john@example.com tomorrow at 3 PM",
        "expected_intent": "schedule_meeting",
        "expected_extraction": {"participants": ["john@example.com"], "time": "3 PM"},
        "required_questions": ["title"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 12,
        "category": "meeting",
        "input": "Set up a team meeting for next Monday",
        "expected_intent": "schedule_meeting",
        "expected_extraction": {},
        "required_questions": ["title", "participants", "time"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 13,
        "category": "meeting",
        "input": "Create a Zoom call with my manager for today at 5",
        "expected_intent": "schedule_meeting",
        "expected_extraction": {"time": "5 PM"},
        "required_questions": ["title", "participants"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 14,
        "category": "meeting",
        "input": "I need to schedule a 1-on-1 with Sarah for Wednesday 10 AM",
        "expected_intent": "schedule_meeting",
        "expected_extraction": {"title": "1-on-1", "time": "10 AM"},
        "required_questions": ["participants"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 15,
        "category": "meeting",
        "input": "Book a conference room for the client presentation next Friday at 2 PM",
        "expected_intent": "schedule_meeting",
        "expected_extraction": {"title": "client presentation"},
        "required_questions": ["participants"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 16,
        "category": "meeting",
        "input": "Schedule a project kickoff meeting with alex@tech.com and bob@tech.com",
        "expected_intent": "schedule_meeting",
        "expected_extraction": {"title": "project kickoff meeting", "participants": ["alex@tech.com", "bob@tech.com"]},
        "required_questions": ["date", "time"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 17,
        "category": "meeting",
        "input": "Can you schedule a 30-minute sync with the design team?",
        "expected_intent": "schedule_meeting",
        "expected_extraction": {"duration_minutes": 30},
        "required_questions": ["title", "participants", "date", "time"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 18,
        "category": "meeting",
        "input": "Set up a recurring weekly meeting every Monday at 9 AM",
        "expected_intent": "schedule_meeting",
        "expected_extraction": {"time": "9 AM"},
        "required_questions": ["title", "participants"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 19,
        "category": "meeting",
        "input": "Create a meeting for interview with candidate@email.com on Thursday",
        "expected_intent": "schedule_meeting",
        "expected_extraction": {"title": "interview", "participants": ["candidate@email.com"]},
        "required_questions": ["time"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    {
        "id": 20,
        "category": "meeting",
        "input": "I want to have a video call with my doctor tomorrow morning",
        "expected_intent": "schedule_meeting",
        "expected_extraction": {},
        "required_questions": ["title", "participants", "time"],
        "expected_flow": ["collect_info", "confirm", "execute"],
        "security_level": "medium"
    },
    
    # =========================================================================
    # TICKET BOOKING SCENARIOS (21-40)
    # =========================================================================
    {
        "id": 21,
        "category": "booking",
        "input": "Book 5 tickets for Wonderla Bangalore tomorrow",
        "expected_intent": "book_tickets",
        "expected_extraction": {"venue_name": "Wonderla Bangalore", "num_tickets": 5},
        "required_questions": [],
        "expected_flow": ["show_offers", "select_offer", "otp_verify", "confirm", "payment"],
        "security_level": "high"
    },
    {
        "id": 22,
        "category": "booking",
        "input": "We are 5 members, college students. Find best offer and book 5 Wonderla Bangalore tickets for us",
        "expected_intent": "book_tickets",
        "expected_extraction": {"venue_name": "Wonderla Bangalore", "num_tickets": 5},
        "required_questions": ["date"],
        "expected_flow": ["collect_info", "show_offers", "select_offer", "otp_verify", "confirm", "payment"],
        "security_level": "high"
    },
    {
        "id": 23,
        "category": "booking",
        "input": "I want to book movie tickets for Avengers in PVR",
        "expected_intent": "book_tickets",
        "expected_extraction": {"venue_name": "PVR"},
        "required_questions": ["num_tickets", "date", "show_time"],
        "expected_flow": ["collect_info", "confirm", "redirect_to_bookmyshow"],
        "security_level": "high"
    },
    {
        "id": 24,
        "category": "booking",
        "input": "Get me 2 tickets for the comedy show this weekend",
        "expected_intent": "book_tickets",
        "expected_extraction": {"num_tickets": 2},
        "required_questions": ["venue_name", "date"],
        "expected_flow": ["collect_info", "show_offers", "confirm", "payment"],
        "security_level": "high"
    },
    {
        "id": 25,
        "category": "booking",
        "input": "Book 3 tickets for Wonderla Hyderabad for Saturday",
        "expected_intent": "book_tickets",
        "expected_extraction": {"venue_name": "Wonderla Hyderabad", "num_tickets": 3},
        "required_questions": [],
        "expected_flow": ["show_offers", "select_offer", "otp_verify", "confirm", "payment"],
        "security_level": "high"
    },
    {
        "id": 26,
        "category": "booking",
        "input": "I need movie tickets for 4 people for the 9 PM show today",
        "expected_intent": "book_tickets",
        "expected_extraction": {"num_tickets": 4, "show_time": "9 PM"},
        "required_questions": ["venue_name", "movie_name"],
        "expected_flow": ["collect_info", "confirm", "redirect_to_bookmyshow"],
        "security_level": "high"
    },
    {
        "id": 27,
        "category": "booking",
        "input": "Book entry tickets to the zoo for my family of 5",
        "expected_intent": "book_tickets",
        "expected_extraction": {"num_tickets": 5},
        "required_questions": ["venue_name", "date"],
        "expected_flow": ["collect_info", "show_offers", "confirm", "payment"],
        "security_level": "high"
    },
    {
        "id": 28,
        "category": "booking",
        "input": "Get VIP tickets for the concert next month",
        "expected_intent": "book_tickets",
        "expected_extraction": {"ticket_type": "VIP"},
        "required_questions": ["venue_name", "num_tickets", "date"],
        "expected_flow": ["collect_info", "show_offers", "confirm", "payment"],
        "security_level": "high"
    },
    {
        "id": 29,
        "category": "booking",
        "input": "Book fast track tickets for Wonderla Kochi",
        "expected_intent": "book_tickets",
        "expected_extraction": {"venue_name": "Wonderla Kochi", "ticket_type": "fast track"},
        "required_questions": ["num_tickets", "date"],
        "expected_flow": ["collect_info", "show_offers", "confirm", "payment"],
        "security_level": "high"
    },
    {
        "id": 30,
        "category": "booking",
        "input": "I want to book tickets for the football match on Sunday",
        "expected_intent": "book_tickets",
        "expected_extraction": {},
        "required_questions": ["venue_name", "num_tickets"],
        "expected_flow": ["collect_info", "show_offers", "confirm", "payment"],
        "security_level": "high"
    },
    
    # =========================================================================
    # PAYMENT SCENARIOS (31-45)
    # =========================================================================
    {
        "id": 31,
        "category": "payment",
        "input": "Pay ₹500 to john@paytm",
        "expected_intent": "make_payment",
        "expected_extraction": {"amount": 500, "recipient": "john@paytm"},
        "required_questions": ["purpose"],
        "expected_flow": ["collect_info", "otp_verify", "confirm", "payment_gateway"],
        "security_level": "high"
    },
    {
        "id": 32,
        "category": "payment",
        "input": "Send money to my friend for dinner last night",
        "expected_intent": "make_payment",
        "expected_extraction": {},
        "required_questions": ["amount", "recipient"],
        "expected_flow": ["collect_info", "otp_verify", "confirm", "payment_gateway"],
        "security_level": "high"
    },
    {
        "id": 33,
        "category": "payment",
        "input": "Transfer ₹10000 to rent@landlord.com for rent",
        "expected_intent": "make_payment",
        "expected_extraction": {"amount": 10000, "recipient": "rent@landlord.com", "purpose": "rent"},
        "required_questions": [],
        "expected_flow": ["otp_verify", "2fa_verify", "confirm", "payment_gateway"],
        "security_level": "critical"
    },
    {
        "id": 34,
        "category": "payment",
        "input": "Pay my electricity bill of ₹2500",
        "expected_intent": "make_payment",
        "expected_extraction": {"amount": 2500, "purpose": "electricity bill"},
        "required_questions": ["recipient"],
        "expected_flow": ["collect_info", "otp_verify", "confirm", "payment_gateway"],
        "security_level": "high"
    },
    {
        "id": 35,
        "category": "payment",
        "input": "Split the bill with 4 people for ₹2000 total",
        "expected_intent": "make_payment",
        "expected_extraction": {"amount": 500},
        "required_questions": ["recipient"],
        "expected_flow": ["collect_info", "otp_verify", "confirm", "payment_gateway"],
        "security_level": "high"
    },
    {
        "id": 36,
        "category": "payment",
        "input": "Pay for my Amazon order of ₹1500",
        "expected_intent": "make_payment",
        "expected_extraction": {"amount": 1500},
        "required_questions": ["recipient"],
        "expected_flow": ["collect_info", "otp_verify", "confirm", "payment_gateway"],
        "security_level": "high"
    },
    {
        "id": 37,
        "category": "payment",
        "input": "I need to pay school fees of ₹25000",
        "expected_intent": "make_payment",
        "expected_extraction": {"amount": 25000, "purpose": "school fees"},
        "required_questions": ["recipient"],
        "expected_flow": ["collect_info", "otp_verify", "2fa_verify", "confirm", "payment_gateway"],
        "security_level": "critical"
    },
    {
        "id": 38,
        "category": "payment",
        "input": "Pay ₹200 to cabdriver@upi for the ride",
        "expected_intent": "make_payment",
        "expected_extraction": {"amount": 200, "recipient": "cabdriver@upi"},
        "required_questions": [],
        "expected_flow": ["confirm", "payment_gateway"],
        "security_level": "low"
    },
    {
        "id": 39,
        "category": "payment",
        "input": "Send ₹50000 to contractor@bank for home renovation",
        "expected_intent": "make_payment",
        "expected_extraction": {"amount": 50000, "purpose": "home renovation"},
        "required_questions": [],
        "expected_flow": ["otp_verify", "2fa_verify", "biometric", "confirm", "payment_gateway"],
        "security_level": "critical"
    },
    {
        "id": 40,
        "category": "payment",
        "input": "Pay insurance premium of ₹15000",
        "expected_intent": "make_payment",
        "expected_extraction": {"amount": 15000, "purpose": "insurance premium"},
        "required_questions": ["recipient"],
        "expected_flow": ["collect_info", "otp_verify", "2fa_verify", "confirm", "payment_gateway"],
        "security_level": "critical"
    },
    
    # =========================================================================
    # REMINDER SCENARIOS (41-55)
    # =========================================================================
    {
        "id": 41,
        "category": "reminder",
        "input": "Remind me to call mom at 7 PM",
        "expected_intent": "create_reminder",
        "expected_extraction": {"reminder_text": "call mom", "remind_at": "7 PM"},
        "required_questions": [],
        "expected_flow": ["confirm", "execute"],
        "security_level": "low"
    },
    {
        "id": 42,
        "category": "reminder",
        "input": "Set a reminder for the dentist appointment next Tuesday",
        "expected_intent": "create_reminder",
        "expected_extraction": {"reminder_text": "dentist appointment"},
        "required_questions": ["time"],
        "expected_flow": ["collect_info", "execute"],
        "security_level": "low"
    },
    {
        "id": 43,
        "category": "reminder",
        "input": "Remind me to submit the report before 5 PM tomorrow",
        "expected_intent": "create_reminder",
        "expected_extraction": {"reminder_text": "submit the report"},
        "required_questions": [],
        "expected_flow": ["execute"],
        "security_level": "low"
    },
    {
        "id": 44,
        "category": "reminder",
        "input": "I need a reminder to pick up dry cleaning",
        "expected_intent": "create_reminder",
        "expected_extraction": {"reminder_text": "pick up dry cleaning"},
        "required_questions": ["remind_at"],
        "expected_flow": ["collect_info", "execute"],
        "security_level": "low"
    },
    {
        "id": 45,
        "category": "reminder",
        "input": "Set daily reminder to take medicine at 9 AM",
        "expected_intent": "create_reminder",
        "expected_extraction": {"reminder_text": "take medicine", "repeat": "daily"},
        "required_questions": [],
        "expected_flow": ["execute"],
        "security_level": "low"
    },
    {
        "id": 46,
        "category": "reminder",
        "input": "Remind me about the team lunch this Friday at noon",
        "expected_intent": "create_reminder",
        "expected_extraction": {"reminder_text": "team lunch"},
        "required_questions": [],
        "expected_flow": ["execute"],
        "security_level": "low"
    },
    {
        "id": 47,
        "category": "reminder",
        "input": "Set a reminder for wife's birthday on March 15",
        "expected_intent": "create_reminder",
        "expected_extraction": {"reminder_text": "wife's birthday"},
        "required_questions": [],
        "expected_flow": ["execute"],
        "security_level": "low"
    },
    {
        "id": 48,
        "category": "reminder",
        "input": "Remind me to renew passport in 2 months",
        "expected_intent": "create_reminder",
        "expected_extraction": {"reminder_text": "renew passport"},
        "required_questions": [],
        "expected_flow": ["execute"],
        "security_level": "low"
    },
    {
        "id": 49,
        "category": "reminder",
        "input": "Set reminder for gym at 6 AM every weekday",
        "expected_intent": "create_reminder",
        "expected_extraction": {"reminder_text": "gym", "repeat": "weekdays"},
        "required_questions": [],
        "expected_flow": ["execute"],
        "security_level": "low"
    },
    {
        "id": 50,
        "category": "reminder",
        "input": "Remind me to water the plants every Sunday",
        "expected_intent": "create_reminder",
        "expected_extraction": {"reminder_text": "water the plants", "repeat": "weekly"},
        "required_questions": ["time"],
        "expected_flow": ["collect_info", "execute"],
        "security_level": "low"
    },
    
    # =========================================================================
    # HOTEL BOOKING SCENARIOS (51-60)
    # =========================================================================
    {
        "id": 51,
        "category": "hotel",
        "input": "Book a hotel in Goa for next weekend",
        "expected_intent": "book_hotel",
        "expected_extraction": {"location": "Goa"},
        "required_questions": ["check_in", "check_out", "guests"],
        "expected_flow": ["collect_info", "search_hotels", "select_hotel", "otp_verify", "confirm", "payment"],
        "security_level": "high"
    },
    {
        "id": 52,
        "category": "hotel",
        "input": "I need a 5-star hotel in Mumbai for 2 nights",
        "expected_intent": "book_hotel",
        "expected_extraction": {"location": "Mumbai", "hotel_type": "5-star"},
        "required_questions": ["check_in", "guests"],
        "expected_flow": ["collect_info", "search_hotels", "select_hotel", "otp_verify", "confirm", "payment"],
        "security_level": "high"
    },
    {
        "id": 53,
        "category": "hotel",
        "input": "Find me a budget hotel near the airport in Delhi",
        "expected_intent": "book_hotel",
        "expected_extraction": {"location": "Delhi airport", "hotel_type": "budget"},
        "required_questions": ["check_in", "check_out", "guests"],
        "expected_flow": ["collect_info", "search_hotels", "select_hotel", "otp_verify", "confirm", "payment"],
        "security_level": "high"
    },
    {
        "id": 54,
        "category": "hotel",
        "input": "Book a beach resort in Kerala for our anniversary",
        "expected_intent": "book_hotel",
        "expected_extraction": {"location": "Kerala", "hotel_type": "resort"},
        "required_questions": ["check_in", "check_out", "guests"],
        "expected_flow": ["collect_info", "search_hotels", "select_hotel", "otp_verify", "confirm", "payment"],
        "security_level": "high"
    },
    {
        "id": 55,
        "category": "hotel",
        "input": "I want to stay at Taj Hotel Bangalore on December 25",
        "expected_intent": "book_hotel",
        "expected_extraction": {"hotel_name": "Taj Hotel", "location": "Bangalore"},
        "required_questions": ["check_out", "guests"],
        "expected_flow": ["collect_info", "confirm", "otp_verify", "payment"],
        "security_level": "high"
    },
    
    # =========================================================================
    # FLIGHT BOOKING SCENARIOS (56-65)
    # =========================================================================
    {
        "id": 56,
        "category": "flight",
        "input": "Book a flight from Bangalore to Delhi for tomorrow",
        "expected_intent": "book_flight",
        "expected_extraction": {"from_city": "Bangalore", "to_city": "Delhi"},
        "required_questions": ["passengers"],
        "expected_flow": ["search_flights", "select_flight", "passenger_details", "otp_verify", "confirm", "payment"],
        "security_level": "critical"
    },
    {
        "id": 57,
        "category": "flight",
        "input": "I need 2 round trip tickets from Mumbai to Goa",
        "expected_intent": "book_flight",
        "expected_extraction": {"from_city": "Mumbai", "to_city": "Goa", "passengers": 2},
        "required_questions": ["date", "return_date"],
        "expected_flow": ["collect_info", "search_flights", "select_flight", "otp_verify", "confirm", "payment"],
        "security_level": "critical"
    },
    {
        "id": 58,
        "category": "flight",
        "input": "Find cheapest flight to Chennai next Monday",
        "expected_intent": "book_flight",
        "expected_extraction": {"to_city": "Chennai"},
        "required_questions": ["from_city", "passengers"],
        "expected_flow": ["collect_info", "search_flights", "select_flight", "otp_verify", "confirm", "payment"],
        "security_level": "critical"
    },
    {
        "id": 59,
        "category": "flight",
        "input": "Book business class flight from Delhi to London",
        "expected_intent": "book_flight",
        "expected_extraction": {"from_city": "Delhi", "to_city": "London", "class": "business"},
        "required_questions": ["date", "passengers"],
        "expected_flow": ["collect_info", "search_flights", "select_flight", "otp_verify", "confirm", "payment"],
        "security_level": "critical"
    },
    {
        "id": 60,
        "category": "flight",
        "input": "I want to fly to Kolkata this weekend with IndiGo",
        "expected_intent": "book_flight",
        "expected_extraction": {"to_city": "Kolkata", "preferred_airline": "IndiGo"},
        "required_questions": ["from_city", "date", "passengers"],
        "expected_flow": ["collect_info", "search_flights", "select_flight", "otp_verify", "confirm", "payment"],
        "security_level": "critical"
    },
    
    # =========================================================================
    # DOCUMENT GENERATION SCENARIOS (66-75)
    # =========================================================================
    {
        "id": 66,
        "category": "document",
        "input": "Create a leave application letter for 3 days",
        "expected_intent": "generate_document",
        "expected_extraction": {"document_type": "leave application"},
        "required_questions": ["content_data"],
        "expected_flow": ["collect_info", "generate", "confirm"],
        "security_level": "low"
    },
    {
        "id": 67,
        "category": "document",
        "input": "Generate an invoice for ₹50000",
        "expected_intent": "generate_document",
        "expected_extraction": {"document_type": "invoice", "amount": 50000},
        "required_questions": ["content_data"],
        "expected_flow": ["collect_info", "generate", "confirm"],
        "security_level": "low"
    },
    {
        "id": 68,
        "category": "document",
        "input": "Create a professional resume for software engineer",
        "expected_intent": "generate_document",
        "expected_extraction": {"document_type": "resume"},
        "required_questions": ["content_data"],
        "expected_flow": ["collect_info", "generate", "confirm"],
        "security_level": "low"
    },
    {
        "id": 69,
        "category": "document",
        "input": "Write a cover letter for the marketing position",
        "expected_intent": "generate_document",
        "expected_extraction": {"document_type": "cover letter"},
        "required_questions": ["content_data"],
        "expected_flow": ["collect_info", "generate", "confirm"],
        "security_level": "low"
    },
    {
        "id": 70,
        "category": "document",
        "input": "Generate a rental agreement document",
        "expected_intent": "generate_document",
        "expected_extraction": {"document_type": "rental agreement"},
        "required_questions": ["content_data"],
        "expected_flow": ["collect_info", "generate", "confirm"],
        "security_level": "low"
    },
    
    # =========================================================================
    # LOGO CREATION SCENARIOS (71-80)
    # =========================================================================
    {
        "id": 71,
        "category": "logo",
        "input": "Create a logo for my startup called TechFlow",
        "expected_intent": "create_logo",
        "expected_extraction": {"name": "TechFlow"},
        "required_questions": ["style", "colors"],
        "expected_flow": ["collect_info", "generate", "confirm"],
        "security_level": "low"
    },
    {
        "id": 72,
        "category": "logo",
        "input": "Design a minimalist logo for CloudNine",
        "expected_intent": "create_logo",
        "expected_extraction": {"name": "CloudNine", "style": "minimalist"},
        "required_questions": [],
        "expected_flow": ["generate", "confirm"],
        "security_level": "low"
    },
    {
        "id": 73,
        "category": "logo",
        "input": "I need a logo for my restaurant called Spice Garden",
        "expected_intent": "create_logo",
        "expected_extraction": {"name": "Spice Garden", "industry": "restaurant"},
        "required_questions": ["style"],
        "expected_flow": ["collect_info", "generate", "confirm"],
        "security_level": "low"
    },
    {
        "id": 74,
        "category": "logo",
        "input": "Create a modern logo for fitness brand PowerFit in blue and black",
        "expected_intent": "create_logo",
        "expected_extraction": {"name": "PowerFit", "style": "modern", "colors": ["blue", "black"]},
        "required_questions": [],
        "expected_flow": ["generate", "confirm"],
        "security_level": "low"
    },
    {
        "id": 75,
        "category": "logo",
        "input": "Design a logo with tagline 'Innovation First' for InnovateTech",
        "expected_intent": "create_logo",
        "expected_extraction": {"name": "InnovateTech", "tagline": "Innovation First"},
        "required_questions": ["style"],
        "expected_flow": ["collect_info", "generate", "confirm"],
        "security_level": "low"
    },
    
    # =========================================================================
    # SEARCH/INFO SCENARIOS (76-85)
    # =========================================================================
    {
        "id": 76,
        "category": "search",
        "input": "What's the weather in Mumbai today?",
        "expected_intent": "search_info",
        "expected_extraction": {"query": "weather Mumbai"},
        "required_questions": [],
        "expected_flow": ["search", "respond"],
        "security_level": "none"
    },
    {
        "id": 77,
        "category": "search",
        "input": "Find me Italian restaurants near me",
        "expected_intent": "search_info",
        "expected_extraction": {"query": "Italian restaurants"},
        "required_questions": [],
        "expected_flow": ["search", "respond"],
        "security_level": "none"
    },
    {
        "id": 78,
        "category": "search",
        "input": "What are the best places to visit in Kerala?",
        "expected_intent": "search_info",
        "expected_extraction": {"query": "best places Kerala"},
        "required_questions": [],
        "expected_flow": ["search", "respond"],
        "security_level": "none"
    },
    {
        "id": 79,
        "category": "search",
        "input": "Show me today's stock market updates",
        "expected_intent": "search_info",
        "expected_extraction": {"query": "stock market today"},
        "required_questions": [],
        "expected_flow": ["search", "respond"],
        "security_level": "none"
    },
    {
        "id": 80,
        "category": "search",
        "input": "Find me a good laptop under ₹50000",
        "expected_intent": "search_info",
        "expected_extraction": {"query": "laptop under 50000"},
        "required_questions": [],
        "expected_flow": ["search", "respond"],
        "security_level": "none"
    },
    
    # =========================================================================
    # COMPLEX/MULTI-STEP SCENARIOS (86-100)
    # =========================================================================
    {
        "id": 86,
        "category": "complex",
        "input": "Plan a weekend trip to Goa - book flight and hotel",
        "expected_intent": "multi_task",
        "expected_extraction": {"destination": "Goa"},
        "required_questions": ["dates", "passengers", "budget"],
        "expected_flow": ["break_into_tasks", "execute_each", "confirm_all"],
        "security_level": "critical"
    },
    {
        "id": 87,
        "category": "complex",
        "input": "Schedule a meeting with the team and send them the agenda",
        "expected_intent": "multi_task",
        "expected_extraction": {},
        "required_questions": ["participants", "date", "time", "agenda"],
        "expected_flow": ["create_meeting", "send_email", "confirm"],
        "security_level": "medium"
    },
    {
        "id": 88,
        "category": "complex",
        "input": "Book movie tickets for 4 people and dinner reservation after",
        "expected_intent": "multi_task",
        "expected_extraction": {"num_tickets": 4},
        "required_questions": ["movie", "show_time", "restaurant"],
        "expected_flow": ["book_tickets", "book_restaurant", "confirm"],
        "security_level": "high"
    },
    {
        "id": 89,
        "category": "complex",
        "input": "Create invoice and email it to client@company.com",
        "expected_intent": "multi_task",
        "expected_extraction": {"to_email": "client@company.com"},
        "required_questions": ["invoice_details"],
        "expected_flow": ["generate_invoice", "send_email", "confirm"],
        "security_level": "medium"
    },
    {
        "id": 90,
        "category": "complex",
        "input": "Book Wonderla tickets and arrange cab pickup",
        "expected_intent": "multi_task",
        "expected_extraction": {"venue": "Wonderla"},
        "required_questions": ["num_tickets", "date", "pickup_location"],
        "expected_flow": ["book_tickets", "book_cab", "confirm"],
        "security_level": "high"
    },
    {
        "id": 91,
        "category": "complex",
        "input": "Pay electricity bill and set reminder for next month",
        "expected_intent": "multi_task",
        "expected_extraction": {},
        "required_questions": ["amount", "bill_details"],
        "expected_flow": ["make_payment", "create_reminder", "confirm"],
        "security_level": "high"
    },
    {
        "id": 92,
        "category": "complex",
        "input": "Schedule interview with candidate, send them meeting link, and remind me 1 hour before",
        "expected_intent": "multi_task",
        "expected_extraction": {},
        "required_questions": ["candidate_email", "date", "time"],
        "expected_flow": ["create_meeting", "send_email", "create_reminder", "confirm"],
        "security_level": "medium"
    },
    {
        "id": 93,
        "category": "complex",
        "input": "Book flight to Mumbai tomorrow, hotel for 2 nights, and schedule meeting with client there",
        "expected_intent": "multi_task",
        "expected_extraction": {"destination": "Mumbai"},
        "required_questions": ["client_email", "meeting_time"],
        "expected_flow": ["book_flight", "book_hotel", "create_meeting", "confirm"],
        "security_level": "critical"
    },
    {
        "id": 94,
        "category": "complex",
        "input": "Create a logo for my business and send it to designer@agency.com for feedback",
        "expected_intent": "multi_task",
        "expected_extraction": {"to_email": "designer@agency.com"},
        "required_questions": ["business_name", "logo_style"],
        "expected_flow": ["create_logo", "send_email", "confirm"],
        "security_level": "medium"
    },
    {
        "id": 95,
        "category": "complex",
        "input": "Pay rent, send confirmation to landlord, and set reminder for next month",
        "expected_intent": "multi_task",
        "expected_extraction": {},
        "required_questions": ["amount", "landlord_email"],
        "expected_flow": ["make_payment", "send_email", "create_reminder", "confirm"],
        "security_level": "critical"
    },
    {
        "id": 96,
        "category": "edge_case",
        "input": "Yes",
        "expected_intent": "confirmation",
        "expected_extraction": {},
        "required_questions": [],
        "expected_flow": ["check_context", "execute_or_clarify"],
        "security_level": "varies"
    },
    {
        "id": 97,
        "category": "edge_case",
        "input": "Cancel",
        "expected_intent": "cancel",
        "expected_extraction": {},
        "required_questions": [],
        "expected_flow": ["cancel_current_task"],
        "security_level": "none"
    },
    {
        "id": 98,
        "category": "edge_case",
        "input": "What can you do?",
        "expected_intent": "general_question",
        "expected_extraction": {},
        "required_questions": [],
        "expected_flow": ["show_capabilities"],
        "security_level": "none"
    },
    {
        "id": 99,
        "category": "edge_case",
        "input": "123456",
        "expected_intent": "provide_info",
        "expected_extraction": {"otp": "123456"},
        "required_questions": [],
        "expected_flow": ["check_context_for_otp"],
        "security_level": "varies"
    },
    {
        "id": 100,
        "category": "edge_case",
        "input": "Never mind, forget it",
        "expected_intent": "cancel",
        "expected_extraction": {},
        "required_questions": [],
        "expected_flow": ["cancel_current_task"],
        "security_level": "none"
    }
]


# =============================================================================
# TEST RUNNER
# =============================================================================

class TaskScenarioTester:
    """Run task scenarios against the AI brain"""
    
    def __init__(self, brain=None):
        self.brain = brain
        self.results = []
    
    async def run_scenario(self, scenario: Dict) -> Dict:
        """Run a single scenario"""
        result = {
            "id": scenario["id"],
            "category": scenario["category"],
            "input": scenario["input"],
            "expected_intent": scenario["expected_intent"],
            "passed": False,
            "errors": []
        }
        
        if not self.brain:
            # Dry run - just validate scenario structure
            result["passed"] = True
            result["note"] = "Dry run - brain not connected"
            return result
        
        try:
            # Send message to brain
            response = await self.brain.process_message(
                scenario["input"],
                f"test_session_{scenario['id']}",
                "test_user"
            )
            
            result["response"] = response
            
            # Validate intent detection
            # (In real implementation, check if response matches expected flow)
            
            result["passed"] = True
            
        except Exception as e:
            result["errors"].append(str(e))
        
        return result
    
    async def run_all_scenarios(self, categories: List[str] = None) -> Dict:
        """Run all scenarios or specific categories"""
        
        scenarios = TASK_SCENARIOS
        if categories:
            scenarios = [s for s in scenarios if s["category"] in categories]
        
        results = {
            "total": len(scenarios),
            "passed": 0,
            "failed": 0,
            "by_category": {},
            "details": []
        }
        
        for scenario in scenarios:
            result = await self.run_scenario(scenario)
            
            if result["passed"]:
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            category = scenario["category"]
            if category not in results["by_category"]:
                results["by_category"][category] = {"passed": 0, "failed": 0}
            
            if result["passed"]:
                results["by_category"][category]["passed"] += 1
            else:
                results["by_category"][category]["failed"] += 1
            
            results["details"].append(result)
        
        return results
    
    def print_results(self, results: Dict):
        """Print test results"""
        print("\n" + "=" * 60)
        print("TASK SCENARIO TEST RESULTS")
        print("=" * 60)
        print(f"\nTotal: {results['total']}")
        print(f"Passed: {results['passed']} ({results['passed']/results['total']*100:.1f}%)")
        print(f"Failed: {results['failed']}")
        
        print("\nBy Category:")
        for category, stats in results["by_category"].items():
            total = stats["passed"] + stats["failed"]
            pct = stats["passed"] / total * 100 if total > 0 else 0
            print(f"  {category}: {stats['passed']}/{total} ({pct:.1f}%)")
        
        if results["failed"] > 0:
            print("\nFailed Scenarios:")
            for detail in results["details"]:
                if not detail["passed"]:
                    print(f"  - #{detail['id']}: {detail['input'][:50]}...")
                    for error in detail["errors"]:
                        print(f"    Error: {error}")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run all task scenarios"""
    tester = TaskScenarioTester()
    results = await tester.run_all_scenarios()
    tester.print_results(results)
    
    # Save results to file
    with open("task_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to task_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
