"""Data coordinator for Vejdirektoratet."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VejdirektoratetAPI, SaltingStatus
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, DEFAULT_ZOOM

_LOGGER = logging.getLogger(__name__)


class VejdirektoratetCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching winter road data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: VejdirektoratetAPI,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict:
        """Fetch data from the API."""
        _LOGGER.debug("Starting data update")
        try:
            # Always use current home location from Home Assistant
            latitude = self.hass.config.latitude
            longitude = self.hass.config.longitude

            # Get all roads near the home location
            roads = await self.api.get_roads_near_location(
                latitude, longitude, DEFAULT_ZOOM
            )

            # Calculate summary statistics
            status_counts = {status: 0 for status in SaltingStatus}
            for segment in roads.values():
                status_counts[segment.status] += 1

            # Determine overall status (best case)
            if status_counts[SaltingStatus.SALTING_NOW] > 0:
                overall_status = SaltingStatus.SALTING_NOW
            elif status_counts[SaltingStatus.LESS_THAN_12H] > 0:
                overall_status = SaltingStatus.LESS_THAN_12H
            elif status_counts[SaltingStatus.BETWEEN_12H_48H] > 0:
                overall_status = SaltingStatus.BETWEEN_12H_48H
            elif status_counts[SaltingStatus.MORE_THAN_48H] > 0:
                overall_status = SaltingStatus.MORE_THAN_48H
            else:
                overall_status = SaltingStatus.UNKNOWN

            _LOGGER.debug(
                "Updated Vejdirektoratet data: %d roads, overall status: %s",
                len(roads),
                overall_status.value,
            )

            return {
                "roads": roads,
                "status_counts": status_counts,
                "overall_status": overall_status,
                "total_roads": len(roads),
                "latitude": latitude,
                "longitude": longitude,
            }

        except Exception as err:
            _LOGGER.error("Failed to update Vejdirektoratet data: %s", err)
            raise UpdateFailed(f"Error fetching Vejdirektoratet data: {err}") from err
