#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "app/uart_protocol.h"

uint16_t CRC_Calculate(const void *pBuffer, uint16_t Size)
{
	const uint8_t *pData = pBuffer;
	uint16_t CRC	     = 0;
	uint16_t i;
	uint8_t Bit;

	for (i = 0; i < Size; i++) {
		CRC ^= (uint16_t)pData[i] << 8;
		for (Bit = 0; Bit < 8; Bit++) {
			if ((CRC & 0x8000U) != 0) {
				CRC = (CRC << 1) ^ 0x1021U;
			} else {
				CRC <<= 1;
			}
		}
	}

	return CRC;
}

static int HexValue(char Value)
{
	if (Value >= '0' && Value <= '9') {
		return Value - '0';
	}
	if (Value >= 'a' && Value <= 'f') {
		return Value - 'a' + 10;
	}
	if (Value >= 'A' && Value <= 'F') {
		return Value - 'A' + 10;
	}

	return -1;
}

static int DecodeHex(const char *pHex, uint8_t *pOutput, size_t OutputCapacity)
{
	const size_t HexLength = strlen(pHex);
	size_t i;

	if (HexLength % 2 != 0 || HexLength / 2 > OutputCapacity) {
		return -1;
	}

	for (i = 0; i < HexLength / 2; i++) {
		const int High = HexValue(pHex[i * 2]);
		const int Low  = HexValue(pHex[(i * 2) + 1]);

		if (High < 0 || Low < 0) {
			return -1;
		}
		pOutput[i] = (High << 4) | Low;
	}

	return (int)(HexLength / 2);
}

static int ValidateCommand(const char *pHex)
{
	uint8_t Command[256];
	const int CommandSize = DecodeHex(pHex, Command, sizeof(Command));

	if (CommandSize < 0) {
		return 2;
	}

	printf("%u\n", UART_PROTOCOL_ValidateCommand(Command, CommandSize));
	return 0;
}

static int ParseFrame(const char *pHex, const char *pRingSizeText, const char *pStartText, const char *pEncryptedText)
{
	uint8_t Frame[256];
	uint8_t RingBuffer[256]	      = { 0 };
	uint8_t Command[256]	      = { 0 };
	const int FrameLength	      = DecodeHex(pHex, Frame, sizeof(Frame));
	const uint16_t RingBufferSize = (uint16_t)strtoul(pRingSizeText, NULL, 0);
	const uint16_t Start	      = (uint16_t)strtoul(pStartText, NULL, 0);
	const bool bIsEncrypted	      = strtoul(pEncryptedText, NULL, 0) != 0;
	uint16_t CommandSize;
	uint16_t NextReadIndex;
	uint16_t WriteIndex;
	uint16_t i;
	bool bNextIsEncrypted;
	UART_PROTOCOL_FrameResult_t Result;

	if (FrameLength < 0 || RingBufferSize == 0 || RingBufferSize > sizeof(RingBuffer) || Start >= RingBufferSize || FrameLength >= RingBufferSize) {
		return 2;
	}

	for (i = 0; i < (uint16_t)FrameLength; i++) {
		RingBuffer[(Start + i) % RingBufferSize] = Frame[i];
	}
	WriteIndex = (Start + FrameLength) % RingBufferSize;

	Result = UART_PROTOCOL_ParseFrame(
		RingBuffer,
		RingBufferSize,
		Start,
		WriteIndex,
		bIsEncrypted,
		Command,
		sizeof(Command),
		&NextReadIndex,
		&CommandSize,
		&bNextIsEncrypted);

	printf("%u %u %u %u %04X\n", Result, NextReadIndex, CommandSize, bNextIsEncrypted, CommandSize >= 2 ? Command[0] | (Command[1] << 8) : 0);
	return 0;
}

int main(int argc, char **argv)
{
	if (argc == 3 && strcmp(argv[1], "validate") == 0) {
		return ValidateCommand(argv[2]);
	}
	if (argc == 6 && strcmp(argv[1], "parse") == 0) {
		return ParseFrame(argv[2], argv[3], argv[4], argv[5]);
	}

	return 2;
}
