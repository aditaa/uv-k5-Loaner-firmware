/* Copyright 2026 Open Edition contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 */

#ifndef DRIVER_HARDWARE_H
#define DRIVER_HARDWARE_H

#include <stdbool.h>
#include <stdint.h>

enum HARDWARE_Fault_t {
	HARDWARE_FAULT_NONE = 0U,
	HARDWARE_FAULT_ADC,
	HARDWARE_FAULT_AES,
	HARDWARE_FAULT_UART,
	HARDWARE_FAULT_SPI,
	HARDWARE_FAULT_EEPROM,
	HARDWARE_FAULT_BK4819,
	HARDWARE_FAULT_FLASH,
};

typedef enum HARDWARE_Fault_t HARDWARE_Fault_t;

bool HARDWARE_WaitForRegister(const volatile uint32_t *pRegister, uint32_t Mask, uint32_t Expected, uint32_t PollLimit);
void HARDWARE_ReportFault(HARDWARE_Fault_t Fault);
HARDWARE_Fault_t HARDWARE_GetLastFault(void);
HARDWARE_Fault_t HARDWARE_TakePendingFault(void);
void HARDWARE_ClearFault(void);

#endif
