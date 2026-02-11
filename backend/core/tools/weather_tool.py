"""
Weather Tool - Open-Meteo API
==============================
Get current weather and forecast for any location.
Completely free, no API key needed, no signup required.
Uses Open-Meteo geocoding + weather API.
"""

import httpx

from .base import Tool, ToolResult


# WMO Weather interpretation codes
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherTool(Tool):
    name = "weather"
    description = "Get current weather and 3-day forecast for any city or location. Free, no API key needed."
    parameters = {
        "location": {
            "description": "City name (e.g., 'Bangalore', 'New York', 'Tokyo')",
            "required": True,
            "type": "string",
        },
    }
    requires_confirmation = False

    async def execute(self, **params) -> ToolResult:
        location = params.get("location", "")

        if not location:
            return ToolResult(
                success=False,
                output="Please provide a location.",
                error="missing_location",
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Step 1: Geocode the location
                geo_resp = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": location, "count": 1, "language": "en"},
                )
                geo_data = geo_resp.json()

                if not geo_data.get("results"):
                    return ToolResult(
                        success=False,
                        output=f"Could not find location '{location}'. Try a different city name.",
                        error="location_not_found",
                    )

                place = geo_data["results"][0]
                lat = place["latitude"]
                lon = place["longitude"]
                city_name = place.get("name", location)
                country = place.get("country", "")
                full_location = f"{city_name}, {country}" if country else city_name

                # Step 2: Get weather
                weather_resp = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current_weather": True,
                        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                        "timezone": "auto",
                        "forecast_days": 3,
                    },
                )
                weather = weather_resp.json()

                current = weather.get("current_weather", {})
                daily = weather.get("daily", {})

                temp = current.get("temperature", "N/A")
                windspeed = current.get("windspeed", "N/A")
                weather_code = current.get("weathercode", 0)
                condition = WMO_CODES.get(weather_code, "Unknown")

                # Build output
                lines = [
                    f"Weather for {full_location}:",
                    f"",
                    f"Current: {temp}°C, {condition}",
                    f"Wind: {windspeed} km/h",
                    f"",
                    f"3-Day Forecast:",
                ]

                dates = daily.get("time", [])
                maxs = daily.get("temperature_2m_max", [])
                mins = daily.get("temperature_2m_min", [])
                precips = daily.get("precipitation_sum", [])
                codes = daily.get("weathercode", [])

                for i in range(min(3, len(dates))):
                    day_condition = WMO_CODES.get(codes[i] if i < len(codes) else 0, "")
                    precip = precips[i] if i < len(precips) else 0
                    rain = f", Rain: {precip}mm" if precip > 0 else ""
                    lines.append(
                        f"  {dates[i]}: {mins[i]}°C - {maxs[i]}°C, {day_condition}{rain}"
                    )

                output = "\n".join(lines)

                return ToolResult(
                    success=True,
                    output=output,
                    data={
                        "location": full_location,
                        "current": {
                            "temperature": temp,
                            "condition": condition,
                            "windspeed": windspeed,
                        },
                        "forecast": [
                            {
                                "date": dates[i] if i < len(dates) else "",
                                "max": maxs[i] if i < len(maxs) else None,
                                "min": mins[i] if i < len(mins) else None,
                                "condition": WMO_CODES.get(
                                    codes[i] if i < len(codes) else 0, ""
                                ),
                                "precipitation": precips[i] if i < len(precips) else 0,
                            }
                            for i in range(min(3, len(dates)))
                        ],
                        "ui_components": {
                            "type": "info_card",
                            "title": f"Weather - {full_location}",
                            "data": {
                                "Temperature": f"{temp}°C",
                                "Condition": condition,
                                "Wind": f"{windspeed} km/h",
                            },
                        },
                    },
                )

        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                output="Weather service timed out. Please try again.",
                error="timeout",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Failed to get weather: {str(e)}",
                error=str(e),
            )
