import httpx
from datetime import datetime, timezone

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherLookupError(Exception):
    pass


async def get_district_forecast(district: str) -> dict:
    """Fetch today's forecast for a given Indian district using Open-Meteo (free, no API key).

    Raises WeatherLookupError on any failure so the caller can handle it gracefully.
    """
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            geo_resp = await client.get(
                GEOCODING_URL,
                params={"name": district, "country": "IN", "count": 1},
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()

            results = geo_data.get("results")
            if not results:
                raise WeatherLookupError(f"Could not find location data for '{district}'.")

            location = results[0]
            lat = location["latitude"]
            lon = location["longitude"]
            resolved_name = location.get("name", district)

            forecast_resp = await client.get(
                FORECAST_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                    "timezone": "auto",
                },
            )
            forecast_resp.raise_for_status()
            forecast_data = forecast_resp.json()

            daily = forecast_data.get("daily")
            if not daily or not daily.get("time"):
                raise WeatherLookupError("Weather service returned no forecast data.")

            return {
                "location": resolved_name,
                "date": daily["time"][0],
                "temp_max": daily["temperature_2m_max"][0],
                "temp_min": daily["temperature_2m_min"][0],
                "precipitation_mm": daily["precipitation_sum"][0],
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

    except httpx.TimeoutException:
        raise WeatherLookupError("The weather service took too long to respond.")
    except httpx.HTTPStatusError:
        raise WeatherLookupError("The weather service returned an error.")
    except (KeyError, IndexError):
        raise WeatherLookupError("Weather data came back in an unexpected format.")