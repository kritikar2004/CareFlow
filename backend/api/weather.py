import os

import requests
from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_current_user
from backend.database.models import User


router = APIRouter(
    prefix="/weather",
    tags=["Weather"],
)


WEATHER_API_URL = "https://api.weatherapi.com/v1/current.json"


@router.get("")
def get_weather(
    current_user: User = Depends(get_current_user),
):
    api_key = os.getenv("WEATHER_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Weather API key is not configured.",
        )

    city = current_user.city.strip()

    if not city:
        raise HTTPException(
            status_code=400,
            detail="Hospital city is not configured.",
        )

    try:
        response = requests.get(
            WEATHER_API_URL,
            params={
                "key": api_key,
                "q": city,
                "aqi": "no",
            },
            timeout=10,
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach the weather service.",
        )

    if response.status_code != 200:
        try:
            error_data = response.json()
            error_message = (
                error_data.get("error", {}).get("message")
                or "Weather service request failed."
            )
        except ValueError:
            error_message = "Weather service request failed."

        raise HTTPException(
            status_code=502,
            detail=error_message,
        )

    data = response.json()
    location = data.get("location", {})
    current = data.get("current", {})
    condition = current.get("condition", {})

    return {
        "city": location.get("name") or city,
        "country": location.get("country"),
        "local_time": location.get("localtime"),
        "temperature": current.get("temp_c"),
        "feels_like": current.get("feelslike_c"),
        "humidity": current.get("humidity"),
        "rainfall": current.get("precip_mm"),
        "condition": condition.get("text"),
        "condition_icon": condition.get("icon"),
        "wind_kph": current.get("wind_kph"),
        "last_updated": current.get("last_updated"),
    }