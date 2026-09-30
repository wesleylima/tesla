"""Tests for the Tesla services."""

from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
import pytest
import voluptuous as vol

from custom_components.tesla_custom.const import (
    ATTR_DRIVING_INTERVAL,
    ATTR_VIN,
    DOMAIN,
    SERVICE_DRIVING_INTERVAL,
    SERVICE_SCAN_INTERVAL,
)

from .common import setup_platform
from .mock_data import car as car_mock_data


async def _call_driving_interval(hass: HomeAssistant, data: dict) -> dict:
    """Call the driving_interval service and return its response."""
    return await hass.services.async_call(
        DOMAIN,
        SERVICE_DRIVING_INTERVAL,
        data,
        blocking=True,
        return_response=True,
    )


async def test_driving_interval_for_vin(hass: HomeAssistant) -> None:
    """A VIN-scoped call sets that car's driving interval only."""
    _, mock_controller = await setup_platform(hass, "sensor")
    controller = mock_controller.return_value

    response = await _call_driving_interval(
        hass, {ATTR_VIN: car_mock_data.VIN, ATTR_DRIVING_INTERVAL: 15}
    )

    controller.set_driving_interval_vin.assert_called_once_with(
        vin=car_mock_data.VIN, value=15
    )
    assert response["result"] is True


async def test_driving_interval_default(hass: HomeAssistant) -> None:
    """A call without a VIN sets the controller-wide default driving interval."""
    _, mock_controller = await setup_platform(hass, "sensor")
    controller = mock_controller.return_value

    await _call_driving_interval(hass, {ATTR_DRIVING_INTERVAL: 15})

    assert controller.driving_interval == 15
    controller.set_driving_interval_vin.assert_not_called()


async def test_driving_interval_reset_for_vin(hass: HomeAssistant) -> None:
    """-1 is passed through so the controller drops the VIN override."""
    _, mock_controller = await setup_platform(hass, "sensor")
    controller = mock_controller.return_value

    await _call_driving_interval(
        hass, {ATTR_VIN: car_mock_data.VIN, ATTR_DRIVING_INTERVAL: -1}
    )

    controller.set_driving_interval_vin.assert_called_once_with(
        vin=car_mock_data.VIN, value=-1
    )


@pytest.mark.parametrize("interval", [0, -2, 3601])
async def test_driving_interval_rejects_invalid(
    hass: HomeAssistant, interval: int
) -> None:
    """0 (silently ignored by the controller) and out-of-range values are rejected."""
    await setup_platform(hass, "sensor")

    with pytest.raises(vol.Invalid):
        await _call_driving_interval(hass, {ATTR_DRIVING_INTERVAL: interval})


async def test_polling_interval_for_vin(hass: HomeAssistant) -> None:
    """The existing polling_interval service still resolves the controller."""
    _, mock_controller = await setup_platform(hass, "sensor")
    controller = mock_controller.return_value
    controller.get_update_interval_vin.return_value = 660

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SCAN_INTERVAL,
        {ATTR_VIN: car_mock_data.VIN, CONF_SCAN_INTERVAL: 120},
        blocking=True,
        return_response=True,
    )

    controller.set_update_interval_vin.assert_called_once_with(
        vin=car_mock_data.VIN, value=120
    )
