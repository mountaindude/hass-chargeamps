"""Light platform for Chargeamps."""

import logging

from homeassistant.components.light import SUPPORT_BRIGHTNESS, LightEntity

from . import ChargeampsEntity
from .const import DOMAIN_DATA

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Setup light platform."""
    lights = []
    handler = hass.data[DOMAIN_DATA]["handler"]
    for cp_id in handler.charge_point_ids:
        cp_info = handler.get_chargepoint_info(cp_id)
        cp_settings = handler.get_chargepoint_settings(cp_id)
        _LOGGER.warning("%s", cp_settings)
        for _type in ("dimmer", "downlight"):
            lights.append(
                ChargeampsLight(hass, f"{cp_info.name}_{cp_id}_{_type}", cp_id, _type)
            )
            _LOGGER.info(
                "Adding chargepoint %s light %s",
                cp_id,
                _type,
            )
    async_add_entities(lights, True)


class ChargeampsLight(LightEntity, ChargeampsEntity):
    """Chargeamps Light class."""

    def __init__(self, hass, name, charge_point_id, light_type):
        super().__init__(hass, name, charge_point_id, light_type)
        self._light_type = light_type
        self._supported_features = 0
        if light_type == "dimmer":
            self._supported_features |= SUPPORT_BRIGHTNESS

    @property
    def supported_features(self):
        """Return supported features."""
        return self._supported_features

    @property
    def is_on(self):
        settings = self.handler.get_chargepoint_settings(self.charge_point_id)
        if self._light_type == "downlight":
            status = settings.down_light
        elif self._light_type == "dimmer":
            status = settings.dimmer
        else:
            return None
        return status not in (False, "Off")

    async def async_turn_on(self, brightness=None):
        if brightness:
            if brightness < 128:
                brightness = "low"
            elif brightness < 192:
                brightness = "medium"
            else:
                brightness = "high"
        else:
            brightness = True if self._light_type == "downlight" else "high"
        await self.handler.async_set_light(
            {"chargepoint": self.charge_point_id, self._light_type: brightness}
        )

    async def async_turn_off(self):

        await self.handler.async_set_light(
            {
                "chargepoint": self.charge_point_id,
                self._light_type: False if self._light_type == "downlight" else "off",
            }
        )

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        brightness = {"Off": 0, "Low": 85, "Medium": 170, "High": 255}
        return brightness.get(
            self.handler.get_chargepoint_settings(self.charge_point_id).dimmer
        )