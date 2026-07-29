# EEPROM validation and compatibility

Firmware settings and calibration values are validated when they are loaded into RAM. Validation never writes a fallback value back to EEPROM, so the EEPROM address map and the bytes managed by CHIRP remain unchanged.

Valid settings retain their stored value. Out-of-range enumerations and indexes use the existing firmware defaults, invalid scan-priority channels are disabled with the `0xFF` sentinel, and output power is clamped to the supported low-through-high range.

Calibration failures use conservative runtime fallbacks:

- Battery thresholds must be strictly increasing and between 500 and 3000 ADC counts. An invalid table uses the known UV-K5 sample table `{1258, 1747, 1876, 1901, 2004, 2300}`, which also guarantees the voltage calculation divisor is nonzero.
- RSSI thresholds must be strictly increasing 9-bit values. An invalid table uses `{512, 512, 512, 512}`, suppressing S-meter bars instead of displaying misleading strength.
- PA calibration bytes must be between 1 and 200. An invalid triplet uses zero bias, preventing transmission with an untrusted amplifier setting.

The EEPROM layout, channel records, names, welcome strings, DTMF data, AES key, calibration records, and unused padding are not migrated or normalized. This preserves round-trip compatibility with CHIRP and existing radio images.
