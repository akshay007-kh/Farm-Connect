"""Small Open-Meteo adapter; cache at the caller and respect provider terms."""
import requests

def forecast(latitude: float, longitude: float) -> dict:
    response = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": latitude, "longitude": longitude,
        "daily": "temperature_2m_max,precipitation_probability_max",
        "timezone": "Asia/Kolkata", "forecast_days": 7,
    }, timeout=10)
    response.raise_for_status()
    return response.json()
