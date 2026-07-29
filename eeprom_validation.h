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

#ifndef EEPROM_VALIDATION_H
#define EEPROM_VALIDATION_H

#include <stdbool.h>
#include <stdint.h>

enum {
	EEPROM_BATTERY_CALIBRATION_COUNT = 6U,
	EEPROM_RSSI_CALIBRATION_COUNT = 4U,
	EEPROM_PA_CALIBRATION_COUNT = 3U,
	EEPROM_PRIORITY_CHANNEL_DISABLED = 0xFFU,
};

uint8_t EEPROM_ValidateU8(uint8_t Value, uint8_t UpperExclusive, uint8_t Fallback);
bool EEPROM_ValidateBool(uint8_t Value, bool Fallback);
uint8_t EEPROM_ValidateChannel(uint8_t Value, uint8_t First, uint8_t Last, uint8_t Fallback);
uint8_t EEPROM_ValidateOutputPower(uint8_t Value);

bool EEPROM_ValidateBatteryCalibration(uint16_t Values[EEPROM_BATTERY_CALIBRATION_COUNT]);
bool EEPROM_ValidateRssiCalibration(uint16_t Values[EEPROM_RSSI_CALIBRATION_COUNT]);
bool EEPROM_ValidatePaCalibration(uint8_t Values[EEPROM_PA_CALIBRATION_COUNT]);

#endif
