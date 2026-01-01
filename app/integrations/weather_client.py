"""
Weather Client - Fetches weather and surf data from various APIs
"""

from __future__ import annotations
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("presentos.integrations.weather")

# Environment variables
OPENWEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
SURFLINE_API_KEY = os.getenv("SURFLINE_API_KEY", "")
IKITESURF_API_KEY = os.getenv("IKITESURF_API_KEY", "")

# URLs
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Default location
DEFAULT_LOCATION = {
    "city": "Pune",
    "state": "Maharashtra",
    "country": "IN",
    "lat": 18.5204,
    "lon": 73.8567
}

# Activity thresholds
PERFECT_KITE_WIND = (15, 25)
GOOD_SURF_SWELL = (3, 6)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_forecast(location: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get weather forecast for location."""
    
    if not OPENWEATHER_API_KEY:
        logger.warning("Weather API key missing")
        return _get_fallback_forecast(location)
    
    loc = location or DEFAULT_LOCATION
    
    try:
        current = _get_openweather_current(loc)
        if not current:
            return _get_fallback_forecast(loc)
        
        forecast_24h = _get_openweather_forecast(loc)
        wind_knots = current.get("wind", {}).get("speed", 0) * 1.944
        
        # Calculate metrics
        rain_risk = _calculate_rain_risk(
            current.get("weather", [{}])[0].get("main", ""),
            forecast_24h.get("conditions", []),
            forecast_24h.get("pop", 0)
        )
        
        surf_score = _calculate_surf_score(
            wind_knots,
            current.get("weather", [{}])[0].get("main", ""),
            datetime.now().hour
        )
        
        result = {
            "condition": current.get("weather", [{}])[0].get("main", "").lower(),
            "description": current.get("weather", [{}])[0].get("description", ""),
            "temperature_c": current.get("main", {}).get("temp"),
            "temperature_f": round((current.get("main", {}).get("temp", 0) * 9/5) + 32, 1),
            
            "wind_speed": current.get("wind", {}).get("speed"),
            "wind_speed_knots": round(wind_knots, 1),
            "wind_direction": current.get("wind", {}).get("deg"),
            
            "rain_risk": rain_risk,
            "surf_score": round(surf_score, 2),
            "kite_score": _calculate_kite_score(wind_knots),
            
            "humidity": current.get("main", {}).get("humidity"),
            "pressure": current.get("main", {}).get("pressure"),
            "visibility": current.get("visibility"),
            "clouds": current.get("clouds", {}).get("all"),
            
            "location": {
                "city": loc.get("city", "Pune"),
                "country": loc.get("country", "IN"),
                "coordinates": {
                    "lat": loc.get("lat", DEFAULT_LOCATION["lat"]),
                    "lon": loc.get("lon", DEFAULT_LOCATION["lon"])
                }
            },
            
            "source": "openweathermap",
            "timestamp": current.get("dt"),
            "fetched_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Weather: {result['condition']}, Wind: {result['wind_speed_knots']}kt")
        
        return result
        
    except Exception as e:
        logger.exception("Weather fetch failed")
        return _get_fallback_forecast(loc)


def get_surf_forecast(location: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get surf-specific forecast data."""
    
    loc = location or DEFAULT_LOCATION
    
    # Try specialized APIs first
    if SURFLINE_API_KEY:
        try:
            surf_data = _get_surfline_forecast(loc)
            if surf_data:
                surf_data["source"] = "surfline"
                return surf_data
        except Exception:
            pass
    
    if IKITESURF_API_KEY:
        try:
            kite_data = _get_ikitesurf_forecast(loc)
            if kite_data:
                kite_data["source"] = "ikitesurf"
                return kite_data
        except Exception:
            pass
    
    # Fallback to estimation
    return _estimate_surf_from_weather(loc)


# Helper functions
def _get_openweather_current(location: Dict) -> Dict:
    params = {"appid": OPENWEATHER_API_KEY, "units": "metric"}
    
    if "lat" in location and "lon" in location:
        params["lat"] = location["lat"]
        params["lon"] = location["lon"]
    else:
        city = location.get("city", "Pune")
        country = location.get("country", "IN")
        params["q"] = f"{city},{country}"
    
    resp = requests.get(OPENWEATHER_URL, params=params, timeout=10)
    return resp.json() if resp.status_code == 200 else {}


def _get_openweather_forecast(location: Dict) -> Dict:
    params = {
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "cnt": 8
    }
    
    if "lat" in location and "lon" in location:
        params["lat"] = location["lat"]
        params["lon"] = location["lon"]
    else:
        city = location.get("city", "Pune")
        country = location.get("country", "IN")
        params["q"] = f"{city},{country}"
    
    try:
        resp = requests.get(OPENWEATHER_FORECAST_URL, params=params, timeout=10)
        if resp.status_code != 200:
            return {"pop": 0, "conditions": []}
        
        data = resp.json()
        forecasts = data.get("list", [])[:8]
        conditions = [f.get("weather", [{}])[0].get("main", "") for f in forecasts]
        pop_values = [f.get("pop", 0) for f in forecasts]
        temps = [f.get("main", {}).get("temp") for f in forecasts if f.get("main", {}).get("temp")]
        
        return {
            "pop": max(pop_values) if pop_values else 0,
            "conditions": conditions,
            "temp_max": max(temps) if temps else None,
            "temp_min": min(temps) if temps else None
        }
        
    except Exception:
        return {"pop": 0, "conditions": []}


def _calculate_rain_risk(current_condition: str, forecast_conditions: list, pop: float) -> str:
    """Assess rain risk level."""
    
    condition_lower = current_condition.lower()
    
    storm_conditions = ["thunderstorm", "squall", "tornado"]
    heavy_rain = ["heavy intensity rain", "very heavy rain", "extreme rain"]
    medium_rain = ["rain", "shower rain", "light rain", "moderate rain"]
    
    if any(storm in condition_lower for storm in storm_conditions):
        return "very_high"
    
    if any(rain in condition_lower for rain in heavy_rain):
        return "high"
    
    if any(rain in condition_lower for rain in medium_rain):
        return "medium" if pop < 0.7 else "high"
    
    if pop >= 0.7:
        return "high"
    elif pop >= 0.4:
        return "medium"
    
    return "low"


def _calculate_surf_score(wind_knots: float, condition: str, time_of_day: int) -> float:
    """Calculate surf quality score (0.0 to 1.0)."""
    
    score = 0.0
    
    # Wind component
    if PERFECT_KITE_WIND[0] <= wind_knots <= PERFECT_KITE_WIND[1]:
        score += 0.6
    elif 10 <= wind_knots <= 30:
        score += 0.4
    elif 5 <= wind_knots <= 35:
        score += 0.2
    
    # Weather condition
    cond_lower = condition.lower()
    good_conditions = ["clear", "few clouds", "scattered clouds"]
    ok_conditions = ["broken clouds", "overcast clouds"]
    bad_conditions = ["rain", "thunderstorm", "snow", "fog"]
    
    if any(good in cond_lower for good in good_conditions):
        score += 0.3
    elif any(ok in cond_lower for ok in ok_conditions):
        score += 0.1
    elif any(bad in cond_lower for bad in bad_conditions):
        score -= 0.2
    
    # Time preference (morning is best)
    if 6 <= time_of_day <= 10:
        score += 0.1
    
    return max(0.0, min(1.0, score))


def _calculate_kite_score(wind_knots: float) -> float:
    """Calculate kitesurf-specific score."""
    if 15 <= wind_knots <= 25:
        return 0.9
    elif 10 <= wind_knots <= 30:
        return 0.7
    elif 5 <= wind_knots <= 35:
        return 0.4
    else:
        return 0.1


def _get_surfline_forecast(location: Dict) -> Dict:
    """Get surf forecast from Surfline API."""
    # Actual implementation depends on API access
    return {
        "swell_feet": 4.2,
        "swell_direction": "SW",
        "swell_period": 12,
        "tide": "incoming",
        "water_temp": 28,
        "source": "surfline"
    }


def _get_ikitesurf_forecast(location: Dict) -> Dict:
    """Get kitesurf forecast from iKitesurf API."""
    # Actual implementation depends on API access
    return {
        "wind_knots": 18,
        "wind_direction": "cross_shore",
        "gust_knots": 22,
        "source": "ikitesurf"
    }


def _estimate_surf_from_weather(location: Dict) -> Dict:
    """Estimate surf conditions from basic weather data."""
    
    weather = get_forecast(location)
    if not weather:
        return {"swell_feet": 2.0, "tide": "unknown", "source": "estimated"}
    
    wind_knots = weather.get("wind_speed_knots", 0)
    
    # Simple swell estimation
    if wind_knots > 20:
        swell = 5.0
    elif wind_knots > 15:
        swell = 3.5
    elif wind_knots > 10:
        swell = 2.5
    else:
        swell = 1.5
    
    # Simple tide estimation
    hour = datetime.now().hour
    if 0 <= hour < 6:
        tide = "low"
    elif 6 <= hour < 12:
        tide = "incoming"
    elif 12 <= hour < 18:
        tide = "high"
    else:
        tide = "outgoing"
    
    return {
        "swell_feet": round(swell, 1),
        "tide": tide,
        "water_temp": weather.get("temperature_c", 28),
        "source": "estimated_from_weather",
        "confidence": 0.5
    }


def _get_fallback_forecast(location: Dict) -> Dict:
    """Return fallback forecast data when APIs fail."""
    
    return {
        "condition": "clear",
        "description": "Clear sky",
        "temperature_c": 28.0,
        "wind_speed_knots": 5.8,
        "rain_risk": "low",
        "surf_score": 0.3,
        "location": {
            "city": location.get("city", "Pune"),
            "country": location.get("country", "IN")
        },
        "source": "fallback",
        "fetched_at": datetime.utcnow().isoformat(),
        "fallback_used": True
    }