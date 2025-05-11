"""The sensor component for the Google Maps Bus Tracker integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    CONF_ORIGIN,
    CONF_DESTINATION,
    CONF_ROUTE_NUMBER,
    DEFAULT_SCAN_INTERVAL,
)
from .api import GoogleMapsAPIError

_LOGGER = logging.getLogger(__name__)

# Define entity descriptions
SENSOR_TYPES = {
    "stop_name": SensorEntityDescription(
        key="stop_name",
        name="Stop Name",
        icon="mdi:bus-stop",
    ),
    "line_number": SensorEntityDescription(
        key="line_number",
        name="Line Number",
        icon="mdi:bus",
    ),
    "next_departure": SensorEntityDescription(
        key="next_departure",
        name="Next Departure",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
}

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Bus Tracker sensor from a config entry."""
    try:
        # Get the API instance from hass.data
        api = hass.data[DOMAIN][config_entry.entry_id]["api"]
        if not api:
            raise ValueError("API client not initialized")

        # Get configuration from the config entry
        route_number = config_entry.data.get(CONF_ROUTE_NUMBER)
        origin = config_entry.data.get(CONF_ORIGIN)
        destination = config_entry.data.get(CONF_DESTINATION)

        if not all([route_number, origin, destination]):
            _LOGGER.error("Missing required configuration parameters")
            return

        # Create coordinator for this bus route
        coordinator = BusTrackerCoordinator(
            hass,
            api,
            origin,
            destination,
            route_number,
        )

        # Create entities for this bus route
        entities = [
            BusTrackerSensor(coordinator, description)
            for description in SENSOR_TYPES.values()
        ]

        # Add entities to Home Assistant
        async_add_entities(entities)

        _LOGGER.info("Created entities for bus route %s", route_number)

    except Exception as err:
        _LOGGER.error("Error setting up Bus Tracker sensors: %s", err)
        raise

class BusTrackerCoordinator(DataUpdateCoordinator):
    """Coordinator for Bus Tracker data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: GoogleMapsAPI,
        origin: str,
        destination: str,
        route_number: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Bus {route_number} Tracker",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self.origin = origin
        self.destination = destination
        self.route_number = route_number

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            response = await self.api.get_directions(
                self.origin,
                self.destination,
                self.route_number,
            )
            return self._extract_bus_info(response)
        except GoogleMapsAPIError as err:
            _LOGGER.error("API error: %s", err)
            return {}
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            return {}

    def _extract_bus_info(self, response: dict[str, Any]) -> dict[str, Any]:
        """Extract relevant bus information from the API response."""
        try:
            if not response.get("routes"):
                _LOGGER.debug("No routes found in response")
                return {}

            route = response["routes"][0]
            leg = route["legs"][0]
            steps = leg["steps"]

            # Find the first bus step
            bus_step = next(
                (step for step in steps if step["travel_mode"] == "TRANSIT"),
                None,
            )

            if not bus_step:
                _LOGGER.debug("No bus transit found in route")
                return {}

            transit_details = bus_step.get("transit_details", {})
            departure_stop = transit_details.get("departure_stop", {})
            line = transit_details.get("line", {})

            # Get departure time
            departure_time = transit_details.get("departure_time", {})
            departure_timestamp = departure_time.get("value")
            departure_dt = None
            if departure_timestamp:
                try:
                    departure_dt = datetime.fromtimestamp(departure_timestamp, tz=ZoneInfo("UTC"))
                    departure_dt = departure_dt.astimezone(dt_util.get_time_zone(hass.config.time_zone))
                except (ValueError, TypeError) as err:
                    _LOGGER.error("Error parsing departure time: %s", err)

            return {
                "stop_name": departure_stop.get("name", "Unknown"),
                "line_number": line.get("short_name", "Unknown"),
                "next_departure": departure_dt,
            }
        except Exception as err:
            _LOGGER.error("Error extracting bus info: %s", err)
            return {}

class BusTrackerSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Bus Tracker sensor."""

    def __init__(
        self,
        coordinator: BusTrackerCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.route_number}_{description.key}"
        self._attr_name = f"Bus {coordinator.route_number} {description.name}"

    @property
    def state(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self.entity_description.key)
        
        # Handle timestamp sensors
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            if value is None:
                return None
            if isinstance(value, datetime):
                return value
            try:
                return dt_util.parse_datetime(str(value))
            except (ValueError, TypeError) as err:
                _LOGGER.error("Error parsing timestamp: %s", err)
                return None

        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.coordinator.data:
            return {}

        return {
            "route_number": self.coordinator.route_number,
        } 