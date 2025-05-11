"""The sensor component for the Google Maps Bus Tracker integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_ORIGIN,
    CONF_DESTINATION,
    CONF_ROUTE_NUMBER,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .api import GoogleMapsAPI

_LOGGER = logging.getLogger(__name__)

# Define entity descriptions
SENSOR_TYPES = {
    "next_departure": SensorEntityDescription(
        key="next_departure",
        name="Next Departure",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    "arrival_time": SensorEntityDescription(
        key="arrival_time",
        name="Arrival Time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    "duration": SensorEntityDescription(
        key="duration",
        name="Duration",
        native_unit_of_measurement="min",
        state_class=SensorStateClass.MEASUREMENT,
    ),
}

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Bus Tracker sensor from a config entry."""
    api_key = config_entry.data[CONF_API_KEY]
    origin = config_entry.data[CONF_ORIGIN]
    destination = config_entry.data[CONF_DESTINATION]
    route_number = config_entry.data[CONF_ROUTE_NUMBER]

    api = GoogleMapsAPI(api_key)
    coordinator = BusTrackerCoordinator(
        hass,
        api,
        origin,
        destination,
        route_number,
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        BusTrackerSensor(coordinator, description)
        for description in SENSOR_TYPES.values()
    )

class BusTrackerCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: GoogleMapsAPI,
        origin: str,
        destination: str,
        route_number: str,
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Bus Tracker",
            update_interval=timedelta(minutes=1),
        )
        self.api = api
        self.origin = origin
        self.destination = destination
        self.route_number = route_number

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            response = await self.api.get_directions(
                self.origin,
                self.destination,
                self.route_number,
            )
            return self._extract_bus_info(response)
        except Exception as err:
            _LOGGER.error("Error fetching bus data: %s", err)
            return {}

    def _extract_bus_info(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant bus information from the API response."""
        try:
            if not response.get("routes"):
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
                return {}

            transit_details = bus_step.get("transit_details", {})
            departure_stop = transit_details.get("departure_stop", {})
            arrival_stop = transit_details.get("arrival_stop", {})
            line = transit_details.get("line", {})

            # Get departure time
            departure_time = transit_details.get("departure_time", {})
            departure_timestamp = departure_time.get("value")
            if departure_timestamp:
                departure_dt = datetime.fromtimestamp(departure_timestamp, tz=ZoneInfo("UTC"))
                departure_dt = departure_dt.astimezone(dt_util.get_time_zone("Europe/Amsterdam"))
            else:
                departure_dt = None

            # Get arrival time
            arrival_time = transit_details.get("arrival_time", {})
            arrival_timestamp = arrival_time.get("value")
            if arrival_timestamp:
                arrival_dt = datetime.fromtimestamp(arrival_timestamp, tz=ZoneInfo("UTC"))
                arrival_dt = arrival_dt.astimezone(dt_util.get_time_zone("Europe/Amsterdam"))
            else:
                arrival_dt = None

            # Calculate duration in minutes
            duration = int(leg["duration"]["value"] / 60) if leg.get("duration") else None

            return {
                "next_departure": departure_dt,
                "arrival_time": arrival_dt,
                "duration": duration,
                "departure_stop": departure_stop.get("name", "Unknown"),
                "arrival_stop": arrival_stop.get("name", "Unknown"),
                "line_name": line.get("name", "Unknown"),
                "line_number": line.get("short_name", "Unknown"),
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
            except (ValueError, TypeError):
                return None

        return value

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.coordinator.data:
            return {}

        return {
            "departure_stop": self.coordinator.data.get("departure_stop"),
            "arrival_stop": self.coordinator.data.get("arrival_stop"),
            "line_name": self.coordinator.data.get("line_name"),
            "line_number": self.coordinator.data.get("line_number"),
        } 