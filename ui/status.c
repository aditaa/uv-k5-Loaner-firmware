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
#include <string.h>
#include "bitmaps.h"
#include "driver/st7565.h"
#include "font.h"
#include "helper/battery.h"
#include "external/printf/printf.h"

static const uint8_t PercentGlyph[7] = { 0x41, 0xA2, 0x44, 0x08, 0x13, 0x26, 0x44 };

static uint8_t UI_BatteryPercent(void)
{
	static const uint8_t Lookup[] = { 0, 20, 40, 60, 80, 95, 100 };
	uint8_t level = gBatteryDisplayLevel;

	if (level >= (sizeof(Lookup) / sizeof(Lookup[0]))) {
		level = (sizeof(Lookup) / sizeof(Lookup[0])) - 1;
	}
	return Lookup[level];
}

static uint8_t UI_StatusWriteDigits(uint8_t cursor, const char *text)
{
	while (*text != '\0' && cursor + 7 < sizeof(gStatusLine)) {
		const char c = *text++;
		if (c >= '0' && c <= '9') {
			memcpy(gStatusLine + cursor, gFontSmallDigits[c - '0'], 7);
			cursor += 7;
		} else if (c == ' ') {
			cursor += 3;
		}
	}
	return cursor;
}

void UI_DisplayStatus(void)
{
	memset(gStatusLine, 0, sizeof(gStatusLine));

	if (gBatteryDisplayLevel < 2) {
		if (gLowBatteryBlink == 1) {
			memcpy(gStatusLine + 110, BITMAP_BatteryLevel1, sizeof(BITMAP_BatteryLevel1));
		}
	} else {
		switch (gBatteryDisplayLevel) {
		case 2:
			memcpy(gStatusLine + 110, BITMAP_BatteryLevel2, sizeof(BITMAP_BatteryLevel2));
			break;
		case 3:
			memcpy(gStatusLine + 110, BITMAP_BatteryLevel3, sizeof(BITMAP_BatteryLevel3));
			break;
		case 4:
			memcpy(gStatusLine + 110, BITMAP_BatteryLevel4, sizeof(BITMAP_BatteryLevel4));
			break;
		default:
			memcpy(gStatusLine + 110, BITMAP_BatteryLevel5, sizeof(BITMAP_BatteryLevel5));
			break;
		}
	}

	if (gChargingWithTypeC) {
		memcpy(gStatusLine + 100, BITMAP_USB_C, sizeof(BITMAP_USB_C));
	}

	char text[4];
	snprintf(text, sizeof(text), "%u", UI_BatteryPercent());
	uint8_t cursor = 70;
	cursor = UI_StatusWriteDigits(cursor, text);
	if (cursor + 7 < sizeof(gStatusLine)) {
		memcpy(gStatusLine + cursor, PercentGlyph, sizeof(PercentGlyph));
	}

	ST7565_BlitStatusLine();
}
