/* Copyright 2026
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "eeprom_validation.h"

enum
{
	BATTERY_CALIBRATION_MIN = 500U,
	BATTERY_CALIBRATION_MAX = 3000U,
	RSSI_CALIBRATION_MAX = 511U,
	RSSI_CALIBRATION_DISABLED = 512U,
	PA_CALIBRATION_MAX = 200U,
	OUTPUT_POWER_HIGH = 2U,
};

static const uint16_t BatteryCalibrationFallback[EEPROM_BATTERY_CALIBRATION_COUNT] = {
    1258U,
    1747U,
    1876U,
    1901U,
    2004U,
    2300U,
};

uint8_t EEPROM_ValidateU8(uint8_t Value, uint8_t UpperExclusive, uint8_t Fallback)
{
	return (Value < UpperExclusive) ? Value : Fallback;
}

bool EEPROM_ValidateBool(uint8_t Value, bool Fallback)
{
	return (Value < 2U) ? (Value != 0U) : Fallback;
}

uint8_t EEPROM_ValidateChannel(uint8_t Value, uint8_t First, uint8_t Last, uint8_t Fallback)
{
	return (First <= Last && Value >= First && Value <= Last) ? Value : Fallback;
}

uint8_t EEPROM_ValidateOutputPower(uint8_t Value)
{
	return (Value <= OUTPUT_POWER_HIGH) ? Value : OUTPUT_POWER_HIGH;
}

bool EEPROM_ValidateBatteryCalibration(uint16_t Values[EEPROM_BATTERY_CALIBRATION_COUNT])
{
	uint8_t i;

	for (i = 0U; i < EEPROM_BATTERY_CALIBRATION_COUNT; i++) {
		if (Values[i] < BATTERY_CALIBRATION_MIN || Values[i] > BATTERY_CALIBRATION_MAX ||
		    (i > 0U && Values[i] <= Values[i - 1U])) {
			for (i = 0U; i < EEPROM_BATTERY_CALIBRATION_COUNT; i++) {
				Values[i] = BatteryCalibrationFallback[i];
			}
			return false;
		}
	}

	return true;
}

bool EEPROM_ValidateRssiCalibration(uint16_t Values[EEPROM_RSSI_CALIBRATION_COUNT])
{
	uint8_t i;

	for (i = 0U; i < EEPROM_RSSI_CALIBRATION_COUNT; i++) {
		if (Values[i] > RSSI_CALIBRATION_MAX || (i > 0U && Values[i] <= Values[i - 1U])) {
			for (i = 0U; i < EEPROM_RSSI_CALIBRATION_COUNT; i++) {
				Values[i] = RSSI_CALIBRATION_DISABLED;
			}
			return false;
		}
	}

	return true;
}

bool EEPROM_ValidatePaCalibration(uint8_t Values[EEPROM_PA_CALIBRATION_COUNT])
{
	uint8_t i;

	for (i = 0U; i < EEPROM_PA_CALIBRATION_COUNT; i++) {
		if (Values[i] == 0U || Values[i] > PA_CALIBRATION_MAX) {
			for (i = 0U; i < EEPROM_PA_CALIBRATION_COUNT; i++) {
				Values[i] = 0U;
			}
			return false;
		}
	}

	return true;
}
