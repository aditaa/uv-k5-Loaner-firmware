/* Copyright 2026 Open Edition contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 */

#include "driver/hardware.h"

static volatile HARDWARE_Fault_t gLastHardwareFault;
static volatile bool gHardwareFaultPending;

bool HARDWARE_WaitForRegister(const volatile uint32_t *pRegister, uint32_t Mask, uint32_t Expected, uint32_t PollLimit)
{
	while (PollLimit != 0U) {
		PollLimit--;
		if ((*pRegister & Mask) == Expected) {
			return true;
		}
	}

	return false;
}

void HARDWARE_ReportFault(HARDWARE_Fault_t Fault)
{
	if (Fault != HARDWARE_FAULT_NONE) {
		gLastHardwareFault    = Fault;
		gHardwareFaultPending = true;
	}
}

HARDWARE_Fault_t HARDWARE_GetLastFault(void)
{
	return gLastHardwareFault;
}

HARDWARE_Fault_t HARDWARE_TakePendingFault(void)
{
	const HARDWARE_Fault_t Fault = gHardwareFaultPending ? gLastHardwareFault : HARDWARE_FAULT_NONE;

	gHardwareFaultPending = false;
	return Fault;
}

void HARDWARE_ClearFault(void)
{
	gLastHardwareFault    = HARDWARE_FAULT_NONE;
	gHardwareFaultPending = false;
}
