"""Config flow for homee integration."""
import asyncio
import logging

from pymee import (
    AuthenticationFailedException as HomeeAuthenticationFailedException,
    Homee,
)
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.components import zeroconf
from homeassistant.components.zeroconf import ATTR_HOST
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
DATA_SCHEMA = vol.Schema({CONF_HOST: str, CONF_USERNAME: str, CONF_PASSWORD: str})
DISCOVERED_SCHEMA = vol.Schema({CONF_USERNAME: str, CONF_PASSWORD: str})


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


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for homee."""

    VERSION = 1
    # TODO pick one of the available connection classes in homeassistant/config_entries.py
    # CONNECTION_CLASS = config_entries.CONN_CLASS_UNKNOWN
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovered_host = None

    async def async_step_user(self, user_input=None):
        """Handle the initial user step."""
        errors = {}
        if user_input is not None:
            if self.discovered_host is not None:
                user_input[ATTR_HOST] = self.discovered_host

            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(
                    title=info["title"],
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

        schema = DATA_SCHEMA if self.discovered_host is None else DISCOVERED_SCHEMA

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_zeroconf(self, discovery_info=None):
        """Handle the initial step."""
        await self.async_set_unique_id(discovery_info.get(zeroconf.ATTR_NAME))
        self.discovered_host = discovery_info.get(zeroconf.ATTR_HOST)
        return await self.async_step_user()


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
