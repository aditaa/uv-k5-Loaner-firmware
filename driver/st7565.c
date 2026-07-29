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

#include <stdint.h>
#include "bsp/dp32g030/gpio.h"
#include "bsp/dp32g030/spi.h"
#include "driver/gpio.h"
#include "driver/spi.h"
#include "driver/st7565.h"
#include "driver/system.h"
#include "misc.h"

uint8_t gStatusLine[128];
uint8_t gFrameBuffer[7][128];

static bool ST7565_WriteData(uint8_t Value)
{
	if (!SPI_WaitForTxFifoSpace()) {
		return false;
	}
	SPI0->WDR = Value;
	return true;
}

bool ST7565_DrawLine(uint8_t Column, uint8_t Line, uint16_t Size, const uint8_t *pBitmap, bool bIsClearMode)
{
	uint16_t i;
	bool Success = false;

	SPI_ToggleMasterMode(&SPI0->CR, false);
	if (!ST7565_SelectColumnAndLine(Column + 4U, Line)) {
		goto cleanup;
	}
	GPIO_SetBit(&GPIOB->DATA, GPIOB_PIN_ST7565_A0);

	if (!bIsClearMode) {
		for (i = 0; i < Size; i++) {
			if (!ST7565_WriteData(pBitmap[i])) {
				goto cleanup;
			}
		}
	} else {
		for (i = 0; i < Size; i++) {
			if (!ST7565_WriteData(0)) {
				goto cleanup;
			}
		}
	}

	Success = SPI_WaitForUndocumentedTxFifoStatusBit();
cleanup:
	SPI_ToggleMasterMode(&SPI0->CR, true);
	return Success;
}

bool ST7565_BlitFullScreen(void)
{
	uint8_t Line;
	uint8_t Column;
	bool Success = false;

	SPI_ToggleMasterMode(&SPI0->CR, false);
	if (!ST7565_WriteByte(0x40)) {
		goto cleanup;
	}

	for (Line = 0; Line < ARRAY_SIZE(gFrameBuffer); Line++) {
		if (!ST7565_SelectColumnAndLine(4U, Line + 1U)) {
			goto cleanup;
		}
		GPIO_SetBit(&GPIOB->DATA, GPIOB_PIN_ST7565_A0);
		for (Column = 0; Column < ARRAY_SIZE(gFrameBuffer[0]); Column++) {
			if (!ST7565_WriteData(gFrameBuffer[Line][Column])) {
				goto cleanup;
			}
		}
		if (!SPI_WaitForUndocumentedTxFifoStatusBit()) {
			goto cleanup;
		}
	}

	SYSTEM_DelayMs(20);
	Success = true;
cleanup:
	SPI_ToggleMasterMode(&SPI0->CR, true);
	return Success;
}

bool ST7565_BlitStatusLine(void)
{
	uint8_t i;
	bool Success = false;

	SPI_ToggleMasterMode(&SPI0->CR, false);
	if (!ST7565_WriteByte(0x40) || !ST7565_SelectColumnAndLine(4, 0)) {
		goto cleanup;
	}
	GPIO_SetBit(&GPIOB->DATA, GPIOB_PIN_ST7565_A0);

	for (i = 0; i < ARRAY_SIZE(gStatusLine); i++) {
		if (!ST7565_WriteData(gStatusLine[i])) {
			goto cleanup;
		}
	}
	Success = SPI_WaitForUndocumentedTxFifoStatusBit();
cleanup:
	SPI_ToggleMasterMode(&SPI0->CR, true);
	return Success;
}

bool ST7565_FillScreen(uint8_t Value)
{
	uint8_t i, j;
	bool Success = false;

	SPI_ToggleMasterMode(&SPI0->CR, false);
	for (i = 0; i < 8; i++) {
		if (!ST7565_SelectColumnAndLine(0, i)) {
			goto cleanup;
		}
		GPIO_SetBit(&GPIOB->DATA, GPIOB_PIN_ST7565_A0);
		for (j = 0; j < 132; j++) {
			if (!ST7565_WriteData(Value)) {
				goto cleanup;
			}
		}
		if (!SPI_WaitForUndocumentedTxFifoStatusBit()) {
			goto cleanup;
		}
	}
	Success = true;
cleanup:
	SPI_ToggleMasterMode(&SPI0->CR, true);
	return Success;
}

bool ST7565_Init(void)
{
	bool Success = false;

	SPI0_Init();
	ST7565_HardwareReset();
	SPI_ToggleMasterMode(&SPI0->CR, false);
	if (!ST7565_WriteByte(0xE2)) {
		goto cleanup;
	}
	SYSTEM_DelayMs(0x78);
	if (!ST7565_WriteByte(0xA2) || !ST7565_WriteByte(0xC0) || !ST7565_WriteByte(0xA1) || !ST7565_WriteByte(0xA6) || !ST7565_WriteByte(0xA4) || !ST7565_WriteByte(0x24) || !ST7565_WriteByte(0x81) || !ST7565_WriteByte(0x1F) || !ST7565_WriteByte(0x2B)) {
		goto cleanup;
	}
	SYSTEM_DelayMs(1);
	if (!ST7565_WriteByte(0x2E)) {
		goto cleanup;
	}
	SYSTEM_DelayMs(1);
	if (!ST7565_WriteByte(0x2F) || !ST7565_WriteByte(0x2F) || !ST7565_WriteByte(0x2F) || !ST7565_WriteByte(0x2F)) {
		goto cleanup;
	}
	SYSTEM_DelayMs(0x28);
	if (!ST7565_WriteByte(0x40) || !ST7565_WriteByte(0xAF) || !SPI_WaitForUndocumentedTxFifoStatusBit()) {
		goto cleanup;
	}
	Success = true;
cleanup:
	SPI_ToggleMasterMode(&SPI0->CR, true);
	return Success && ST7565_FillScreen(0x00);
}

void ST7565_HardwareReset(void)
{
	GPIO_SetBit(&GPIOB->DATA, GPIOB_PIN_ST7565_RES);
	SYSTEM_DelayMs(1);
	GPIO_ClearBit(&GPIOB->DATA, GPIOB_PIN_ST7565_RES);
	SYSTEM_DelayMs(20);
	GPIO_SetBit(&GPIOB->DATA, GPIOB_PIN_ST7565_RES);
	SYSTEM_DelayMs(120);
}

bool ST7565_SelectColumnAndLine(uint8_t Column, uint8_t Line)
{
	GPIO_ClearBit(&GPIOB->DATA, GPIOB_PIN_ST7565_A0);
	if (!ST7565_WriteData(Line + 0xB0)) {
		return false;
	}
	if (!ST7565_WriteData(((Column >> 4) & 0x0F) | 0x10)) {
		return false;
	}
	if (!ST7565_WriteData(((Column >> 0) & 0x0F))) {
		return false;
	}
	return SPI_WaitForUndocumentedTxFifoStatusBit();
}

bool ST7565_WriteByte(uint8_t Value)
{
	GPIO_ClearBit(&GPIOB->DATA, GPIOB_PIN_ST7565_A0);
	return ST7565_WriteData(Value);
}
