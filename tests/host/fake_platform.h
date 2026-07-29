#ifndef TESTS_HOST_FAKE_PLATFORM_H
#define TESTS_HOST_FAKE_PLATFORM_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define HOST_FAKE_EEPROM_SIZE 0x2000U
#define HOST_FAKE_REGISTER_COUNT 128U
#define HOST_FAKE_GPIO_COUNT 32U

typedef struct
{
	uint8_t Eeprom[HOST_FAKE_EEPROM_SIZE];
	uint16_t Registers[HOST_FAKE_REGISTER_COUNT];
	bool Gpio[HOST_FAKE_GPIO_COUNT];
	uint32_t Time;
	bool FailEepromRead;
	bool FailEepromWrite;
	bool FailRegisterRead;
	bool FailRegisterWrite;
} HOST_FakePlatform_t;

void HOST_FakePlatform_Reset(HOST_FakePlatform_t *pPlatform);
bool HOST_FakeEeprom_Read(HOST_FakePlatform_t *pPlatform, uint16_t Address, void *pData, size_t Size);
bool HOST_FakeEeprom_Write(HOST_FakePlatform_t *pPlatform, uint16_t Address, const void *pData, size_t Size);
bool HOST_FakeRegister_Read(HOST_FakePlatform_t *pPlatform, uint8_t Address, uint16_t *pValue);
bool HOST_FakeRegister_Write(HOST_FakePlatform_t *pPlatform, uint8_t Address, uint16_t Value);
uint32_t HOST_FakeTime_Get(const HOST_FakePlatform_t *pPlatform);
void HOST_FakeTime_Advance(HOST_FakePlatform_t *pPlatform, uint32_t Ticks);
bool HOST_FakeGpio_Get(const HOST_FakePlatform_t *pPlatform, uint8_t Pin);
void HOST_FakeGpio_Set(HOST_FakePlatform_t *pPlatform, uint8_t Pin, bool Set);

#endif
