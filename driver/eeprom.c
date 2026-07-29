/* Copyright 2023 Dual Tachyon
 * https://github.com/DualTachyon
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 *     Unless required by applicable law or agreed to in writing, software
 *     distributed under the License is distributed on an "AS IS" BASIS,
 *     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *     See the License for the specific language governing permissions and
 *     limitations under the License.
 */

#include <stdbool.h>
#include <string.h>

#include "driver/eeprom.h"
#include "driver/hardware.h"
#include "driver/i2c.h"
#include "driver/system.h"

bool EEPROM_ReadBuffer(uint16_t Address, void *pBuffer, uint8_t Size)
{
	bool Success = false;

	if (Size == 0U) {
		return true;
	}
	memset(pBuffer, 0xFF, Size);
	I2C_Start();

	if (I2C_Write(0xA0) < 0 || I2C_Write((Address >> 8) & 0xFF) < 0 || I2C_Write((Address >> 0) & 0xFF) < 0) {
		goto cleanup;
	}

	I2C_Start();

	if (I2C_Write(0xA1) < 0 || I2C_ReadBuffer(pBuffer, Size) != Size) {
		goto cleanup;
	}
	Success = true;

cleanup:
	I2C_Stop();
	if (!Success) {
		memset(pBuffer, 0xFF, Size);
		HARDWARE_ReportFault(HARDWARE_FAULT_EEPROM);
	}
	return Success;
}

bool EEPROM_WriteBuffer(uint16_t Address, const void *pBuffer)
{
	bool Success = false;

	I2C_Start();

	if (I2C_Write(0xA0) < 0 || I2C_Write((Address >> 8) & 0xFF) < 0 || I2C_Write((Address >> 0) & 0xFF) < 0 || I2C_WriteBuffer(pBuffer, 8) < 0) {
		goto cleanup;
	}
	Success = true;

cleanup:
	I2C_Stop();
	if (Success) {
		SYSTEM_DelayMs(10);
	} else {
		HARDWARE_ReportFault(HARDWARE_FAULT_EEPROM);
	}
	return Success;
}
