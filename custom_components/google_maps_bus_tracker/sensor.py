"""The sensor component for the Google Maps Bus Tracker integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
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
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.entity_registry import async_get_registry

from .const import (
    DOMAIN,
    CONF_ORIGIN,
    CONF_DESTINATION,
    CONF_ROUTE_NUMBER,
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

        # Initialize coordinators storage
        if "coordinators" not in hass.data[DOMAIN][config_entry.entry_id]:
            hass.data[DOMAIN][config_entry.entry_id]["coordinators"] = {}

        # Register the service
        async def async_handle_track_bus(call: ServiceCall) -> None:
            """Handle the track_bus service call."""
            route_number = call.data.get(CONF_ROUTE_NUMBER)
            origin = call.data.get(CONF_ORIGIN)
            destination = call.data.get(CONF_DESTINATION)

            if not all([route_number, origin, destination]):
                _LOGGER.error("Missing required parameters")
                return

            # Check if we already have a coordinator for this route
            if route_number in hass.data[DOMAIN][config_entry.entry_id]["coordinators"]:
                _LOGGER.warning("Bus route %s is already being tracked", route_number)
                return

            # Create coordinator for this bus route
            coordinator = BusTrackerCoordinator(
                hass,
                api,
                origin,
                destination,
                route_number,
            )

            await coordinator.async_config_entry_first_refresh()

            # Create entities for this bus route
            entities = [
                BusTrackerSensor(coordinator, description)
                for description in SENSOR_TYPES.values()
            ]

            # Add entities to Home Assistant
            async_add_entities(entities)

            # Store coordinator in hass.data
            hass.data[DOMAIN][config_entry.entry_id]["coordinators"][route_number] = coordinator

            _LOGGER.info("Started tracking bus route %s", route_number)

        # Register the service
        hass.services.async_register(
            DOMAIN,
            "track_bus",
            async_handle_track_bus,
        )

        # Register service to remove bus tracking
        async def async_handle_untrack_bus(call: ServiceCall) -> None:
            """Handle the untrack_bus service call."""
            route_number = call.data.get(CONF_ROUTE_NUMBER)
            if not route_number:
                _LOGGER.error("Missing route number")
                return

            # Get the entity registry
            registry = await async_get_registry(hass)
            
            # Remove all entities for this route
            for sensor_type in SENSOR_TYPES:
                entity_id = f"sensor.bus_{route_number}_{sensor_type}"
                if entity := registry.async_get(entity_id):
                    registry.async_remove(entity.entity_id)

            # Remove coordinator
            if route_number in hass.data[DOMAIN][config_entry.entry_id]["coordinators"]:
                coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinators"][route_number]
                await coordinator.async_shutdown()
                hass.data[DOMAIN][config_entry.entry_id]["coordinators"].pop(route_number)
                _LOGGER.info("Stopped tracking bus route %s", route_number)

        hass.services.async_register(
            DOMAIN,
            "untrack_bus",
            async_handle_untrack_bus,
        )

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
        """Initialize the coordinator.
        
        Args:
            hass: Home Assistant instance
            api: Google Maps API client
            origin: Origin coordinates
            destination: Destination coordinates
            route_number: Bus route number
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"Bus {route_number} Tracker",
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
        except GoogleMapsAPIError as err:
            _LOGGER.error("API error: %s", err)
            return {}
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            return {}

    def _extract_bus_info(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant bus information from the API response.
        
        Args:
            response: API response data
            
        Returns:
            Dict containing extracted bus information
        """
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
                    departure_dt = departure_dt.astimezone(dt_util.get_time_zone("Europe/Amsterdam"))
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
        """Initialize the sensor.
        
        Args:
            coordinator: The coordinator for this sensor
            description: The sensor description
        """
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
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.coordinator.data:
            return {}

        return {
            "route_number": self.coordinator.route_number,
        } 