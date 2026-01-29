"""Sensor platform for Vejdirektoratet integration."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SaltingStatus
from .const import DOMAIN
from .coordinator import VejdirektoratetCoordinator


STATUS_ICONS = {
    SaltingStatus.SALTING_NOW: "mdi:snowflake-alert",
    SaltingStatus.LESS_THAN_12H: "mdi:snowflake-check",
    SaltingStatus.BETWEEN_12H_48H: "mdi:snowflake",
    SaltingStatus.MORE_THAN_48H: "mdi:snowflake-off",
    SaltingStatus.UNKNOWN: "mdi:help-circle-outline",
}

STATUS_DESCRIPTIONS = {
    SaltingStatus.SALTING_NOW: "Salting Now",
    SaltingStatus.LESS_THAN_12H: "Salted < 12h ago",
    SaltingStatus.BETWEEN_12H_48H: "Salted 12-48h ago",
    SaltingStatus.MORE_THAN_48H: "Salted > 48h ago",
    SaltingStatus.UNKNOWN: "Unknown",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vejdirektoratet sensors from a config entry."""
    coordinator: VejdirektoratetCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VejdirektoratetOverallSensor(coordinator, entry),
        VejdirektoratetTotalSensor(coordinator, entry),
        VejdirektoratetSaltingNowSensor(coordinator, entry),
        VejdirektoratetLessThan12hSensor(coordinator, entry),
        VejdirektoratetBetween12h48hSensor(coordinator, entry),
        VejdirektoratetMoreThan48hSensor(coordinator, entry),
        VejdirektoratetUnknownSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class VejdirektoratetBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Vejdirektoratet sensors."""

    def __init__(
        self,
        coordinator: VejdirektoratetCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
        name_suffix: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_name = f"Winter Roads {name_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Vejdirektoratet (Unofficial)",
            "manufacturer": "Vejdirektoratet",
            "model": "Winter Road Status",
        }


class VejdirektoratetOverallSensor(VejdirektoratetBaseSensor):
    """Sensor showing overall road status."""

    def __init__(self, coordinator: VejdirektoratetCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, "overall", "Overall Status")

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        status = self.coordinator.data.get("overall_status", SaltingStatus.UNKNOWN)
        return STATUS_DESCRIPTIONS.get(status, "Unknown")

    @property
    def icon(self) -> str:
        """Return the icon based on status."""
        if self.coordinator.data is None:
            return "mdi:snowflake-variant"
        status = self.coordinator.data.get("overall_status", SaltingStatus.UNKNOWN)
        return STATUS_ICONS.get(status, "mdi:snowflake-variant")

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return {}
        status = self.coordinator.data.get("overall_status", SaltingStatus.UNKNOWN)
        return {
            "status_code": status.value,
            "total_roads": self.coordinator.data.get("total_roads", 0),
        }


class VejdirektoratetTotalSensor(VejdirektoratetBaseSensor):
    """Sensor showing total number of roads."""

    def __init__(self, coordinator: VejdirektoratetCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, "total", "Total Roads")
        self._attr_native_unit_of_measurement = "roads"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("total_roads", 0)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:road"


class VejdirektoratetCountSensor(VejdirektoratetBaseSensor):
    """Base class for count sensors."""

    _status: SaltingStatus

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        counts = self.coordinator.data.get("status_counts", {})
        return counts.get(self._status, 0)

    @property
    def icon(self) -> str:
        """Return the icon based on status."""
        return STATUS_ICONS.get(self._status, "mdi:snowflake-variant")

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "roads"


class VejdirektoratetSaltingNowSensor(VejdirektoratetCountSensor):
    """Sensor showing roads being salted now."""

    _status = SaltingStatus.SALTING_NOW

    def __init__(self, coordinator: VejdirektoratetCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, "salting_now", "Salting Now")


class VejdirektoratetLessThan12hSensor(VejdirektoratetCountSensor):
    """Sensor showing roads salted less than 12h ago."""

    _status = SaltingStatus.LESS_THAN_12H

    def __init__(self, coordinator: VejdirektoratetCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, "less_than_12h", "Salted < 12h")


class VejdirektoratetBetween12h48hSensor(VejdirektoratetCountSensor):
    """Sensor showing roads salted between 12h and 48h ago."""

    _status = SaltingStatus.BETWEEN_12H_48H

    def __init__(self, coordinator: VejdirektoratetCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, "between_12h_48h", "Salted 12-48h")


class VejdirektoratetMoreThan48hSensor(VejdirektoratetCountSensor):
    """Sensor showing roads salted more than 48h ago."""

    _status = SaltingStatus.MORE_THAN_48H

    def __init__(self, coordinator: VejdirektoratetCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, "more_than_48h", "Salted > 48h")


class VejdirektoratetUnknownSensor(VejdirektoratetCountSensor):
    """Sensor showing roads with unknown salting status."""

    _status = SaltingStatus.UNKNOWN

    def __init__(self, coordinator: VejdirektoratetCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, "unknown", "Unknown Status")
