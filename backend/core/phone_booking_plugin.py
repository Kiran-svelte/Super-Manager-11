"""
Phone Call Plugin for Making Reservations and Bookings
Simulates phone calls to resorts, bakeries, etc.
"""
from typing import Dict, Any, List
import asyncio
from datetime import datetime

from .plugins import BasePlugin

class PhoneCallPlugin(BasePlugin):
    """Plugin for making phone calls to businesses"""
    
    def __init__(self):
        super().__init__("phone_call", "Make phone calls for reservations and bookings")
        self.call_history = []
    
    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute phone call action"""
        parameters = step.get("parameters", {})
        purpose = parameters.get("purpose", "general")
        
        if purpose == "room_reservation":
            return await self._call_for_room_reservation(parameters)
        elif purpose == "cake_order":
            return await self._call_bakery_for_cake(parameters)
        elif purpose == "restaurant_booking":
            return await self._call_restaurant(parameters)
        elif purpose == "activity_booking":
            return await self._call_for_activity(parameters)
        else:
            return await self._make_general_call(parameters)
    
    async def _call_for_room_reservation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate calling a resort/hotel for room reservation"""
        contact = parameters.get("contact", "Resort")
        details = parameters.get("details", {})
        
        # Simulate call delay
        await asyncio.sleep(0.5)
        
        call_record = {
            "type": "room_reservation",
            "contact": contact,
            "status": "completed",
            "booking_reference": f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "details": {
                "resort_name": contact,
                "check_in": details.get("check_in", "This weekend"),
                "check_out": details.get("check_out", "Next week"),
                "room_type": "Deluxe Room",
                "confirmation": "Confirmed"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.call_history.append(call_record)
        
        return {
            "status": "completed",
            "result": f"✅ Called {contact} - Room reservation confirmed",
            "output": {
                "booking_reference": call_record["booking_reference"],
                "confirmation_status": "Confirmed",
                "resort_name": contact,
                "message": f"Your room at {contact} has been reserved. Booking reference: {call_record['booking_reference']}"
            }
        }
    
    async def _call_bakery_for_cake(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate calling bakery for birthday cake order"""
        destination = parameters.get("destination", "")
        
        await asyncio.sleep(0.4)
        
        bakery_name = self._get_local_bakery(destination)
        order_number = f"CAKE{datetime.now().strftime('%Y%m%d%H%M')}"
        
        call_record = {
            "type": "cake_order",
            "contact": bakery_name,
            "status": "completed",
            "order_number": order_number,
            "details": {
                "cake_type": "Birthday Cake",
                "size": "2 kg",
                "flavor": "Chocolate Truffle",
                "delivery_time": "This weekend",
                "price": "₹1,500"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.call_history.append(call_record)
        
        return {
            "status": "completed",
            "result": f"✅ Called {bakery_name} - Birthday cake ordered",
            "output": {
                "order_number": order_number,
                "bakery_name": bakery_name,
                "cake_details": call_record["details"],
                "message": f"Birthday cake ordered from {bakery_name}. Order #: {order_number}"
            }
        }
    
    async def _call_restaurant(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate calling restaurant for table booking"""
        restaurant_name = parameters.get("restaurant", "Fine Dining Restaurant")
        
        await asyncio.sleep(0.4)
        
        booking_id = f"TBL{datetime.now().strftime('%Y%m%d%H%M')}"
        
        call_record = {
            "type": "restaurant_booking",
            "contact": restaurant_name,
            "status": "completed",
            "booking_id": booking_id,
            "details": {
                "restaurant": restaurant_name,
                "date": "This weekend",
                "time": "8:00 PM",
                "guests": "4 people",
                "table_type": "Window seat"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.call_history.append(call_record)
        
        return {
            "status": "completed",
            "result": f"✅ Called {restaurant_name} - Table booked",
            "output": {
                "booking_id": booking_id,
                "restaurant": restaurant_name,
                "details": call_record["details"],
                "message": f"Table reserved at {restaurant_name}. Booking ID: {booking_id}"
            }
        }
    
    async def _call_for_activity(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate calling for activity booking"""
        activity_name = parameters.get("activity", "Activity")
        
        await asyncio.sleep(0.3)
        
        booking_ref = f"ACT{datetime.now().strftime('%Y%m%d%H%M')}"
        
        return {
            "status": "completed",
            "result": f"✅ Booked {activity_name}",
            "output": {
                "booking_reference": booking_ref,
                "activity": activity_name,
                "message": f"{activity_name} has been booked. Reference: {booking_ref}"
            }
        }
    
    async def _make_general_call(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Make a general phone call"""
        contact = parameters.get("contact", "Contact")
        
        await asyncio.sleep(0.3)
        
        return {
            "status": "completed",
            "result": f"✅ Called {contact}",
            "output": {
                "contact": contact,
                "message": f"Successfully contacted {contact}"
            }
        }
    
    def _get_local_bakery(self, destination: str) -> str:
        """Get local bakery name based on destination"""
        bakeries = {
            "goa": "Confeitaria 31 de Janeiro (Goa's Famous Bakery)",
            "manali": "Johnson's Cafe & Bakery",
            "mumbai": "Theobroma Patisserie",
            "delhi": "Wenger's Bakery",
            "bangalore": "Iyengar's Bakery"
        }
        return bakeries.get(destination.lower(), "Local Artisan Bakery")
    
    def get_capabilities(self) -> List[str]:
        return ["phone_call", "call", "reservation", "booking", "contact"]
    
    def validate_parameters(self, parameters: Dict) -> bool:
        """Validate phone call parameters"""
        return "contact" in parameters or "purpose" in parameters


class BookingPlugin(BasePlugin):
    """Plugin for making various bookings"""
    
    def __init__(self):
        super().__init__("booking", "Handle various booking operations")
        self.bookings = []
    
    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute booking action"""
        parameters = step.get("parameters", {})
        booking_type = parameters.get("type", "general")
        
        await asyncio.sleep(0.3)
        
        booking_id = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        booking_record = {
            "id": booking_id,
            "type": booking_type,
            "details": parameters,
            "status": "confirmed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.bookings.append(booking_record)
        
        return {
            "status": "completed",
            "result": f"✅ Booking confirmed: {booking_type}",
            "output": {
                "booking_id": booking_id,
                "type": booking_type,
                "confirmation": "Confirmed",
                "message": f"Your booking has been confirmed. ID: {booking_id}"
            }
        }
    
    def get_capabilities(self) -> List[str]:
        return ["booking", "reserve", "book"]
