# Peripheral timeout and recovery policy

Firmware code must not wait forever for a peripheral. A timeout records the
failing subsystem, returns failure through the driver API, and is consumed by
the foreground loop. The recovery path disables the BK4819 TX DSP, PA bias,
PA-enable GPIO, red TX LED, speaker path, and future TX attempts. When the LCD
is usable, the main screen displays the failing subsystem and the radio remains
receive-only until it is rebooted.

## Polling inventory

| Path | Bound | Failure behavior |
| --- | ---: | --- |
| ADC battery conversion | 100,000 polls | Soft-reset ADC; preserve the previous reading |
| AES block completion | 100,000 polls | Disable AES; reject the UART challenge |
| UART TX FIFO | 100,000 polls per byte | Clear the TX FIFO; abort the reply |
| LCD SPI FIFO / TX active | 100,000 polls | Abort the current display operation |
| BK4819 interrupt drain | 64 events per foreground pass | Latch radio fault and force TX-safe state |
| BK4819 setup interrupt clear | 100 ms | Abort setup and force TX-safe state |
| BK4819 air-copy TX | 200 polls at 5 ms | Reset FSK and latch radio fault |
| EEPROM I2C ACK | 255 polls per byte | Stop the bus; reads return erased `0xFF` defaults and writes fail |
| Optional flash busy / wake | 1,000,000 polls | Abort the overlay operation and return failure |

The poll counts are deliberately generous CPU-iteration limits. The BK4819
paths use existing millisecond delays and therefore have explicit wall-clock
bounds. Hardware release testing must confirm that normal operations never
approach these limits and that firmware size remains within the configured CI
limit.

## Intentionally permanent loops

- `main.c` is the cooperative firmware scheduler and runs for the life of the
  device.
- `ui/lock.c` owns the password screen until the user unlocks it; its inner
  wait is released by the SysTick interrupt.
- `driver/systick.c` implements requested microsecond delays while verifying
  that the counter advances.
- `app/uart_protocol.c` drains a finite DMA ring-buffer snapshot.
- `sram-overlay.c` waits forever only after requesting a CPU reset, because
  returning to normal execution after that request is unsafe.

The host suite injects stuck-register and EEPROM ACK/data failures to verify
bounded return, diagnostic latching, safe read defaults, and status
propagation. Physical timing and the PA-disable signal are part of the hardware
release checklist.
