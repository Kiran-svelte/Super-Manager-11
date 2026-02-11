"""
DateTime Tool - Current Date/Time
===================================
Provides current date, time, and timezone conversions.
Uses Python stdlib - no external API needed.
Critical because the LLM doesn't know today's date.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones

from .base import Tool, ToolResult


# Common timezone aliases
TIMEZONE_ALIASES = {
    "ist": "Asia/Kolkata",
    "et": "US/Eastern",
    "est": "US/Eastern",
    "edt": "US/Eastern",
    "ct": "US/Central",
    "cst": "US/Central",
    "cdt": "US/Central",
    "mt": "US/Mountain",
    "mst": "US/Mountain",
    "pt": "US/Pacific",
    "pst": "US/Pacific",
    "pdt": "US/Pacific",
    "gmt": "GMT",
    "utc": "UTC",
    "jst": "Asia/Tokyo",
    "kst": "Asia/Seoul",
    "cet": "Europe/Paris",
    "bst": "Europe/London",
    "aest": "Australia/Sydney",
    "nzst": "Pacific/Auckland",
    "sgt": "Asia/Singapore",
    "hkt": "Asia/Hong_Kong",
    "india": "Asia/Kolkata",
    "london": "Europe/London",
    "new york": "US/Eastern",
    "los angeles": "US/Pacific",
    "tokyo": "Asia/Tokyo",
    "beijing": "Asia/Shanghai",
    "dubai": "Asia/Dubai",
    "sydney": "Australia/Sydney",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "moscow": "Europe/Moscow",
    "singapore": "Asia/Singapore",
    "hong kong": "Asia/Hong_Kong",
    "chicago": "US/Central",
    "denver": "US/Mountain",
    "bangalore": "Asia/Kolkata",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "kolkata": "Asia/Kolkata",
    "chennai": "Asia/Kolkata",
}


def resolve_timezone(tz_str: str) -> str:
    """Resolve a timezone string to a valid IANA timezone"""
    if not tz_str:
        return "UTC"

    lower = tz_str.lower().strip()

    # Check aliases first
    if lower in TIMEZONE_ALIASES:
        return TIMEZONE_ALIASES[lower]

    # Check if it's already a valid timezone
    if tz_str in available_timezones():
        return tz_str

    # Try case-insensitive match
    for tz in available_timezones():
        if tz.lower() == lower:
            return tz

    # Try partial match (e.g., "kolkata" matches "Asia/Kolkata")
    for tz in available_timezones():
        if lower in tz.lower():
            return tz

    return ""


class DateTimeTool(Tool):
    name = "datetime_info"
    description = "Get the current date and time in any timezone. Also converts between timezones. Use this whenever you need to know today's date or current time."
    parameters = {
        "timezone": {
            "description": "Timezone (e.g., 'Asia/Kolkata', 'US/Eastern', 'UTC', 'IST', 'Tokyo', 'New York')",
            "required": False,
            "type": "string",
            "default": "UTC",
        },
        "convert_to": {
            "description": "Target timezone to convert to (optional, for timezone conversion)",
            "required": False,
            "type": "string",
        },
    }
    requires_confirmation = False

    async def execute(self, **params) -> ToolResult:
        tz_input = params.get("timezone", "UTC") or "UTC"
        convert_to = params.get("convert_to", "")

        # Resolve the timezone
        tz_name = resolve_timezone(tz_input)
        if not tz_name:
            return ToolResult(
                success=False,
                output=f"Unknown timezone '{tz_input}'. Try using format like 'Asia/Kolkata', 'US/Eastern', or city names like 'Tokyo', 'London'.",
                error="invalid_timezone",
            )

        try:
            tz = ZoneInfo(tz_name)
            now = datetime.now(tz)

            result_lines = [
                f"Current date and time in {tz_name}:",
                f"  Date: {now.strftime('%A, %B %d, %Y')}",
                f"  Time: {now.strftime('%I:%M:%S %p')}",
                f"  24h:  {now.strftime('%H:%M:%S')}",
                f"  UTC offset: {now.strftime('%z')}",
            ]

            data = {
                "timezone": tz_name,
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "time_12h": now.strftime("%I:%M:%S %p"),
                "day": now.strftime("%A"),
                "iso": now.isoformat(),
            }

            # Handle timezone conversion
            if convert_to:
                target_tz_name = resolve_timezone(convert_to)
                if not target_tz_name:
                    result_lines.append(f"\nCould not find timezone '{convert_to}' for conversion.")
                else:
                    target_tz = ZoneInfo(target_tz_name)
                    target_now = now.astimezone(target_tz)
                    result_lines.extend([
                        f"",
                        f"Converted to {target_tz_name}:",
                        f"  Date: {target_now.strftime('%A, %B %d, %Y')}",
                        f"  Time: {target_now.strftime('%I:%M:%S %p')}",
                    ])
                    data["converted"] = {
                        "timezone": target_tz_name,
                        "date": target_now.strftime("%Y-%m-%d"),
                        "time": target_now.strftime("%H:%M:%S"),
                        "time_12h": target_now.strftime("%I:%M:%S %p"),
                    }

            return ToolResult(
                success=True,
                output="\n".join(result_lines),
                data=data,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Error getting time: {str(e)}",
                error=str(e),
            )
