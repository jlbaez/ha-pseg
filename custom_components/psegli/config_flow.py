"""Config flow for PSEG Long Island integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.yaml import load_yaml

from .const import DOMAIN, CONF_COOKIE, CONF_COOKIE_SECRET
from .psegli import PSEGLIClient

_LOGGER = logging.getLogger(__name__)


class PSEGLIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PSEG Long Island."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                cookie = user_input["cookie"]
                
                # If user entered a secret reference, load it from secrets.yaml
                if cookie.startswith("!secret "):
                    secret_name = cookie.replace("!secret ", "")
                    secrets = await self.hass.async_add_executor_job(
                        load_yaml, self.hass.config.path("secrets.yaml")
                    )
                    if secrets and secret_name in secrets:
                        cookie = secrets[secret_name]
                    else:
                        errors["base"] = "secret_not_found"
                        return self.async_show_form(
                            step_id="user",
                            data_schema=self._get_schema(),
                            errors=errors,
                        )
                
                # Validate the cookie by making a test request
                client = PSEGLIClient(cookie)
                await self.hass.async_add_executor_job(client.test_connection)

                # Create the config entry
                return self.async_create_entry(
                    title="PSEG Long Island",
                    data={
                        CONF_COOKIE: cookie,
                    },
                )

            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(),
            errors=errors,
        )

    def _get_schema(self):
        """Return the schema for the config flow."""
        return vol.Schema(
            {
                vol.Required(
                    "cookie",
                    description="Enter your PSEG cookie directly or use !secret psegli_cookie to load from secrets.yaml"
                ): str,
            }
        )


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth.""" 