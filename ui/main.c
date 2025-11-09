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

#include <ctype.h>
#include <string.h>
#include "driver/st7565.h"
#include "external/printf/printf.h"
#include "functions.h"
#include "misc.h"
#include "radio.h"
#include "settings.h"
#include "ui/helper.h"
#include "ui/inputbox.h"
#include "ui/main.h"

static void UI_CopyUpperTrimmed(const char* src, char* dst, size_t length)
{
	size_t i;
	size_t j = 0;

	for (i = 0; i < 16 && src[i] != 0x00 && src[i] != (char)0xFF; i++) {
		char c = src[i];
		if (c < 0x20 || c > 0x7E) {
			continue;
		}
		if (c >= 'a' && c <= 'z') {
			c = c - ('a' - 'A');
		}
		if (j + 1 < length) {
			dst[j++] = c;
		}
	}
	dst[j] = 0;
}

static void UI_GetVfoLabel(uint8_t vfo, char* buffer, size_t length)
{
	char name[17];

	UI_CopyUpperTrimmed(gEeprom.VfoInfo[vfo].Name, name, sizeof(name));
	if (name[0] != '\0') {
		snprintf(buffer, length, "%s", name);
		return;
	}

	const uint8_t channel = gEeprom.ScreenChannel[vfo];
	if (IS_MR_CHANNEL(channel)) {
		char channel_string[8];

		if (gInputBoxIndex != 0 && gEeprom.TX_VFO == vfo) {
			UI_GenerateChannelStringEx(channel_string, true, channel);
		} else {
			snprintf(channel_string, sizeof(channel_string), "CH-%03u", channel + 1);
		}
		snprintf(buffer, length, "%s", channel_string);
		return;
	}

	if (IS_FREQ_CHANNEL(channel)) {
		const float mhz = gEeprom.VfoInfo[vfo].pRX->Frequency / 100000.0f;
		snprintf(buffer, length, "%.3f MHZ", mhz);
		return;
	}

#if defined(ENABLE_NOAA)
	if (IS_NOAA_CHANNEL(channel)) {
		snprintf(buffer, length, "NOAA %u", (channel - NOAA_CHANNEL_FIRST) + 1);
		return;
	}
#endif

	snprintf(buffer, length, "VFO");
}

static char UI_GetVfoMarker(uint8_t vfo)
{
	if (gCurrentFunction == FUNCTION_TRANSMIT && gEeprom.TX_VFO == vfo) {
		return 'T';
	}
	if ((gCurrentFunction == FUNCTION_RECEIVE || gCurrentFunction == FUNCTION_MONITOR) && gEeprom.RX_VFO == vfo) {
		return 'R';
	}
	if (gEeprom.TX_VFO == vfo) {
		return '>';
	}
	return ' ';
}

void UI_DisplayMain(void)
{
	char line[24];
	char label[18];
	uint8_t i;

	memset(gFrameBuffer, 0, sizeof(gFrameBuffer));
	if (gEeprom.KEY_LOCK && gKeypadLocked) {
		UI_PrintString("Long Press #", 0, 127, 1, 8, true);
		UI_PrintString("To Unlock", 0, 127, 3, 8, true);
		ST7565_BlitFullScreen();
		return;
	}

	for (i = 0; i < 2; i++) {
		UI_GetVfoLabel(i, label, sizeof(label));
		snprintf(line, sizeof(line), "%c%c %s",
			 UI_GetVfoMarker(i),
			 (i == 0) ? 'A' : 'B',
			 label);
		UI_PrintString(line, 0, 127, 2 + (i * 3), 8, true);
	}

	ST7565_BlitFullScreen();
}
