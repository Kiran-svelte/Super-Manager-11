"""
Interactive UI Components System
Provides button-based, card-based, and form-based interactive elements
for the chat interface.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
import secrets


class ComponentType(Enum):
    """Types of UI components"""
    BUTTON = "button"
    BUTTON_GROUP = "button_group"
    CARD = "card"
    CARD_GRID = "card_grid"
    CAROUSEL = "carousel"
    FORM = "form"
    LIST = "list"
    TABLE = "table"
    CONFIRMATION = "confirmation"
    PAYMENT = "payment"
    SELECTION = "selection"
    DATE_PICKER = "date_picker"
    TIME_PICKER = "time_picker"
    LOCATION_PICKER = "location_picker"
    FILE_UPLOAD = "file_upload"
    PROGRESS = "progress"
    SUMMARY = "summary"
    RECEIPT = "receipt"


class ButtonStyle(Enum):
    """Button styling options"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    DANGER = "danger"
    WARNING = "warning"
    INFO = "info"
    OUTLINE = "outline"
    GHOST = "ghost"


class CardStyle(Enum):
    """Card styling options"""
    DEFAULT = "default"
    ELEVATED = "elevated"
    BORDERED = "bordered"
    FEATURED = "featured"
    COMPACT = "compact"


@dataclass
class Button:
    """Interactive button component"""
    id: str
    label: str
    action: str  # Action identifier
    style: ButtonStyle = ButtonStyle.PRIMARY
    icon: Optional[str] = None
    disabled: bool = False
    loading: bool = False
    tooltip: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "label": self.label,
            "action": self.action,
            "style": self.style.value,
            "icon": self.icon,
            "disabled": self.disabled,
            "loading": self.loading,
            "tooltip": self.tooltip,
            "metadata": self.metadata
        }


@dataclass
class ButtonGroup:
    """Group of buttons"""
    buttons: List[Button]
    layout: str = "horizontal"  # horizontal, vertical, grid
    columns: int = 2  # For grid layout
    allow_multiple: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "type": ComponentType.BUTTON_GROUP.value,
            "layout": self.layout,
            "columns": self.columns,
            "allow_multiple": self.allow_multiple,
            "buttons": [b.to_dict() for b in self.buttons]
        }


@dataclass
class Card:
    """Information card component"""
    id: str
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon: Optional[str] = None
    price: Optional[str] = None
    original_price: Optional[str] = None
    discount: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    actions: List[Button] = field(default_factory=list)
    style: CardStyle = CardStyle.DEFAULT
    metadata: Dict = field(default_factory=dict)
    selectable: bool = False
    selected: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
            "image_url": self.image_url,
            "icon": self.icon,
            "price": self.price,
            "original_price": self.original_price,
            "discount": self.discount,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "tags": self.tags,
            "features": self.features,
            "actions": [a.to_dict() for a in self.actions],
            "style": self.style.value,
            "metadata": self.metadata,
            "selectable": self.selectable,
            "selected": self.selected
        }


@dataclass
class CardGrid:
    """Grid of cards for selection"""
    cards: List[Card]
    columns: int = 2
    selection_mode: str = "single"  # single, multiple, none
    title: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "type": ComponentType.CARD_GRID.value,
            "title": self.title,
            "description": self.description,
            "columns": self.columns,
            "selection_mode": self.selection_mode,
            "cards": [c.to_dict() for c in self.cards]
        }


@dataclass
class FormField:
    """Form field component"""
    name: str
    label: str
    type: str  # text, email, phone, number, date, time, select, checkbox, radio
    required: bool = False
    placeholder: Optional[str] = None
    default_value: Optional[Any] = None
    options: Optional[List[Dict]] = None  # For select, radio
    validation: Optional[Dict] = None  # Validation rules
    help_text: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "label": self.label,
            "type": self.type,
            "required": self.required,
            "placeholder": self.placeholder,
            "default_value": self.default_value,
            "options": self.options,
            "validation": self.validation,
            "help_text": self.help_text
        }


