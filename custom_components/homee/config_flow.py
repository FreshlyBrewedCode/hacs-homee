"""Config flow for homee integration."""
import asyncio
import logging

from homeassistant import config_entries, core, exceptions
from homeassistant.components import zeroconf
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback

# import homeassistant.helpers.config_validation as cv
from pymee import (
    AuthenticationFailedException as HomeeAuthenticationFailedException,
    Homee,
)
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = schema = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect."""

    # TODO DATA SCHEMA validation

    # Create a Homee object and try to receive an access token.
    # This tells us if the host is reachable and if the credentials work
    homee = Homee(data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD])

    try:
        await homee.get_access_token()
    except HomeeAuthenticationFailedException:
        raise InvalidAuth
    except asyncio.TimeoutError:
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {"title": "homee", "description": f"homee cube at {data[CONF_HOST]}"}


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for homee."""

    VERSION = 1
    # TODO pick one of the available connection classes in homeassistant/config_entries.py
    # CONNECTION_CLASS = config_entries.CONN_CLASS_UNKNOWN
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.homee_host: str = None
        self.homee_id: str = None

    async def async_step_user(self, user_input=None):
        """Handle the initial user step."""
        errors = {}
        if user_input is not None:

            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(
                    title=info["description"],
                    description=info["description"],
                    data=user_input,
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_zeroconf(self, discovery_info=None):
        """Handle the zerconf discovery."""

        # Get the homee id from the discovery info
        self.homee_id = discovery_info.get(zeroconf.ATTR_NAME)
        # homee-<HOMEE ID>._sftp-ssh._tcp.local.
        self.homee_id = self.homee_id.split("-")[1].split(".")[0]

        # Get the host (ip address) from the discovery info
        self.homee_host = discovery_info.get(zeroconf.ATTR_HOST)

        # Update the title of the discovered device
        # pylint: disable=no-member # https://github.com/PyCQA/pylint/issues/3167
        self.context.update(
            {"title_placeholders": {"host": self.homee_host, "name": self.homee_id}}
        )

        await self.async_set_unique_id(self.homee_id)
        self._abort_if_unique_id_configured()

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input=None):
        """Handle the zeroconf confirm step."""
        errors = {}
        if user_input is not None:

            try:
                await validate_input(self.hass, user_input)
                user_input["homee_id"] = self.homee_id

                return self.async_create_entry(
                    title=f"{self.homee_id} ({self.homee_host})",
                    data=user_input,
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        schema = DATA_SCHEMA.extend(
            {
                vol.Required(CONF_HOST, default=self.homee_host): str,
            }
        )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={"id": self.homee_id, "host": self.homee_host},
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        OPT_CLASS_FROM_ICONS,
                        default=self.entry.options.get(OPT_CLASS_FROM_ICONS, True),
                    ): bool
                }
            ),
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
