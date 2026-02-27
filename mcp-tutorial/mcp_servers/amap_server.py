"""
AMap MCP Server - 高德地图服务
支持地点搜索、路线规划
"""
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AMap MCP Server")

AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")
SEARCH_URL = "https://restapi.amap.com/v3/place/text"
GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"


class PlaceSearchRequest(BaseModel):
    keywords: str
    city: Optional[str] = None
    limit: int = 10


class Place(BaseModel):
    name: str
    address: str
    location: str  # "经度,纬度"
    type: str


class PlaceSearchResponse(BaseModel):
    places: List[Place]
    count: int


class GeocodeRequest(BaseModel):
    address: str
    city: Optional[str] = None


class GeocodeResponse(BaseModel):
    address: str
    location: str
    formatted_address: str


@app.get("/")
def root():
    return {
        "name": "AMap MCP Server",
        "version": "1.0.0",
        "protocol": "MCP",
        "capabilities": ["place_search", "geocode"]
    }


@app.post("/search", response_model=PlaceSearchResponse)
def search_places(request: PlaceSearchRequest) -> PlaceSearchResponse:
    """搜索地点"""
    if not AMAP_API_KEY:
        raise HTTPException(status_code=500, detail="AMap API Key not configured")
    
    try:
        params = {
            "key": AMAP_API_KEY,
            "keywords": request.keywords,
            "offset": request.limit,
            "extensions": "base"
        }
        
        if request.city:
            params["city"] = request.city
        
        response = requests.get(SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "1":
            raise HTTPException(status_code=500, detail=f"AMap API error: {data.get('info')}")
        
        places = []
        for poi in data.get("pois", []):
            places.append(Place(
                name=poi.get("name", ""),
                address=poi.get("address", ""),
                location=poi.get("location", ""),
                type=poi.get("type", "")
            ))
        
        return PlaceSearchResponse(places=places, count=len(places))
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"AMap API error: {str(e)}")


@app.post("/geocode", response_model=GeocodeResponse)
def geocode_address(request: GeocodeRequest) -> GeocodeResponse:
    """地址转坐标"""
    if not AMAP_API_KEY:
        raise HTTPException(status_code=500, detail="AMap API Key not configured")
    
    try:
        params = {
            "key": AMAP_API_KEY,
            "address": request.address
        }
        
        if request.city:
            params["city"] = request.city
        
        response = requests.get(GEOCODE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "1":
            raise HTTPException(status_code=500, detail=f"AMap API error: {data.get('info')}")
        
        geocodes = data.get("geocodes", [])
        if not geocodes:
            raise HTTPException(status_code=404, detail="Address not found")
        
        geocode = geocodes[0]
        
        return GeocodeResponse(
            address=request.address,
            location=geocode.get("location", ""),
            formatted_address=geocode.get("formatted_address", "")
        )
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"AMap API error: {str(e)}")


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy", "api_key_configured": bool(AMAP_API_KEY)}


if __name__ == "__main__":
    import uvicorn
    print("🗺️  AMap MCP Server starting on http://localhost:8003")
    uvicorn.run(app, host="0.0.0.0", port=8003)
