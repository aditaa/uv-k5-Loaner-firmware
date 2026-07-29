# Firmware host testing

Host tests exercise firmware logic without an ARM board. They complement, but
do not replace, release smoke tests on a radio.

## Test boundary

Pure modules accept ordinary values and buffers and must not read MCU registers
directly. Examples include frequency policy, EEPROM value validation, firmware
packing, and UART frame validation. These modules can be compiled with the host
C compiler and tested directly.

Hardware drivers under `driver/`, board initialization in `board.c`, and radio
state transitions that control the PA remain hardware-facing. When logic needs
one of those services, keep the decision logic separate and represent EEPROM,
register, time, and GPIO access through a small adapter. Reusable fake adapters
for those four resources live in `tests/host/fake_platform.*` and include
explicit read/write failure injection.

## Running tests

Run the full suite with:

```sh
pytest -q
```

Run one host module while developing with:

```sh
pytest -q tests/test_uart_protocol.py
```

Linux CI requires a host compiler and enables AddressSanitizer and
UndefinedBehaviorSanitizer for host executables. To reproduce that mode:

```sh
HOST_TESTS_REQUIRED=1 HOST_SANITIZERS=address,undefined pytest -q
```

## Hardware release checks

Before a release, separately record the exact firmware artifact and perform the
boot, channel-selection, receive-audio, PTT, timeout-timer, power-cycle, CHIRP
download/upload, battery, and RF bench checks required by the release issues.
Host tests cannot validate RF purity, PA shutdown timing, peripheral electrical
behavior, charging, or board-specific calibration.
