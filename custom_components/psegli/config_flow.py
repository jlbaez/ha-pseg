"""Config flow for PSEG Long Island integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.yaml import load_yaml

from .const import DOMAIN, CONF_COOKIE, CONF_COOKIE_SECRET
from .psegli import PSEGLIClient
from .exceptions import InvalidAuth

_LOGGER = logging.getLogger(__name__)


class PSEGLIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PSEG Long Island."""

    VERSION = 1
    has_options = True

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return PSEGLIOptionsFlow(config_entry)

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


class PSEGLIOptionsFlow(config_entries.OptionsFlow):
    """PSEG Long Island options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Manage the options for PSEG Long Island."""
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
                            step_id="init",
                            data_schema=self._get_options_schema(),
                            errors=errors,
                        )
                
                # Validate the cookie by making a test request
                client = PSEGLIClient(cookie)
                await self.hass.async_add_executor_job(client.test_connection)

                # Update the config entry data
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, CONF_COOKIE: cookie},
                )
                
                # Clear any persistent notification about expired cookies
                await self.hass.services.async_call(
                    "persistent_notification",
                    "dismiss",
                    {"notification_id": "psegli_auth_failed"},
                )

                return self.async_create_entry(title="", data={})

            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during reconfigure")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
            errors=errors,
            description_placeholders={
                "current_cookie": self.config_entry.data.get(CONF_COOKIE, "")[:50] + "..." if self.config_entry.data.get(CONF_COOKIE) else "None"
            },
        )

    def _get_options_schema(self):
        """Return the schema for the options flow."""
        return vol.Schema(
            {
                vol.Required(
                    "cookie",
                    description=(
                        "To get a new cookie:\n"
                        "1. Open Chrome/Firefox Developer Tools (F12)\n"
                        "2. Go to Network tab\n"
                        "3. Visit https://mysmartenergy.psegliny.com\n"
                        "4. Log in to your account\n"
                        "5. Find any request to mysmartenergy.psegliny.com\n"
                        "6. Copy the Cookie header value\n"
                        "Or use !secret psegli_cookie to load from secrets.yaml"
                    ),
                    default=self.config_entry.data.get(CONF_COOKIE, "")
                ): str,
            }
        )


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth.""" 