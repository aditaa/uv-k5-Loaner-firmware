#include <stdint.h>
#include <string.h>

#include "tests/host/fake_platform.h"

int main(void)
{
	HOST_FakePlatform_t Platform;
	const uint8_t Written[]	      = { 1U, 2U, 3U, 4U };
	uint8_t Read[sizeof(Written)] = { 0 };
	uint16_t Register;

	HOST_FakePlatform_Reset(&Platform);
	if (!HOST_FakeEeprom_Write(&Platform, 0x100U, Written, sizeof(Written))) {
		return 1;
	}
	if (!HOST_FakeEeprom_Read(&Platform, 0x100U, Read, sizeof(Read)) || memcmp(Written, Read, sizeof(Read)) != 0) {
		return 2;
	}
	if (HOST_FakeEeprom_Read(&Platform, HOST_FAKE_EEPROM_SIZE - 1U, Read, sizeof(Read))) {
		return 3;
	}
	Platform.FailEepromRead = true;
	if (HOST_FakeEeprom_Read(&Platform, 0x100U, Read, sizeof(Read))) {
		return 4;
	}
	if (!HOST_FakeRegister_Write(&Platform, 0x20U, 0xA55AU) || !HOST_FakeRegister_Read(&Platform, 0x20U, &Register) || Register != 0xA55AU) {
		return 5;
	}
	HOST_FakeTime_Advance(&Platform, 25U);
	if (HOST_FakeTime_Get(&Platform) != 25U) {
		return 6;
	}
	HOST_FakeGpio_Set(&Platform, 7U, true);
	if (!HOST_FakeGpio_Get(&Platform, 7U) || HOST_FakeGpio_Get(&Platform, HOST_FAKE_GPIO_COUNT)) {
		return 7;
	}
	return 0;
}
