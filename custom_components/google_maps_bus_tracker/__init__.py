"""The Google Maps Bus Tracker integration."""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN
from .api import GoogleMapsAPI

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({})

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Google Maps Bus Tracker from a config entry."""
    try:
        # Initialize API client
        api = GoogleMapsAPI(hass, entry.data)
        await api.initialize()

        # Store API client in hass.data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {"api": api}

        # Load platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Load services
        hass.services.async_register(
            DOMAIN,
            "reload",
            lambda call: hass.config_entries.async_reload(entry.entry_id),
        )

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