"""API client for Vejdirektoratet winter roads."""

import logging
import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import aiohttp

from .const import (
    WINTER_STATUS_URL,
    METADATA_URL,
    TILE_URL_PATTERN,
    TILE_GRID_ORIGIN_X,
    TILE_GRID_ORIGIN_Y,
    TILE_GRID_EXTENT_WIDTH,
    VALID_ROAD_CLASSES,
)

_LOGGER = logging.getLogger(__name__)


class SaltingStatus(Enum):
    """Road salting status based on time since last salting."""

    SALTING_NOW = "salting_now"
    LESS_THAN_12H = "less_than_12h"
    BETWEEN_12H_48H = "between_12h_48h"
    MORE_THAN_48H = "more_than_48h"
    UNKNOWN = "unknown"


@dataclass
class RoadSegment:
    """A road segment with its salting status."""

    feature_id: str
    road_class: int
    salting_time: datetime | None
    salting_now: bool
    condition: int
    service_level: int
    status: SaltingStatus


def lat_lon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """Convert latitude/longitude to tile coordinates."""
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
    utm_x, utm_y = transformer.transform(lon, lat)

    tile_size = TILE_GRID_EXTENT_WIDTH / (2**zoom)
    tile_x = math.floor((utm_x - TILE_GRID_ORIGIN_X) / tile_size)
    tile_y = math.floor((TILE_GRID_ORIGIN_Y - utm_y) / tile_size)

    return tile_x, tile_y


def get_neighboring_tiles(
    lat: float, lon: float, zoom: int, radius: int = 1
) -> list[tuple[int, int]]:
    """Get tile coordinates for a location and its neighbors."""
    center_x, center_y = lat_lon_to_tile(lat, lon, zoom)
    tiles = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            tiles.append((center_x + dx, center_y + dy))
    return tiles


def get_salting_status(salting_time_epoch: int, salting_now: bool) -> SaltingStatus:
    """Determine road status based on salting time."""
    if salting_now:
        return SaltingStatus.SALTING_NOW

    if salting_time_epoch <= 0:
        return SaltingStatus.UNKNOWN

    now = datetime.now()
    salting_time = datetime.fromtimestamp(salting_time_epoch)
    hours_ago = (now - salting_time).total_seconds() / 3600

    # Handle future timestamps (treat as > 48h)
    if hours_ago < 0:
        return SaltingStatus.MORE_THAN_48H
    elif hours_ago < 12:
        return SaltingStatus.LESS_THAN_12H
    elif hours_ago < 48:
        return SaltingStatus.BETWEEN_12H_48H
    else:
        return SaltingStatus.MORE_THAN_48H


class VejdirektoratetAPI:
    """API client for fetching winter road status."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._session = session
        self._tile_version: int | None = None

    async def fetch_winter_status(self) -> dict[str, RoadSegment]:
        """Fetch and parse the winter road status data."""
        async with self._session.get(WINTER_STATUS_URL) as response:
            response.raise_for_status()
            raw_data = await response.json()

        segments = {}
        for feature_id, values in raw_data.items():
            road_class, salting_epoch, salting_now, condition, service_level = values
            segments[feature_id] = RoadSegment(
                feature_id=feature_id,
                road_class=road_class,
                salting_time=(
                    datetime.fromtimestamp(salting_epoch) if salting_epoch > 0 else None
                ),
                salting_now=salting_now,
                condition=condition,
                service_level=service_level,
                status=get_salting_status(salting_epoch, salting_now),
            )
        return segments

    async def fetch_tile_version(self) -> int:
        """Fetch the current tile version from metadata."""
        async with self._session.get(METADATA_URL) as response:
            response.raise_for_status()
            data = await response.json()
            if "version" not in data:
                raise ValueError("Missing 'version' in tile metadata")
            self._tile_version = data["version"]
            return self._tile_version

    async def fetch_tile_features(
        self, zoom: int, x: int, y: int
    ) -> list[str]:
        """Fetch feature IDs from a tile using our custom MVT decoder."""
        from .mvt_decoder import extract_feature_ids

        if self._tile_version is None:
            await self.fetch_tile_version()

        url = TILE_URL_PATTERN.format(version=self._tile_version, z=zoom, x=x, y=y)

        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                content = await response.read()

            return extract_feature_ids(content)

        except Exception as err:
            _LOGGER.warning("Failed to fetch tile %s/%s/%s: %s", zoom, x, y, err)
            return []

    async def get_roads_near_location(
        self, lat: float, lon: float, zoom: int = 12
    ) -> dict[str, RoadSegment]:
        """Get all road segments near a location (3x3 tile grid)."""
        # Fetch status data
        all_segments = await self.fetch_winter_status()

        # Get tiles around the location
        tiles = get_neighboring_tiles(lat, lon, zoom, radius=1)

        # Fetch features from all tiles
        nearby_feature_ids = set()
        for tile_x, tile_y in tiles:
            feature_ids = await self.fetch_tile_features(zoom, tile_x, tile_y)
            nearby_feature_ids.update(feature_ids)

        if nearby_feature_ids:
            # Filter segments to only those in the nearby tiles with valid road classes
            result = {
                fid: segment
                for fid, segment in all_segments.items()
                if fid in nearby_feature_ids
                and segment.road_class in VALID_ROAD_CLASSES
            }
            _LOGGER.info(
                "Found %d roads in 3x3 grid around (%.4f, %.4f)",
                len(result), lat, lon
            )
            return result

        _LOGGER.warning("No roads found in tiles, returning empty")
        return {}
