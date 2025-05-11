"""The Google Maps Bus Tracker integration."""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_ORIGIN,
    CONF_DESTINATION,
    CONF_ROUTE_NUMBER,
)
from .api import GoogleMapsAPI

_LOGGER = logging.getLogger(__name__)

# Define the configuration schema
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.All(
        cv.ensure_list,
        [
            vol.Schema({
                vol.Required(CONF_ROUTE_NUMBER): cv.string,
                vol.Required(CONF_ORIGIN): cv.string,
                vol.Required(CONF_DESTINATION): cv.string,
            })
        ]
    )
})

PLATFORMS = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    """Set up the Google Maps Bus Tracker component."""
    if DOMAIN not in config:
        return True

    hass.data.setdefault(DOMAIN, {})
    
    # Create config entries for each bus route
    for bus_config in config[DOMAIN]:
        # Create a unique entry ID
        entry_id = f"{bus_config[CONF_ROUTE_NUMBER]}"
        
        # Create config entry
        entry = ConfigEntry(
            entry_id=entry_id,
            domain=DOMAIN,
            title=f"Bus {bus_config[CONF_ROUTE_NUMBER]}",
            data=bus_config,
            source="import",
        )
        
        # Add entry to hass
        hass.config_entries.async_add_entry(entry)
        
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Google Maps Bus Tracker from a config entry."""
    try:
        # Initialize API client
        api = GoogleMapsAPI(hass, entry.data)
        await api.initialize()

        # Store API client and bus routes in hass.data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "api": api,
            "bus_routes": {},
        }

        # Load platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Register services
        async def async_handle_reload(call: ServiceCall) -> None:
            """Handle reload service call."""
            await hass.config_entries.async_reload(entry.entry_id)

        async def async_handle_get_bus_info(call: ServiceCall) -> None:
            """Handle get_bus_info service call."""
            route_number = call.data.get(CONF_ROUTE_NUMBER)
            if not route_number:
                _LOGGER.error("Missing route number")
                return

            bus_routes = hass.data[DOMAIN][entry.entry_id]["bus_routes"]
            if route_number not in bus_routes:
                _LOGGER.error("Bus route %s not found", route_number)
                return

            bus_info = bus_routes[route_number]
            _LOGGER.info("Bus route %s info: %s", route_number, bus_info)

        async def async_handle_update_bus_route(call: ServiceCall) -> None:
            """Handle update_bus_route service call."""
            route_number = call.data.get(CONF_ROUTE_NUMBER)
            if not route_number:
                _LOGGER.error("Missing route number")
                return

            bus_routes = hass.data[DOMAIN][entry.entry_id]["bus_routes"]
            if route_number not in bus_routes:
                _LOGGER.error("Bus route %s not found", route_number)
                return

            # Update bus route configuration
            if CONF_ORIGIN in call.data:
                bus_routes[route_number][CONF_ORIGIN] = call.data[CONF_ORIGIN]
            if CONF_DESTINATION in call.data:
                bus_routes[route_number][CONF_DESTINATION] = call.data[CONF_DESTINATION]

            # Reload the integration to apply changes
            await hass.config_entries.async_reload(entry.entry_id)

        # Register main services
        hass.services.async_register(DOMAIN, "reload", async_handle_reload)
        hass.services.async_register(DOMAIN, "get_bus_info", async_handle_get_bus_info)
        hass.services.async_register(DOMAIN, "update_bus_route", async_handle_update_bus_route)

        return True
    except Exception as err:
        _LOGGER.error("Error setting up Google Maps Bus Tracker: %s", err)
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        # Unload platforms
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

        # Clean up API client and bus routes
        if entry.entry_id in hass.data[DOMAIN]:
            api = hass.data[DOMAIN][entry.entry_id]["api"]
            await api.cleanup()
            hass.data[DOMAIN].pop(entry.entry_id)

        return unload_ok
    except Exception as err:
        _LOGGER.error("Error unloading Google Maps Bus Tracker: %s", err)
        return False 