@dataclass
class Form:
    """Form component for data collection"""
    id: str
    title: str
    fields: List[FormField]
    submit_label: str = "Submit"
    cancel_label: str = "Cancel"
    description: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "type": ComponentType.FORM.value,
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "fields": [f.to_dict() for f in self.fields],
            "submit_label": self.submit_label,
            "cancel_label": self.cancel_label
        }


@dataclass
class ListItem:
    """List item component"""
    id: str
    title: str
    subtitle: Optional[str] = None
    icon: Optional[str] = None
    trailing: Optional[str] = None
    action: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "icon": self.icon,
            "trailing": self.trailing,
            "action": self.action,
            "metadata": self.metadata
        }


@dataclass
class ListComponent:
    """List component"""
    items: List[ListItem]
    title: Optional[str] = None
    selectable: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "type": ComponentType.LIST.value,
            "title": self.title,
            "selectable": self.selectable,
            "items": [i.to_dict() for i in self.items]
        }


@dataclass
class ConfirmationDialog:
    """Confirmation dialog for important actions"""
    id: str
    title: str
    message: str
    details: List[Dict]  # Key-value pairs to show
    security_level: str = "medium"  # low, medium, high, critical
    confirm_button: Button = None
    cancel_button: Button = None
    requires_otp: bool = False
    warning: Optional[str] = None
    
    def __post_init__(self):
        if not self.confirm_button:
            self.confirm_button = Button(
                id="confirm",
                label="Confirm",
                action="confirm",
                style=ButtonStyle.PRIMARY
            )
        if not self.cancel_button:
            self.cancel_button = Button(
                id="cancel",
                label="Cancel",
                action="cancel",
                style=ButtonStyle.SECONDARY
            )
    
    def to_dict(self) -> Dict:
        return {
            "type": ComponentType.CONFIRMATION.value,
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "security_level": self.security_level,
            "confirm_button": self.confirm_button.to_dict(),
            "cancel_button": self.cancel_button.to_dict(),
            "requires_otp": self.requires_otp,
            "warning": self.warning
        }


@dataclass
class PaymentComponent:
    """Secure payment component"""
    id: str
    amount: float
    currency: str = "INR"
    description: str = ""
    merchant_name: str = ""
    items: List[Dict] = field(default_factory=list)  # Line items
    payment_methods: List[str] = field(default_factory=lambda: ["upi", "card", "netbanking"])
    upi_id: Optional[str] = None
    qr_code: Optional[str] = None
    expiry_minutes: int = 15
    reference_id: str = field(default_factory=lambda: secrets.token_hex(8))
    security_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    
    def to_dict(self) -> Dict:
        return {
            "type": ComponentType.PAYMENT.value,
            "id": self.id,
            "amount": self.amount,
            "currency": self.currency,
            "formatted_amount": f"₹{self.amount:,.2f}",
            "description": self.description,
            "merchant_name": self.merchant_name,
            "items": self.items,
            "payment_methods": self.payment_methods,
            "upi_id": self.upi_id,
            "qr_code": self.qr_code,
            "expiry_minutes": self.expiry_minutes,
            "reference_id": self.reference_id,
            "security_token": self.security_token
        }


@dataclass
class Receipt:
    """Receipt/confirmation component"""
    id: str
    title: str
    status: str  # success, pending, failed
    reference_number: str
    timestamp: str
    items: List[Dict]
    total: float
    currency: str = "INR"
    merchant: Optional[str] = None
    payment_method: Optional[str] = None
    actions: List[Button] = field(default_factory=list)
    qr_code: Optional[str] = None
    downloadable: bool = True
    shareable: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "type": ComponentType.RECEIPT.value,
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "reference_number": self.reference_number,
            "timestamp": self.timestamp,
            "items": self.items,
            "total": self.total,
            "formatted_total": f"₹{self.total:,.2f}",
            "currency": self.currency,
            "merchant": self.merchant,
            "payment_method": self.payment_method,
            "actions": [a.to_dict() for a in self.actions],
            "qr_code": self.qr_code,
            "downloadable": self.downloadable,
            "shareable": self.shareable
        }


