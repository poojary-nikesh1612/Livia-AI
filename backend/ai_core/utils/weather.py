"""ai_core/tools/weather.py: Agricultural weather tool for LangGraph."""

import httpx

# WMO Weather interpretation codes
WMO_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


async def get_agricultural_weather(latitude: float, longitude: float) -> str:
    """
    Fetches comprehensive agricultural weather data for disease diagnosis and spray planning.
    Includes current farm microclimate and an 11-day timeline (5 days past, current day,
    5 days forecast) tracking moisture, rain probability, wind gusts, and evapotranspiration.

    Args:
        latitude: The latitude of the farm location.
        longitude: The longitude of the farm location.
    """
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "precipitation,weather_code,wind_speed_10m,wind_gusts_10m,soil_moisture_0_to_7cm"
        ),
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_sum,precipitation_probability_max,wind_gusts_10m_max,"
            "uv_index_max,et0_fao_evapotranspiration"
        ),
        "past_days": 5,
        "forecast_days": 5,
        "timezone": "auto",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            # 1. Parse Current Real-Time Metrics
            current = data.get("current", {})
            curr_temp = current.get("temperature_2m", "N/A")
            curr_feels = current.get("apparent_temperature", "N/A")
            curr_hum = current.get("relative_humidity_2m", "N/A")
            curr_precip = current.get("precipitation", "N/A")
            curr_wind = current.get("wind_speed_10m", "N/A")
            curr_gusts = current.get("wind_gusts_10m", "N/A")
            curr_soil = current.get("soil_moisture_0_to_7cm", "N/A")
            curr_wmo = current.get("weather_code", 0)
            curr_condition = WMO_DESCRIPTIONS.get(curr_wmo, f"Code {curr_wmo}")

            # 2. Parse Daily 11-Day Timeline
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            wmo_codes = daily.get("weather_code", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            precip_sums = daily.get("precipitation_sum", [])
            rain_probs = daily.get("precipitation_probability_max", [])
            wind_gust_max = daily.get("wind_gusts_10m_max", [])
            uv_indices = daily.get("uv_index_max", [])
            evapotrans = daily.get("et0_fao_evapotranspiration", [])

            report = (
                f"### Agricultural Weather Assessment (Lat: {latitude}, Lon: {longitude})\n\n"
                f"**Current Field Conditions:**\n"
                f"- Condition: {curr_condition}\n"
                f"- Temperature: {curr_temp}°C (Feels like: {curr_feels}°C)\n"
                f"- Relative Humidity: {curr_hum}%\n"
                f"- Live Precipitation: {curr_precip} mm\n"
                f"- Wind: {curr_wind} km/h (Gusts: {curr_gusts} km/h)\n"
                f"- Rootzone Soil Moisture (0-7cm): {curr_soil} m³/m³\n\n"
                f"**11-Day Trend (5 Days Historical Past, Today, 5 Days Forecast):**\n"
            )

            for i in range(len(dates)):
                wmo_desc = (
                    WMO_DESCRIPTIONS.get(wmo_codes[i], f"Code {wmo_codes[i]}")
                    if i < len(wmo_codes)
                    else "N/A"
                )
                prob = (
                    rain_probs[i]
                    if (i < len(rain_probs) and rain_probs[i] is not None)
                    else "N/A"
                )
                gust = wind_gust_max[i] if i < len(wind_gust_max) else "N/A"
                uv = uv_indices[i] if i < len(uv_indices) else "N/A"
                et0 = evapotrans[i] if i < len(evapotrans) else "N/A"

                report += (
                    f"- **{dates[i]}** ({wmo_desc}): "
                    f"Temp: {min_temps[i]}°C to {max_temps[i]}°C | "
                    f"Rain: {precip_sums[i]} mm (Rain Risk: {prob}%) | "
                    f"Max Gusts: {gust} km/h | UV: {uv} | ET₀: {et0} mm\n"
                )

            return report

        except httpx.HTTPError as e:
            return f"Error fetching weather data: HTTP request failed ({e!s})."
        except (KeyError, IndexError, ValueError, TypeError) as e:
            return f"Error processing weather data structure: {e!s}"
