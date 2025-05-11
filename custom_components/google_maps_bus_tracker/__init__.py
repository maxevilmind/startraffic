"""The Google Maps Bus Tracker integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_API_KEY
from .api import GoogleMapsAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Google Maps Bus Tracker from a config entry."""
    try:
        # Initialize API client
        api_key = entry.data.get(CONF_API_KEY)
        if not api_key:
            raise ValueError("API key is required")
            
        api = GoogleMapsAPI(api_key)
        await api.initialize()

        # Store API client in hass.data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "api": api,
        }

        # Load platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        return True
    except Exception as err:
        _LOGGER.error("Error setting up Google Maps Bus Tracker: %s", err)
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        # Unload platforms
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

        # Clean up API client
        if entry.entry_id in hass.data[DOMAIN]:
            api = hass.data[DOMAIN][entry.entry_id]["api"]
            await api.cleanup()
            hass.data[DOMAIN].pop(entry.entry_id)

        return unload_ok
    except Exception as err:
        _LOGGER.error("Error unloading Google Maps Bus Tracker: %s", err)
        return False 