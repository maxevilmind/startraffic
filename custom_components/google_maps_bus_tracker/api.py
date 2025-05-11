"""Google Maps API client for the Bus Tracker integration."""
from __future__ import annotations

import logging
import aiohttp
from typing import Any, Dict, Optional
from datetime import datetime

from .const import DIRECTIONS_API_URL

_LOGGER = logging.getLogger(__name__)

class GoogleMapsAPIError(Exception):
    """Base exception for Google Maps API errors."""
    pass

class GoogleMapsAPI:
    """Google Maps API client."""

    def __init__(self, api_key: str) -> None:
        """Initialize the API client.
        
        Args:
            api_key: Google Maps API key
        """
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize the API client by creating a session."""
        await self._get_session()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session.
        
        Returns:
            aiohttp.ClientSession: The HTTP session
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def get_directions(
        self,
        origin: str,
        destination: str,
        route_number: str,
    ) -> Dict[str, Any]:
        """Get directions from Google Maps API.
        
        Args:
            origin: Origin coordinates (latitude,longitude)
            destination: Destination coordinates (latitude,longitude)
            route_number: Bus route number to filter results
            
        Returns:
            Dict containing the API response or empty dict on error
            
        Raises:
            GoogleMapsAPIError: If the API request fails
        """
        if not all([origin, destination, route_number]):
            raise ValueError("Origin, destination, and route number are required")

        session = await self._get_session()
        
        params = {
            "origin": origin,
            "destination": destination,
            "mode": "transit",
            "transit_mode": "bus",
            "key": self.api_key,
            "departure_time": "now",  # Get real-time transit information
        }

        try:
            async with session.get(DIRECTIONS_API_URL, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                status = data.get("status")
                if status != "OK":
                    error_message = f"Google Maps API error: {status}"
                    if error_details := data.get("error_message"):
                        error_message += f" - {error_details}"
                    _LOGGER.error(error_message)
                    raise GoogleMapsAPIError(error_message)
                
                return data
        except aiohttp.ClientError as err:
            error_message = f"Error fetching data from Google Maps API: {err}"
            _LOGGER.error(error_message)
            raise GoogleMapsAPIError(error_message) from err
        except Exception as err:
            error_message = f"Unexpected error: {err}"
            _LOGGER.error(error_message)
            raise GoogleMapsAPIError(error_message) from err

    async def cleanup(self) -> None:
        """Clean up resources by closing the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None 