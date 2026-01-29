"""Constants for the Vejdirektoratet integration."""

DOMAIN = "vejdirektoratet_unofficial"

# API URLs
WINTER_STATUS_URL = "https://storage.googleapis.com/trafikkort-data-tiles/winter.json"
METADATA_URL = "https://storage.googleapis.com/trafikkort-data-tiles/winter-network-metadata.json"
TILE_URL_PATTERN = "https://tiles.trafikinfo.net/winter-network/v{version}/{z}/{x}/{y}.pbf"

# Tile grid parameters (EPSG:25832 / UTM zone 32N)
TILE_GRID_ORIGIN_X = 120000
TILE_GRID_ORIGIN_Y = 6500000
TILE_GRID_EXTENT_WIDTH = 1258291.2

# Default values
DEFAULT_ZOOM = 12
DEFAULT_SCAN_INTERVAL = 1800  # 30 minutes

# Valid road classes (from Vejdirektoratet JS - roads with other classes are not displayed)
VALID_ROAD_CLASSES = {11, 21, 22, 23, 24, 31, 32, 33, 34}
