/* Copyright 2023 Dual Tachyon
 * https://github.com/DualTachyon
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "app/uart_protocol.h"
#include "driver/crc.h"

static const uint8_t Obfuscation[16] = { 0x16, 0x6C, 0x14, 0xE6, 0x2E, 0x91, 0x0D, 0x40, 0x21, 0x35, 0xD5, 0x40, 0x13, 0x03, 0xE9, 0x80 };

static uint16_t AddRingIndex(uint16_t Index, uint16_t Amount, uint16_t RingBufferSize)
{
	return (Index + Amount) % RingBufferSize;
}

static uint16_t GetRingDistance(uint16_t Start, uint16_t End, uint16_t RingBufferSize)
{
	if (End >= Start) {
		return End - Start;
	}

	return (RingBufferSize - Start) + End;
}

static uint16_t ReadUint16(const uint8_t *pData)
{
	return pData[0] | ((uint16_t)pData[1] << 8);
}

static uint16_t ReadRingUint16(const uint8_t *pRingBuffer, uint16_t RingBufferSize, uint16_t Index)
{
	return pRingBuffer[Index] | ((uint16_t)pRingBuffer[AddRingIndex(Index, 1, RingBufferSize)] << 8);
}

static bool IsEepromRangeValid(uint16_t Offset, uint16_t Size)
{
	return Size > 0 && (uint32_t)Offset + Size <= UART_PROTOCOL_EEPROM_SIZE;
}

bool UART_PROTOCOL_ValidateCommand(const uint8_t *pCommand, uint16_t CommandSize)
{
	uint16_t ID;
	uint16_t HeaderSize;

	if (CommandSize < 4) {
		return false;
	}

	ID	   = ReadUint16(&pCommand[0]);
	HeaderSize = ReadUint16(&pCommand[2]);
	if (HeaderSize != CommandSize - 4U) {
		return false;
	}

	switch (ID) {
	case 0x0514:
	case 0x052F:
		return CommandSize == 8;

	case 0x051B: {
		if (CommandSize != 12) {
			return false;
		}

		const uint16_t Offset = ReadUint16(&pCommand[4]);
		const uint8_t Size    = pCommand[6];

		return Size <= UART_PROTOCOL_READ_MAX_SIZE && IsEepromRangeValid(Offset, Size);
	}

	case 0x051D: {
		if (CommandSize < 12) {
			return false;
		}

		const uint16_t Offset = ReadUint16(&pCommand[4]);
		const uint8_t Size    = pCommand[6];

		return CommandSize == (uint16_t)(12U + Size) && Size <= UART_PROTOCOL_WRITE_MAX_SIZE && Size % UART_PROTOCOL_WRITE_BLOCK_SIZE == 0 && Offset % UART_PROTOCOL_WRITE_BLOCK_SIZE == 0 && IsEepromRangeValid(Offset, Size);
	}

	case 0x052D:
		return CommandSize == 20;

	case 0x051F:
	case 0x0521:
	case 0x0527:
	case 0x0529:
	case 0x05DD:
		return CommandSize == 4;
	}

	return false;
}

UART_PROTOCOL_FrameResult_t UART_PROTOCOL_ParseFrame(
	const uint8_t *pRingBuffer,
	uint16_t RingBufferSize,
	uint16_t ReadIndex,
	uint16_t WriteIndex,
	bool bIsEncrypted,
	uint8_t *pCommand,
	uint16_t CommandCapacity,
	uint16_t *pNextReadIndex,
	uint16_t *pCommandSize,
	bool *pNextIsEncrypted)
{
	uint16_t Available;
	uint16_t CRC;
	uint16_t ID;
	uint16_t Index;
	uint16_t PayloadIndex;
	uint16_t Size;
	uint16_t i;
	uint32_t FrameSize;
	bool bFrameIsEncrypted;

	*pNextReadIndex	  = ReadIndex;
	*pCommandSize	  = 0;
	*pNextIsEncrypted = bIsEncrypted;

	if (RingBufferSize == 0 || ReadIndex >= RingBufferSize || WriteIndex >= RingBufferSize) {
		return UART_PROTOCOL_FRAME_INVALID;
	}

	Index = ReadIndex;
	while (Index != WriteIndex) {
		if (pRingBuffer[Index] != 0xABU) {
			Index = AddRingIndex(Index, 1, RingBufferSize);
			continue;
		}

		Available = GetRingDistance(Index, WriteIndex, RingBufferSize);
		if (Available < 2) {
			*pNextReadIndex = Index;
			return UART_PROTOCOL_FRAME_INCOMPLETE;
		}
		if (pRingBuffer[AddRingIndex(Index, 1, RingBufferSize)] != 0xCDU) {
			Index = AddRingIndex(Index, 1, RingBufferSize);
			continue;
		}
		if (Available < 4) {
			*pNextReadIndex = Index;
			return UART_PROTOCOL_FRAME_INCOMPLETE;
		}

		Size	  = ReadRingUint16(pRingBuffer, RingBufferSize, AddRingIndex(Index, 2, RingBufferSize));
		FrameSize = Size + 8U;
		if (FrameSize > RingBufferSize || Size + 2U > CommandCapacity) {
			*pNextReadIndex = AddRingIndex(Index, 1, RingBufferSize);
			return UART_PROTOCOL_FRAME_INVALID;
		}
		if (Available < FrameSize) {
			*pNextReadIndex = Index;
			return UART_PROTOCOL_FRAME_INCOMPLETE;
		}

		PayloadIndex = AddRingIndex(Index, 4, RingBufferSize);
		if (pRingBuffer[AddRingIndex(PayloadIndex, Size + 2U, RingBufferSize)] != 0xDCU || pRingBuffer[AddRingIndex(PayloadIndex, Size + 3U, RingBufferSize)] != 0xBAU) {
			*pNextReadIndex = AddRingIndex(Index, 1, RingBufferSize);
			return UART_PROTOCOL_FRAME_INVALID;
		}

		for (i = 0; i < Size + 2U; i++) {
			pCommand[i] = pRingBuffer[AddRingIndex(PayloadIndex, i, RingBufferSize)];
		}
		*pNextReadIndex = AddRingIndex(Index, (uint16_t)FrameSize, RingBufferSize);

		bFrameIsEncrypted = bIsEncrypted;
		if (Size >= 2) {
			ID = ReadUint16(pCommand);
			if (ID == 0x0514) {
				bFrameIsEncrypted = false;
			} else if (ID == 0x6902) {
				bFrameIsEncrypted = true;
			}
		}

		if (bFrameIsEncrypted) {
			for (i = 0; i < Size + 2U; i++) {
				pCommand[i] ^= Obfuscation[i % sizeof(Obfuscation)];
			}
		}

		CRC = ReadUint16(&pCommand[Size]);
		if (CRC_Calculate(pCommand, Size) != CRC) {
			return UART_PROTOCOL_FRAME_INVALID;
		}
		if (!UART_PROTOCOL_ValidateCommand(pCommand, Size)) {
			return UART_PROTOCOL_FRAME_INVALID;
		}

		*pCommandSize	  = Size;
		*pNextIsEncrypted = bFrameIsEncrypted;
		return UART_PROTOCOL_FRAME_COMMAND;
	}

	*pNextReadIndex = Index;
	return UART_PROTOCOL_FRAME_INCOMPLETE;
}
