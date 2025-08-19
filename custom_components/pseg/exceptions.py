"""Exceptions for the PSEG integration."""

from homeassistant.exceptions import HomeAssistantError


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class PSEGLIError(HomeAssistantError):
    """Base exception for PSEG integration.""" 