@dataclass
class ProgressIndicator:
    """Progress/status indicator"""
    current_step: int
    total_steps: int
    steps: List[Dict]  # {name, status, description}
    title: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "type": ComponentType.PROGRESS.value,
            "title": self.title,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "percentage": int((self.current_step / self.total_steps) * 100),
            "steps": self.steps
        }


class UIBuilder:
    """Builder class for creating interactive UI components"""
    
    @staticmethod
    def create_option_buttons(
        options: List[Dict],
        action_prefix: str = "select",
        layout: str = "vertical",
        columns: int = 2
    ) -> ButtonGroup:
        """Create option buttons from a list of options"""
        buttons = []
        for i, opt in enumerate(options):
            buttons.append(Button(
                id=f"{action_prefix}_{i}",
                label=opt.get("label", f"Option {i+1}"),
                action=f"{action_prefix}:{opt.get('id', i)}",
                style=ButtonStyle.OUTLINE if not opt.get("recommended") else ButtonStyle.PRIMARY,
                icon=opt.get("icon"),
                tooltip=opt.get("description"),
                metadata=opt.get("metadata", {})
            ))
        
        return ButtonGroup(
            buttons=buttons,
            layout=layout,
            columns=columns
        )
    
    @staticmethod
    def create_destination_cards(destinations: List[Dict]) -> CardGrid:
        """Create destination selection cards"""
        cards = []
        for dest in destinations:
            cards.append(Card(
                id=dest.get("id", secrets.token_hex(4)),
                title=dest.get("name"),
                subtitle=dest.get("distance"),
                description=dest.get("description"),
                image_url=dest.get("image_url"),
                tags=dest.get("tags", []),
                features=dest.get("highlights", []),
                rating=dest.get("rating"),
                reviews_count=dest.get("reviews_count"),
                actions=[
                    Button(
                        id=f"select_{dest.get('id')}",
                        label="Select",
                        action=f"select_destination:{dest.get('id')}",
                        style=ButtonStyle.PRIMARY
                    ),
                    Button(
                        id=f"details_{dest.get('id')}",
                        label="Details",
                        action=f"view_details:{dest.get('id')}",
                        style=ButtonStyle.OUTLINE
                    )
                ],
                selectable=True,
                metadata=dest
            ))
        
        return CardGrid(
            cards=cards,
            columns=2,
            selection_mode="single",
            title="Choose Your Destination",
            description="Select a destination to continue planning your trip"
        )
    
    @staticmethod
    def create_offer_cards(offers: List[Dict]) -> CardGrid:
        """Create offer/deal cards"""
        cards = []
        for offer in offers:
            cards.append(Card(
                id=offer.get("id", secrets.token_hex(4)),
                title=offer.get("name"),
                subtitle=offer.get("provider"),
                description=offer.get("description"),
                price=f"₹{offer.get('price'):,}" if offer.get('price') else None,
                original_price=f"₹{offer.get('original_price'):,}" if offer.get('original_price') else None,
                discount=offer.get("discount"),
                tags=offer.get("tags", []),
                features=offer.get("features", []),
                actions=[
                    Button(
                        id=f"select_{offer.get('id')}",
                        label="Select This Offer",
                        action=f"select_offer:{offer.get('id')}",
                        style=ButtonStyle.SUCCESS
                    )
                ],
                style=CardStyle.FEATURED if offer.get("recommended") else CardStyle.DEFAULT,
                selectable=True,
                metadata=offer
            ))
        
        return CardGrid(
            cards=cards,
            columns=1,
            selection_mode="single",
            title="Available Offers",
            description="Select the best offer for you"
        )
    
    @staticmethod
    def create_booking_form(booking_type: str, prefilled: Dict = None) -> Form:
        """Create a booking form"""
        fields = []
        
        if booking_type in ["ticket", "movie", "event"]:
            fields = [
                FormField(
                    name="quantity",
                    label="Number of Tickets",
                    type="number",
                    required=True,
                    default_value=prefilled.get("quantity", 1) if prefilled else 1,
                    validation={"min": 1, "max": 10}
                ),
                FormField(
                    name="date",
                    label="Date",
                    type="date",
                    required=True,
                    default_value=prefilled.get("date") if prefilled else None
                ),
                FormField(
                    name="time",
                    label="Preferred Time",
                    type="select",
                    required=True,
                    options=[
                        {"value": "morning", "label": "Morning (9 AM - 12 PM)"},
                        {"value": "afternoon", "label": "Afternoon (12 PM - 5 PM)"},
                        {"value": "evening", "label": "Evening (5 PM - 9 PM)"}
                    ]
                ),
                FormField(
                    name="contact_name",
                    label="Contact Name",
                    type="text",
                    required=True,
                    placeholder="Enter your full name"
                ),
                FormField(
                    name="contact_phone",
                    label="Phone Number",
                    type="phone",
                    required=True,
                    placeholder="+91 XXXXXXXXXX",
                    validation={"pattern": r"^\+?[0-9]{10,12}$"}
                ),
                FormField(
                    name="contact_email",
                    label="Email",
                    type="email",
                    required=True,
                    placeholder="your@email.com"
                )
            ]
        
        return Form(
            id=f"booking_form_{booking_type}",
            title="Booking Details",
            description="Please fill in the required information",
            fields=fields,
            submit_label="Continue to Payment",
            cancel_label="Cancel Booking"
        )
    
    @staticmethod
    def create_payment_confirmation(
        amount: float,
        items: List[Dict],
        merchant: str,
        security_level: str = "high"
    ) -> ConfirmationDialog:
        """Create a payment confirmation dialog"""
        details = [
            {"label": "Merchant", "value": merchant},
            {"label": "Amount", "value": f"₹{amount:,.2f}"},
        ]
        
        for item in items[:5]:  # Show max 5 items
            details.append({
                "label": item.get("name"),
                "value": f"₹{item.get('price', 0):,.2f}"
            })
        
        return ConfirmationDialog(
            id=f"payment_confirm_{secrets.token_hex(4)}",
            title="Confirm Payment",
            message="Please review and confirm your payment details",
            details=details,
            security_level=security_level,
            requires_otp=security_level in ["high", "critical"],
            warning="This action will initiate a payment. Please ensure all details are correct.",
            confirm_button=Button(
                id="confirm_payment",
                label="Confirm & Pay",
                action="confirm_payment",
                style=ButtonStyle.SUCCESS,
                icon="lock"
            ),
            cancel_button=Button(
                id="cancel_payment",
                label="Cancel",
                action="cancel_payment",
                style=ButtonStyle.SECONDARY
            )
        )
    
    @staticmethod
    def create_secure_payment(
        amount: float,
        description: str,
        merchant: str,
        merchant_upi: str,
        items: List[Dict] = None
    ) -> PaymentComponent:
        """Create a secure payment component"""
        return PaymentComponent(
            id=f"payment_{secrets.token_hex(6)}",
            amount=amount,
            description=description,
            merchant_name=merchant,
            items=items or [],
            upi_id=merchant_upi,
            payment_methods=["upi", "card", "netbanking", "wallet"]
        )
    
    @staticmethod
    def create_booking_receipt(
        booking_id: str,
        booking_type: str,
        items: List[Dict],
        total: float,
        merchant: str,
        payment_method: str,
        booking_details: Dict
    ) -> Receipt:
        """Create a booking receipt"""
        from datetime import datetime
        
        return Receipt(
            id=booking_id,
            title=f"{booking_type.title()} Booking Confirmed",
            status="success",
            reference_number=booking_id,
            timestamp=datetime.now().isoformat(),
            items=items,
            total=total,
            merchant=merchant,
            payment_method=payment_method,
            actions=[
                Button(
                    id="download_receipt",
                    label="Download Receipt",
                    action="download_receipt",
                    style=ButtonStyle.PRIMARY,
                    icon="download"
                ),
                Button(
                    id="share_receipt",
                    label="Share",
                    action="share_receipt",
                    style=ButtonStyle.OUTLINE,
                    icon="share"
                ),
                Button(
                    id="add_to_calendar",
                    label="Add to Calendar",
                    action="add_to_calendar",
                    style=ButtonStyle.OUTLINE,
                    icon="calendar"
                )
            ],
            downloadable=True,
            shareable=True
        )
    
    @staticmethod
    def create_meeting_scheduler(
        title: str = "Schedule Meeting",
        participants: List[str] = None,
        suggested_times: List[Dict] = None
    ) -> Dict:
        """Create a meeting scheduler component"""
        return {
            "type": "meeting_scheduler",
            "title": title,
            "participants": participants or [],
            "suggested_times": suggested_times or [],
            "fields": [
                {
                    "name": "title",
                    "label": "Meeting Title",
                    "type": "text",
                    "required": True
                },
                {
                    "name": "date",
                    "label": "Date",
                    "type": "date",
                    "required": True
                },
                {
                    "name": "time",
                    "label": "Time",
                    "type": "time",
                    "required": True
                },
                {
                    "name": "duration",
                    "label": "Duration",
                    "type": "select",
                    "options": [
                        {"value": "15", "label": "15 minutes"},
                        {"value": "30", "label": "30 minutes"},
                        {"value": "45", "label": "45 minutes"},
                        {"value": "60", "label": "1 hour"},
                        {"value": "90", "label": "1.5 hours"},
                        {"value": "120", "label": "2 hours"}
                    ],
                    "required": True
                },
                {
                    "name": "platform",
                    "label": "Meeting Platform",
                    "type": "select",
                    "options": [
                        {"value": "google_meet", "label": "Google Meet"},
                        {"value": "zoom", "label": "Zoom"},
                        {"value": "teams", "label": "Microsoft Teams"},
                        {"value": "in_person", "label": "In Person"}
                    ],
                    "required": True
                }
            ]
        }


