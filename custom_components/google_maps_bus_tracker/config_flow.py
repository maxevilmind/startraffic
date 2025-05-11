"""Config flow for Google Maps Bus Tracker integration."""
from __future__ import annotations

import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from typing import Any

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_ORIGIN,
    CONF_DESTINATION,
    CONF_ROUTE_NUMBER,
)

_LOGGER = logging.getLogger(__name__)

class BusTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Bus Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate coordinates
                for field in [CONF_ORIGIN, CONF_DESTINATION]:
                    lat, lon = map(float, user_input[field].split(','))
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        errors[field] = "invalid_coordinates"
                
                if not errors:
                    return self.async_create_entry(
                        title=f"Bus {user_input[CONF_ROUTE_NUMBER]}",
                        data=user_input,
                    )
            except ValueError:
                errors[CONF_ORIGIN] = "invalid_coordinates"
                errors[CONF_DESTINATION] = "invalid_coordinates"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_ORIGIN, description={
                    "suggested_value": "52.1234567,4.1234567",
                    "description": "Origin coordinates (latitude,longitude)"
                }): str,
                vol.Required(CONF_DESTINATION, description={
                    "suggested_value": "52.1234567,4.1234567",
                    "description": "Destination coordinates (latitude,longitude)"
                }): str,
                vol.Required(CONF_ROUTE_NUMBER): str,
            }),
            errors=errors,
        ) 