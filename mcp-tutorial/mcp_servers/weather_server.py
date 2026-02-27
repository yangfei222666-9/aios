"""
Weather MCP Server - 天气查询服务
基于 OpenWeather API
"""
import os
import json
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Weather MCP Server")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherRequest(BaseModel):
    city: str
    units: str = "metric"  # metric (摄氏度) or imperial (华氏度)


class WeatherResponse(BaseModel):
    city: str
    temperature: float
    feels_like: float
    humidity: int
    description: str
    wind_speed: float


@app.get("/")
def root():
    return {
        "name": "Weather MCP Server",
        "version": "1.0.0",
        "protocol": "MCP",
        "capabilities": ["weather_query"]
    }


@app.post("/weather", response_model=WeatherResponse)
def get_weather(request: WeatherRequest) -> WeatherResponse:
    """查询城市天气"""
    if not OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenWeather API Key not configured")
    
    try:
        params = {
            "q": request.city,
            "appid": OPENWEATHER_API_KEY,
            "units": request.units,
            "lang": "zh_cn"
        }
        
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return WeatherResponse(
            city=data["name"],
            temperature=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            humidity=data["main"]["humidity"],
            description=data["weather"][0]["description"],
            wind_speed=data["wind"]["speed"]
        )
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Weather API error: {str(e)}")


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy", "api_key_configured": bool(OPENWEATHER_API_KEY)}


if __name__ == "__main__":
    import uvicorn
    print("🌤️  Weather MCP Server starting on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
