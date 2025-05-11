# Google Maps Bus Tracker

This Home Assistant integration provides real-time bus arrival information using the Google Maps API. Perfect for commuters, travelers, and anyone who needs to track public transportation schedules.

## Features

- Real-time bus arrival times
- Support for specific bus routes and stops
- Automatic updates every 5 minutes
- Detailed information including bus number and destination
- Easy configuration through Home Assistant UI
- Reliable Google Maps API integration

## Installation

### HACS Installation (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Add this repository to HACS:
   - Go to HACS > Integrations
   - Click the three dots in the top right
   - Click "Custom repositories"
   - Add `https://github.com/maxevilmind/startraffic`
   - Select "Integration" as the category
3. Click "Download" on the integration
4. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `google_maps_bus_tracker` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to Configuration > Integrations
2. Click the "+ Add Integration" button
3. Search for "Google Maps Bus Tracker"
4. Enter your Google Maps API key and bus stop information

### Setting Up Google Maps API Key

#### 1. Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "New Project"
4. Enter a name for your project
5. Click "Create"

#### 2. Enable Required APIs
1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for and enable these APIs one by one:
   - **Directions API**
     - Search for "Directions API"
     - Click "Enable"
   - **Geocoding API**
     - Search for "Geocoding API"
     - Click "Enable"
   - **Maps JavaScript API**
     - Search for "Maps JavaScript API"
     - Click "Enable"
   - **Places API**
     - Search for "Places API"
     - Click "Enable"
   - **Distance Matrix API**
     - Search for "Distance Matrix API"
     - Click "Enable"

#### 3. Set Up Billing
1. Go to "Billing" in the Google Cloud Console
2. Click "Link a billing account"
3. Follow the steps to set up billing
   - Note: Google provides $300 free credit for new accounts
   - The APIs used in this integration are part of the free tier

#### 4. Create API Key
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy the generated API key immediately
   - You won't be able to see it again, but you can create a new one if needed

#### 5. Restrict API Key (Recommended)
1. Click on the created API key
2. Under "Application restrictions":
   - Choose "HTTP referrers"
   - Add your Home Assistant URL (e.g., `https://your-ha-instance.com/*`)
3. Under "API restrictions":
   - Choose "Restrict key"
   - Select these APIs:
     - Directions API
     - Geocoding API
     - Maps JavaScript API
     - Places API
     - Distance Matrix API
4. Click "Save"

#### 6. Verify API Key
1. Wait 5-10 minutes for the API key to become active
2. Test the key in the Google Cloud Console:
   - Go to "APIs & Services" > "Dashboard"
   - Look for any error messages
   - Check the "Quotas" page to ensure APIs are enabled

### Required Information

- **Google Maps API Key**: The key you created in the steps above
- **Stop Location**: The address or coordinates of your bus stop
- **Route Number**: The bus route number you want to track

## Finding Your Bus Stop Information

To find your bus stop information:

1. Go to Google Maps
2. Search for your bus stop location
3. Right-click on the exact location of your bus stop
4. The coordinates will appear at the top of the context menu
5. Use these coordinates in the format: `latitude,longitude`

For example, if the coordinates are 51.5074° N, 0.1278° W, you would enter: `51.5074,-0.1278`

### Tips for Finding Bus Stops

- You can also use the bus stop's address if you know it
- For more accuracy, use the coordinates
- Make sure to select the correct direction of travel
- You can verify the stop by checking the bus route information in Google Maps

## Use Cases

- Track your daily commute bus
- Monitor multiple bus routes
- Get real-time arrival updates
- Plan your journey with accurate timing
- Create automations based on bus arrival times

## Notes

- The integration updates every 5 minutes by default
- Make sure your Google Maps API key has all required APIs enabled
- The API key should have appropriate restrictions set up in the Google Cloud Console

## Troubleshooting

If you get an "Invalid API Key" error:
1. Verify that all required APIs are enabled:
   - Directions API
   - Geocoding API
   - Maps JavaScript API
   - Places API
   - Distance Matrix API
2. Check that your API key restrictions are properly configured
3. Wait 5-10 minutes after creating the key
4. Verify billing is enabled for your project
5. Check the Google Cloud Console for any error messages
6. Make sure you're using the correct API key (not the client ID or other credentials)

Common Issues:
- "API not enabled": Make sure all required APIs are enabled
- "Billing not enabled": Set up billing for your project
- "Invalid API key": Wait 5-10 minutes after creating the key
- "Quota exceeded": Check your usage in the Google Cloud Console

## Support

If you encounter any issues or have questions, please open an issue on the [GitHub repository](https://github.com/maxevilmind/startraffic/issues).

## Contributing

Contributions are welcome! Feel free to submit issues, fork the repository, and create pull requests for any improvements. 