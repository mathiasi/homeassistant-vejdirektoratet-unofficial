"""Config flow for Vejdirektoratet integration."""

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE

from .const import DOMAIN


class VejdirektoratetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Vejdirektoratet."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # Only allow one instance
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            # Use home location from Home Assistant
            lat = self.hass.config.latitude
            lon = self.hass.config.longitude

            return self.async_create_entry(
                title="Vejdirektoratet (Unofficial)",
                data={
                    CONF_LATITUDE: lat,
                    CONF_LONGITUDE: lon,
                },
            )

        # Show confirmation form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "latitude": f"{self.hass.config.latitude:.4f}",
                "longitude": f"{self.hass.config.longitude:.4f}",
            },
        )