class InteractiveResponse:
    """Builder for interactive chat responses"""
    
    def __init__(self):
        self.text: Optional[str] = None
        self.components: List[Dict] = []
        self.metadata: Dict = {}
    
    def with_text(self, text: str) -> 'InteractiveResponse':
        """Add text message"""
        self.text = text
        return self
    
    def with_component(self, component: Any) -> 'InteractiveResponse':
        """Add a UI component"""
        if hasattr(component, 'to_dict'):
            self.components.append(component.to_dict())
        elif isinstance(component, dict):
            self.components.append(component)
        return self
    
    def with_buttons(self, options: List[Dict], layout: str = "vertical") -> 'InteractiveResponse':
        """Add button options"""
        button_group = UIBuilder.create_option_buttons(options, layout=layout)
        self.components.append(button_group.to_dict())
        return self
    
    def with_cards(self, cards: List[Dict], columns: int = 2) -> 'InteractiveResponse':
        """Add card grid"""
        card_objects = [Card(**c) if isinstance(c, dict) else c for c in cards]
        card_grid = CardGrid(cards=card_objects, columns=columns)
        self.components.append(card_grid.to_dict())
        return self
    
    def with_confirmation(self, title: str, message: str, details: List[Dict]) -> 'InteractiveResponse':
        """Add confirmation dialog"""
        confirmation = ConfirmationDialog(
            id=secrets.token_hex(4),
            title=title,
            message=message,
            details=details
        )
        self.components.append(confirmation.to_dict())
        return self
    
    def with_metadata(self, **kwargs) -> 'InteractiveResponse':
        """Add metadata"""
        self.metadata.update(kwargs)
        return self
    
    def build(self) -> Dict:
        """Build the response"""
        return {
            "text": self.text,
            "interactive": len(self.components) > 0,
            "components": self.components,
            "metadata": self.metadata
        }
