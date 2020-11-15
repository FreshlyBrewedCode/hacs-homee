"""Config flow for homee integration."""
import asyncio
import logging

from homeassistant import config_entries, core, exceptions
from homeassistant.components import zeroconf
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow
import homeassistant.helpers.config_validation as cv

# import homeassistant.helpers.config_validation as cv
from pymee import (
    AuthenticationFailedException as HomeeAuthenticationFailedException,
    Homee,
)
import voluptuous as vol

from .const import (
    CONF_ADD_HOME_DATA,
    CONF_DOOR_GROUPS,
    CONF_GROUPS,
    CONF_INITIAL_OPTIONS,
    CONF_WINDOW_GROUPS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = schema = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


def get_options_schema(homee: Homee, default_options={}):
    groups = [str(g.id) for g in homee.groups]
    groups_selection = {str(g.id): f"{g.name} ({len(g.nodes)})" for g in homee.groups}

    return vol.Schema(
        {
            vol.Required(
                CONF_GROUPS,
                default=default_options.get(CONF_GROUPS, groups),
            ): cv.multi_select(groups_selection),
            vol.Required(
                CONF_WINDOW_GROUPS,
                default=default_options.get(CONF_WINDOW_GROUPS, []),
            ): cv.multi_select(groups_selection),
            vol.Required(
                CONF_DOOR_GROUPS,
                default=default_options.get(CONF_DOOR_GROUPS, []),
            ): cv.multi_select(groups_selection),
            vol.Required(
                CONF_ADD_HOME_DATA,
                default=default_options.get(CONF_ADD_HOME_DATA, False),
            ): bool,
        }
    )


async def validate_and_connect(hass: core.HomeAssistant, data) -> Homee:
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

    hass.async_create_task(homee.run())
    await homee.wait_until_connected()
    homee.disconnect()
    await homee.wait_until_disconnected()

    # Return homee instance
    return homee


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
        self.homee: Homee = None

    async def async_step_user(self, user_input=None):
        """Handle the initial user step."""
        errors = {}
        if user_input is not None:

            try:
                self.homee = await validate_and_connect(self.hass, user_input)
                await self.async_set_unique_id(self.homee.settings.uid)
                self._abort_if_unique_id_configured()

                return await self.async_step_config()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except AbortFlow:
                return self.async_abort(reason="already_configured")
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
                self.homee = await validate_and_connect(self.hass, user_input)
                await self.async_set_unique_id(self.homee.settings.uid)
                self._abort_if_unique_id_configured()

                return await self.async_step_config()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except AbortFlow:
                return self.async_abort(reason="already_configured")
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

    async def async_step_config(self, user_input=None):
        """Configure initial options."""

        if user_input is not None:
            return self.async_create_entry(
                title=f"{self.homee.settings.uid} ({self.homee.host})",
                data={
                    CONF_HOST: self.homee.host,
                    CONF_USERNAME: self.homee.user,
                    CONF_PASSWORD: self.homee.password,
                    CONF_INITIAL_OPTIONS: user_input,
                },
            )

        return self.async_show_form(
            step_id="config", data_schema=get_options_schema(self.homee)
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        homee: Homee = self.hass.data[DOMAIN][self.entry.entry_id]

        return self.async_show_form(
            step_id="init", data_schema=get_options_schema(homee, self.entry.options)
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
