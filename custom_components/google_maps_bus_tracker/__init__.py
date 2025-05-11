"""The Google Maps Bus Tracker integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .api import GoogleMapsAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Google Maps Bus Tracker from a config entry."""
    try:
        # Store the API key in hass.data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {}

        # Initialize the API client
        api_key = entry.data.get("api_key")
        if not api_key:
            raise ValueError("API key is required")
        
        api = GoogleMapsAPI(api_key)
        hass.data[DOMAIN][entry.entry_id]["api"] = api

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    except Exception as err:
        _LOGGER.error("Error setting up Google Maps Bus Tracker: %s", err)
        raise ConfigEntryNotReady from err

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Clean up API session
        if api := hass.data[DOMAIN][entry.entry_id].get("api"):
            await api.close()
        
        # Clean up coordinators
        if coordinators := hass.data[DOMAIN][entry.entry_id].get("coordinators"):
            for coordinator in coordinators.values():
                await coordinator.async_shutdown()
        
        # Remove service
        hass.services.async_remove(DOMAIN, "track_bus")
        
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok 