"""Support for Sonicare sensors."""
from __future__ import annotations

from sonicare_ble import SonicareSensor, SensorUpdate

from homeassistant import config_entries
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothProcessorCoordinator,
    PassiveBluetoothProcessorEntity,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.sensor import sensor_device_info_to_hass_device_info

from .const import DOMAIN
from .device import device_key_to_bluetooth_entity_key

SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    SonicareSensor.BRUSHING_TIME: SensorEntityDescription(
        key=SonicareSensor.BRUSHING_TIME,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    SonicareSensor.CURRENT_TIME: SensorEntityDescription(
        key=SonicareSensor.CURRENT_TIME
    ),
    SonicareSensor.TOOTHBRUSH_STATE: SensorEntityDescription(
        key=SonicareSensor.TOOTHBRUSH_STATE
    ),
    SonicareSensor.SIGNAL_STRENGTH: SensorEntityDescription(
        key=SonicareSensor.SIGNAL_STRENGTH,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
    ),
    SonicareSensor.BATTERY_PERCENT: SensorEntityDescription(
        key=SonicareSensor.BATTERY_PERCENT,
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SonicareSensor.BRUSH_HEAD_LIFETIME: SensorEntityDescription(
        key=SonicareSensor.BRUSH_HEAD_LIFETIME,
    ),
    SonicareSensor.BRUSH_HEAD_USAGE: SensorEntityDescription(
        key=SonicareSensor.BRUSH_HEAD_USAGE,
    ),
    SonicareSensor.MODE: SensorEntityDescription(
        key=SonicareSensor.MODE
    ),
    SonicareSensor.BRUSH_STRENGTH: SensorEntityDescription(
        key=SonicareSensor.BRUSH_STRENGTH
    ),
    SonicareSensor.BRUSH_SERIAL_NUMBER: SensorEntityDescription(
        key=SonicareSensor.BRUSH_SERIAL_NUMBER
    ),
    SonicareSensor.BRUSH_LIFETIME_PERCENTAGE: SensorEntityDescription(
        key=SonicareSensor.BRUSH_LIFETIME_PERCENTAGE
    ),
    SonicareSensor.BRUSH_SESSION_ID: SensorEntityDescription(
        key=SonicareSensor.BRUSH_SESSION_ID
    )
}


def sensor_update_to_bluetooth_data_update(
    sensor_update: SensorUpdate,
) -> PassiveBluetoothDataUpdate:
    """Convert a sensor update to a bluetooth data update."""
    return PassiveBluetoothDataUpdate(
        devices={
            device_id: sensor_device_info_to_hass_device_info(device_info)
            for device_id, device_info in sensor_update.devices.items()
        },
        entity_descriptions={
            device_key_to_bluetooth_entity_key(device_key): SENSOR_DESCRIPTIONS[
                device_key.key
            ]
            for device_key in sensor_update.entity_descriptions
        },
        entity_data={
            device_key_to_bluetooth_entity_key(device_key): sensor_values.native_value
            for device_key, sensor_values in sensor_update.entity_values.items()
        },
        entity_names={
            device_key_to_bluetooth_entity_key(device_key): sensor_values.name
            for device_key, sensor_values in sensor_update.entity_values.items()
        },
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Sonicare BLE sensors."""
    coordinator: PassiveBluetoothProcessorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    processor = PassiveBluetoothDataProcessor(sensor_update_to_bluetooth_data_update)
    entry.async_on_unload(
        processor.async_add_entities_listener(
            SonicareBluetoothSensorEntity, async_add_entities
        )
    )
    entry.async_on_unload(coordinator.async_register_processor(processor))


class SonicareBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[PassiveBluetoothDataProcessor[str | int | None]],
    SensorEntity,
):
    """Representation of a Sonicare sensor."""

    @property
    def native_value(self) -> str | int | None:
        """Return the native value."""
        return self.processor.entity_data.get(self.entity_key)
