#include <string.h>

#include "tests/host/fake_platform.h"

void HOST_FakePlatform_Reset(HOST_FakePlatform_t *pPlatform)
{
	memset(pPlatform, 0, sizeof(*pPlatform));
}

bool HOST_FakeEeprom_Read(HOST_FakePlatform_t *pPlatform, uint16_t Address, void *pData, size_t Size)
{
	if (pPlatform->FailEepromRead || Address > HOST_FAKE_EEPROM_SIZE || Size > HOST_FAKE_EEPROM_SIZE - Address) {
		return false;
	}
	memcpy(pData, &pPlatform->Eeprom[Address], Size);
	return true;
}

bool HOST_FakeEeprom_Write(HOST_FakePlatform_t *pPlatform, uint16_t Address, const void *pData, size_t Size)
{
	if (pPlatform->FailEepromWrite || Address > HOST_FAKE_EEPROM_SIZE || Size > HOST_FAKE_EEPROM_SIZE - Address) {
		return false;
	}
	memcpy(&pPlatform->Eeprom[Address], pData, Size);
	return true;
}

bool HOST_FakeRegister_Read(HOST_FakePlatform_t *pPlatform, uint8_t Address, uint16_t *pValue)
{
	if (pPlatform->FailRegisterRead || Address >= HOST_FAKE_REGISTER_COUNT) {
		return false;
	}
	*pValue = pPlatform->Registers[Address];
	return true;
}

bool HOST_FakeRegister_Write(HOST_FakePlatform_t *pPlatform, uint8_t Address, uint16_t Value)
{
	if (pPlatform->FailRegisterWrite || Address >= HOST_FAKE_REGISTER_COUNT) {
		return false;
	}
	pPlatform->Registers[Address] = Value;
	return true;
}

uint32_t HOST_FakeTime_Get(const HOST_FakePlatform_t *pPlatform)
{
	return pPlatform->Time;
}

void HOST_FakeTime_Advance(HOST_FakePlatform_t *pPlatform, uint32_t Ticks)
{
	pPlatform->Time += Ticks;
}

bool HOST_FakeGpio_Get(const HOST_FakePlatform_t *pPlatform, uint8_t Pin)
{
	return Pin < HOST_FAKE_GPIO_COUNT && pPlatform->Gpio[Pin];
}

void HOST_FakeGpio_Set(HOST_FakePlatform_t *pPlatform, uint8_t Pin, bool Set)
{
	if (Pin < HOST_FAKE_GPIO_COUNT) {
		pPlatform->Gpio[Pin] = Set;
	}
}
