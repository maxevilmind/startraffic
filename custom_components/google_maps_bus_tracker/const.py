"""Constants for the Google Maps Bus Tracker integration."""

DOMAIN = "google_maps_bus_tracker"

CONF_API_KEY = "api_key"
CONF_ORIGIN = "origin"
CONF_DESTINATION = "destination"
CONF_ROUTE_NUMBER = "route_number"

# API endpoints
DIRECTIONS_API_URL = "https://maps.googleapis.com/maps/api/directions/json"

# Update interval in seconds
DEFAULT_SCAN_INTERVAL = 60  # 1 minute 