"""ai_core/tools/weather.py: Agricultural weather tool for LangGraph."""

from collections import defaultdict
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Cache weather reports for 30 minutes per rounded (lat, lon) coordinate
WEATHER_CACHE_TTL_SECONDS = 30 * 60
_weather_cache: dict[tuple[float, float], tuple[float, str]] = {}

HTTP_HEADERS = {
    "User-Agent": "LiviaAI-AgriAdvisory/1.0 (https://github.com/livia-ai; support@livia-ai.app)",
    "Accept": "application/json",
}

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


def clear_weather_cache() -> None:
    """Clears the in-memory weather cache (useful for testing)."""
    _weather_cache.clear()


async def _fetch_open_meteo(
    client: httpx.AsyncClient, latitude: float, longitude: float
) -> str:
    """Primary provider: Open-Meteo Agricultural Forecast API."""
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

    response = await client.get(url, params=params, headers=HTTP_HEADERS, timeout=10.0)
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


async def _fetch_met_norway_fallback(
    client: httpx.AsyncClient, latitude: float, longitude: float
) -> str:
    """
    Backup provider: MET Norway Weather API (api.met.no).
    Free, requires no API key (only User-Agent header), and avoids Open-Meteo 429 rate limits on shared cloud IPs.
    """
    url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    params = {"lat": round(latitude, 4), "lon": round(longitude, 4)}

    response = await client.get(url, params=params, headers=HTTP_HEADERS, timeout=10.0)
    response.raise_for_status()
    data: dict[str, Any] = response.json()

    timeseries = data.get("properties", {}).get("timeseries", [])
    if not timeseries:
        raise ValueError("MET Norway returned empty timeseries.")

    # Current conditions from first entry
    first_data = timeseries[0].get("data", {})
    instant = first_data.get("instant", {}).get("details", {})
    next_1h = first_data.get("next_1_hours", {}) or first_data.get("next_6_hours", {})
    curr_symbol = (
        next_1h.get("summary", {}).get("symbol_code", "unknown").replace("_", " ").capitalize()
    )
    curr_precip = next_1h.get("details", {}).get("precipitation_amount", 0.0)

    curr_temp = instant.get("air_temperature", "N/A")
    curr_hum = instant.get("relative_humidity", "N/A")
    # Convert m/s to km/h for consistency with Open-Meteo output
    wind_ms = instant.get("wind_speed")
    curr_wind = round(wind_ms * 3.6, 1) if isinstance(wind_ms, (int, float)) else "N/A"

    # Aggregate daily min/max temp, total rain, and max wind over upcoming days
    daily_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"temps": [], "rain": 0.0, "winds": [], "symbols": []}
    )

    for entry in timeseries:
        time_str = entry.get("time", "")
        if len(time_str) < 10:
            continue
        day_key = time_str[:10]
        entry_data = entry.get("data", {})
        inst_details = entry_data.get("instant", {}).get("details", {})

        temp = inst_details.get("air_temperature")
        if isinstance(temp, (int, float)):
            daily_stats[day_key]["temps"].append(temp)

        w_ms = inst_details.get("wind_speed")
        if isinstance(w_ms, (int, float)):
            daily_stats[day_key]["winds"].append(round(w_ms * 3.6, 1))

        if "next_1_hours" in entry_data:
            rain = entry_data["next_1_hours"].get("details", {}).get("precipitation_amount", 0.0)
            sym = entry_data["next_1_hours"].get("summary", {}).get("symbol_code")
        elif "next_6_hours" in entry_data:
            rain = entry_data["next_6_hours"].get("details", {}).get("precipitation_amount", 0.0)
            sym = entry_data["next_6_hours"].get("summary", {}).get("symbol_code")
        else:
            rain = 0.0
            sym = None

        if isinstance(rain, (int, float)):
            daily_stats[day_key]["rain"] += rain
        if sym:
            daily_stats[day_key]["symbols"].append(sym.replace("_", " ").capitalize())

    report = (
        f"### Agricultural Weather Assessment (Lat: {latitude}, Lon: {longitude})\n\n"
        f"**Current Field Conditions:**\n"
        f"- Condition: {curr_symbol}\n"
        f"- Temperature: {curr_temp}°C (Feels like: {curr_temp}°C)\n"
        f"- Relative Humidity: {curr_hum}%\n"
        f"- Live Precipitation: {curr_precip} mm\n"
        f"- Wind: {curr_wind} km/h (Gusts: {curr_wind} km/h)\n"
        f"- Rootzone Soil Moisture (0-7cm): N/A\n\n"
        f"**Forecast Trend (Today & Upcoming 5 Days):**\n"
    )

    for day_key in sorted(daily_stats.keys())[:6]:
        stats = daily_stats[day_key]
        temps = stats["temps"]
        winds = stats["winds"]
        min_t = round(min(temps), 1) if temps else "N/A"
        max_t = round(max(temps), 1) if temps else "N/A"
        max_w = max(winds) if winds else "N/A"
        total_rain = round(stats["rain"], 1)
        cond = stats["symbols"][len(stats["symbols"]) // 2] if stats["symbols"] else "Fair"

        report += (
            f"- **{day_key}** ({cond}): "
            f"Temp: {min_t}°C to {max_t}°C | "
            f"Rain: {total_rain} mm | "
            f"Max Wind: {max_w} km/h\n"
        )

    return report


async def get_agricultural_weather(latitude: float, longitude: float) -> str:
    """
    Fetches comprehensive agricultural weather data for disease diagnosis and spray planning.
    Uses a 30-minute in-memory cache by (latitude, longitude) and automatically falls back
    to MET Norway if Open-Meteo returns 429 Too Many Requests or is unreachable.

    Raises:
        Exception: If both primary and backup weather providers fail, allowing Tenacity
                   @retry and the caller's fallback handler to execute properly.
    """
    cache_key = (round(float(latitude), 3), round(float(longitude), 3))
    now = time.monotonic()

    cached = _weather_cache.get(cache_key)
    if cached and (now - cached[0]) < WEATHER_CACHE_TTL_SECONDS:
        logger.info(f"Returning cached weather data for Lat: {latitude}, Lon: {longitude}")
        return cached[1]

    async with httpx.AsyncClient() as client:
        try:
            report = await _fetch_open_meteo(client, latitude, longitude)
            _weather_cache[cache_key] = (now, report)
            return report
        except httpx.HTTPError as primary_err:
            logger.warning(
                f"Primary Open-Meteo API failed ({primary_err!s}). "
                f"Switching to MET Norway backup provider for Lat: {latitude}, Lon: {longitude}."
            )
            report = await _fetch_met_norway_fallback(client, latitude, longitude)
            _weather_cache[cache_key] = (now, report)
            return report

