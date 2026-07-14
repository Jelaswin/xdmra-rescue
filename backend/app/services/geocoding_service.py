import httpx
import logging
from typing import List, Optional
from app.schemas import GeocodingResult

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# The user agent is required by Nominatim terms of service
HEADERS = {
    "User-Agent": "X-DMRARescue/1.0 (demo-hackathon-project)"
}

async def search_location(query: str, limit: int = 5) -> List[GeocodingResult]:
    """
    Search for a location using OpenStreetMap's Nominatim API.
    Returns a normalized list of GeocodingResult.
    """
    query = query.strip()
    if not query:
        return []
        
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                NOMINATIM_URL,
                headers=HEADERS,
                params={
                    "q": query,
                    "format": "json",
                    "limit": limit
                }
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data:
                # boundingbox is usually [lat_min, lat_max, lon_min, lon_max] in Nominatim
                bbox = None
                if "boundingbox" in item:
                    try:
                        bbox = [float(x) for x in item["boundingbox"]]
                    except (ValueError, TypeError):
                        bbox = None

                results.append(GeocodingResult(
                    display_name=item.get("display_name", ""),
                    latitude=float(item.get("lat", 0.0)),
                    longitude=float(item.get("lon", 0.0)),
                    provider="nominatim",
                    bounding_box=bbox
                ))
            return results

    except httpx.TimeoutException:
        logger.error(f"Geocoding timeout for query: {query}")
        return []
    except httpx.HTTPError as e:
        logger.error(f"Geocoding HTTP error: {e}")
        return []
    except Exception as e:
        logger.error(f"Geocoding unexpected error: {e}")
        return []
