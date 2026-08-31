"""ai_core/nodes/context_enrichment_node.py"""

import logging
from typing import Any

from ai_core.state import PaddyGraphState
from ai_core.utils.weather import get_agricultural_weather
from database.postgres_ai import get_medical_timeline
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


# This will retry up to 3 times, waiting 2s, 4s, then 8s between tries
@traceable(name="Fetch Open-Meteo API")
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_weather_with_retry(lat: float, lon: float) -> str:
    return get_agricultural_weather(lat, lon)


async def context_enrichment_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Fetches external context (Weather and Chat Logs) required for generation.
    Fails safely if APIs go down.
    """
    logger.info("---CONTEXT ENRICHMENT NODE---")
    location=state.get("location")
    lat = location.get("lat")
    lon = location.get("lon")
    cycle_id = state.get("cycle_id")

    # --- FETCH WEATHER ---
    weather_data = "Weather data currently unavailable."
    if lat and lon:
        try:
            logger.info(f"Fetching weather for Lat: {lat}, Lon: {lon}")
            weather_data = await get_weather_with_retry(lat, lon)
        except Exception:
            logger.exception("Weather API failed after retries. Using fallback.")
            weather_data = (
                "Weather data is currently unavailable due to a network error. "
                "CRITICAL: Advise the farmer to manually check weather conditions."
                "before applying any treatments."
            )
    else:
        logger.warning("No location provided in state. Skipping weather fetch.")

    # --- FETCH CHAT LOGS ---
    chat_logs = ""
    if cycle_id:
        try:
            logger.info(f"Fetching previous chat logs for session: {cycle_id}")

            chat_logs = await get_medical_timeline(cycle_id)
        except Exception:
            logger.exception("Failed to fetch chat logs.")
            chat_logs = "Previous conversation logs unavailable."

    # Update state
    return {"weather_context": weather_data, "medical_timeline": chat_logs}
