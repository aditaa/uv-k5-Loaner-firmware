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

#include "app/action.h"
#include "app/app.h"
#include "app/dtmf.h"
#if defined(ENABLE_FMRADIO)
#include "app/fm.h"
#endif
#include "app/scanner.h"
#include "audio.h"
#include "bsp/dp32g030/gpio.h"
#include "driver/bk1080.h"
#include "driver/bk4819.h"
#include "driver/gpio.h"
#include "functions.h"
#include "misc.h"
#include "settings.h"
#include "ui/inputbox.h"
#include "ui/ui.h"

void ACTION_Power(void)
{
	if (++gTxVfo->OUTPUT_POWER > OUTPUT_POWER_HIGH) {
		gTxVfo->OUTPUT_POWER = OUTPUT_POWER_LOW;
	}

	gRequestSaveChannel = 1;
	gAnotherVoiceID = VOICE_ID_POWER;
	gRequestDisplayScreen = gScreenToDisplay;
}

void ACTION_Scan(bool bRestart)
{
#if defined(ENABLE_FMRADIO)
	if (gFmRadioMode) {
		if (gCurrentFunction != FUNCTION_RECEIVE && gCurrentFunction != FUNCTION_MONITOR && gCurrentFunction != FUNCTION_TRANSMIT) {
			uint16_t Frequency;

			GUI_SelectNextDisplay(DISPLAY_FM);
			if (gFM_ScanState != FM_SCAN_OFF) {
				FM_PlayAndUpdate();
				gAnotherVoiceID = VOICE_ID_SCANNING_STOP;
			} else {
				if (bRestart) {
					gFM_AutoScan = true;
					gFM_ChannelPosition = 0;
					FM_EraseChannels();
					Frequency = gEeprom.FM_LowerLimit;
				} else {
					gFM_AutoScan = false;
					gFM_ChannelPosition = 0;
					Frequency = gEeprom.FM_FrequencyPlaying;
				}
				BK1080_GetFrequencyDeviation(Frequency);
				FM_Tune(Frequency, 1, bRestart);
				gAnotherVoiceID = VOICE_ID_SCANNING_BEGIN;
			}
		}
	} else
#endif
	if (gScreenToDisplay != DISPLAY_SCANNER) {
		RADIO_SelectVfos();
		if (IS_NOT_NOAA_CHANNEL(gRxVfo->CHANNEL_SAVE)) {
			GUI_SelectNextDisplay(DISPLAY_MAIN);
			if (gScanState != SCAN_OFF) {
				SCANNER_Stop();
				gAnotherVoiceID = VOICE_ID_SCANNING_STOP;
			} else {
				CHANNEL_Next(true, 1);
				AUDIO_SetVoiceID(0, VOICE_ID_SCANNING_BEGIN);
				AUDIO_PlaySingleVoice(true);
			}
		}
	}
}

void ACTION_Vox(void)
{
	gEeprom.VOX_SWITCH = !gEeprom.VOX_SWITCH;
	gRequestSaveSettings = true;
	gFlagReconfigureVfos = true;
	gAnotherVoiceID = VOICE_ID_VOX;
	gUpdateStatus = true;
}

static void ACTION_SelectVfo(uint8_t Target)
{
	if (Target > 1) {
		return;
	}

	if (gScanState != SCAN_OFF) {
		SCANNER_Stop();
		gAnotherVoiceID = VOICE_ID_SCANNING_STOP;
	}

	gWasFKeyPressed = false;
	gEeprom.CROSS_BAND_RX_TX = CROSS_BAND_OFF;
	gEeprom.DUAL_WATCH = DUAL_WATCH_OFF;

	if (gEeprom.TX_VFO == Target && gEeprom.RX_VFO == Target) {
		gRequestDisplayScreen = DISPLAY_MAIN;
		gUpdateStatus = true;
		return;
	}

	gEeprom.TX_VFO = Target;
	gEeprom.RX_VFO = Target;
	gTxVfo = &gEeprom.VfoInfo[Target];
	gRxVfo = &gEeprom.VfoInfo[Target];

	gRequestSaveVFO = true;
	gVfoConfigureMode = VFO_CONFIGURE_RELOAD;
	gFlagResetVfos = true;
	gFlagReconfigureVfos = true;
	gUpdateStatus = true;
	gRequestDisplayScreen = DISPLAY_MAIN;
	if (IS_MR_CHANNEL(gEeprom.ScreenChannel[Target])) {
		AUDIO_SetVoiceID(0, VOICE_ID_CHANNEL_MODE);
		AUDIO_SetDigitVoice(1, gEeprom.ScreenChannel[Target] + 1);
		gAnotherVoiceID = (VOICE_ID_t)0xFE;
	}
}

#if defined(ENABLE_FMRADIO)
void ACTION_FM(void)
{
	if (gCurrentFunction != FUNCTION_TRANSMIT && gCurrentFunction != FUNCTION_MONITOR) {
		if (gFmRadioMode) {
			FM_TurnOff();
			gInputBoxIndex = 0;
			gVoxResumeCountdown = 80;
			gFlagReconfigureVfos = true;
			gRequestDisplayScreen = DISPLAY_MAIN;
			return;
		}
		RADIO_SelectVfos();
		RADIO_SetupRegisters(true);
		FM_Start();
		gInputBoxIndex = 0;
		gRequestDisplayScreen = DISPLAY_FM;
	}
}
#endif

void ACTION_Handle(KEY_Code_t Key, bool bKeyPressed, bool bKeyHeld)
{
	uint8_t Target;

	if (gScreenToDisplay == DISPLAY_MAIN && gDTMF_InputMode) {
		if (Key == KEY_SIDE1 && !bKeyHeld && bKeyPressed) {
			gBeepToPlay = BEEP_1KHZ_60MS_OPTIONAL;
			if (gDTMF_InputIndex) {
				gDTMF_InputIndex--;
				gDTMF_InputBox[gDTMF_InputIndex] = '-';
				if (gDTMF_InputIndex) {
					gPttWasReleased = true;
					gRequestDisplayScreen = DISPLAY_MAIN;
					return;
				}
			}
			gAnotherVoiceID = VOICE_ID_CANCEL;
			gRequestDisplayScreen = DISPLAY_MAIN;
			gDTMF_InputMode = false;
		}
		gPttWasReleased = true;
		return;
	}

	if (Key == KEY_SIDE1 || Key == KEY_SIDE2) {
		Target = (Key == KEY_SIDE1) ? 0 : 1;
		if (!bKeyHeld && bKeyPressed) {
			gBeepToPlay = BEEP_1KHZ_60MS_OPTIONAL;
			return;
		}
		if (!bKeyPressed) {
			ACTION_SelectVfo(Target);
		}
		return;
	}
}
