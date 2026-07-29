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

#ifndef APP_UART_PROTOCOL_H
#define APP_UART_PROTOCOL_H

#include <stdbool.h>
#include <stdint.h>

enum
{
	UART_PROTOCOL_EEPROM_SIZE = 0x2000,
	UART_PROTOCOL_READ_MAX_SIZE = 128,
	UART_PROTOCOL_WRITE_MAX_SIZE = 128,
	UART_PROTOCOL_WRITE_BLOCK_SIZE = 8,
};

typedef enum
{
	UART_PROTOCOL_FRAME_INCOMPLETE,
	UART_PROTOCOL_FRAME_INVALID,
	UART_PROTOCOL_FRAME_COMMAND,
} UART_PROTOCOL_FrameResult_t;

bool UART_PROTOCOL_ValidateCommand(const uint8_t* pCommand, uint16_t CommandSize);

UART_PROTOCOL_FrameResult_t UART_PROTOCOL_ParseFrame(
    const uint8_t* pRingBuffer,
    uint16_t RingBufferSize,
    uint16_t ReadIndex,
    uint16_t WriteIndex,
    bool bIsEncrypted,
    uint8_t* pCommand,
    uint16_t CommandCapacity,
    uint16_t* pNextReadIndex,
    uint16_t* pCommandSize,
    bool* pNextIsEncrypted);

#endif
