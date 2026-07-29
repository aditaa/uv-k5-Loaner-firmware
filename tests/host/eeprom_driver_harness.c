#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "driver/eeprom.h"

static bool gFailAddressWrite;
static bool gFailDataWrite;

void HOST_EepromDriver_Reset(bool FailAddressWrite, bool FailDataWrite)
{
	gFailAddressWrite = FailAddressWrite;
	gFailDataWrite	  = FailDataWrite;
}

void I2C_Start(void)
{
}

void I2C_Stop(void)
{
}

int I2C_Write(uint8_t Data)
{
	(void)Data;
	return gFailAddressWrite ? -1 : 0;
}

int I2C_ReadBuffer(void *pBuffer, uint8_t Size)
{
	memset(pBuffer, 0x5A, Size);
	return Size;
}

int I2C_WriteBuffer(const void *pBuffer, uint8_t Size)
{
	(void)pBuffer;
	(void)Size;
	return gFailDataWrite ? -1 : 0;
}

void SYSTEM_DelayMs(uint32_t Delay)
{
	(void)Delay;
}
