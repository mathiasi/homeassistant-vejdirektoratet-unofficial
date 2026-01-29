# Vejdirektoratet (Unofficial)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Unofficial Home Assistant integration for [Vejdirektoratet](https://www.vejdirektoratet.dk/) (Danish Road Directorate).

This integration provides winter road salting status for roads near your Home Assistant home location.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/mathiasi/homeassistant-vejdirektoratet-unofficial`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Vejdirektoratet" and install it
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/vejdirektoratet_unofficial` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings > Devices & Services
2. Click "Add Integration"
3. Search for "Vejdirektoratet"
4. Follow the setup wizard

The integration uses your Home Assistant home location to find nearby roads.

## Sensors

This integration provides the following sensors:

| Sensor | Description |
|--------|-------------|
| Winter Roads Overall Status | Best salting status among all nearby roads |
| Winter Roads Total Roads | Total number of roads being monitored |
| Winter Roads Salting Now | Number of roads currently being salted |
| Winter Roads Salted < 12h | Number of roads salted within the last 12 hours |
| Winter Roads Salted 12-48h | Number of roads salted 12-48 hours ago |
| Winter Roads Salted > 48h | Number of roads not salted in the last 48 hours |
| Winter Roads Unknown Status | Number of roads with unknown salting status |

### Status Values

- **Salting Now** - Road is currently being salted
- **Salted < 12h ago** - Road was salted within the last 12 hours
- **Salted 12-48h ago** - Road was salted between 12 and 48 hours ago
- **Salted > 48h ago** - Road has not been salted in the last 48 hours
- **Unknown** - Salting status is unknown

## Data Source

Data is fetched from Vejdirektoratet's public traffic information service and updated every 30 minutes.

## License

This project is licensed under the MIT License.

## Disclaimer

This is an unofficial integration and is not affiliated with Vejdirektoratet.
