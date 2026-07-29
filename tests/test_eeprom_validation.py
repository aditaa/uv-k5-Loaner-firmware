import ctypes
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


BATTERY_FALLBACK = [1258, 1747, 1876, 1901, 2004, 2300]
RSSI_FALLBACK = [512, 512, 512, 512]
PA_FALLBACK = [0, 0, 0]


@pytest.fixture(scope="session")
def validation_library(tmp_path_factory):
    compiler = shutil.which("gcc")
    if compiler is None:
        pytest.skip("gcc is required for the EEPROM validation host tests")

    repo_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path_factory.mktemp("eeprom-validation")
    library = output_dir / ("eeprom_validation.dll" if sys.platform == "win32" else "libeeprom_validation.so")
    command = [
        compiler,
        "-shared",
        "-std=c11",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-I",
        str(repo_root),
        str(repo_root / "eeprom_validation.c"),
        "-o",
        str(library),
    ]
    if sys.platform != "win32":
        command.insert(2, "-fPIC")
    subprocess.run(command, check=True)

    loaded = ctypes.CDLL(str(library))
    loaded.EEPROM_ValidateU8.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
    loaded.EEPROM_ValidateU8.restype = ctypes.c_uint8
    loaded.EEPROM_ValidateBool.argtypes = [ctypes.c_uint8, ctypes.c_bool]
    loaded.EEPROM_ValidateBool.restype = ctypes.c_bool
    loaded.EEPROM_ValidateChannel.argtypes = [
        ctypes.c_uint8,
        ctypes.c_uint8,
        ctypes.c_uint8,
        ctypes.c_uint8,
    ]
    loaded.EEPROM_ValidateChannel.restype = ctypes.c_uint8
    loaded.EEPROM_ValidateOutputPower.argtypes = [ctypes.c_uint8]
    loaded.EEPROM_ValidateOutputPower.restype = ctypes.c_uint8
    loaded.EEPROM_ValidateBatteryCalibration.argtypes = [ctypes.POINTER(ctypes.c_uint16)]
    loaded.EEPROM_ValidateBatteryCalibration.restype = ctypes.c_bool
    loaded.EEPROM_ValidateRssiCalibration.argtypes = [ctypes.POINTER(ctypes.c_uint16)]
    loaded.EEPROM_ValidateRssiCalibration.restype = ctypes.c_bool
    loaded.EEPROM_ValidatePaCalibration.argtypes = [ctypes.POINTER(ctypes.c_uint8)]
    loaded.EEPROM_ValidatePaCalibration.restype = ctypes.c_bool
    return loaded


def test_scalar_index_and_channel_validation(validation_library):
    lib = validation_library

    assert lib.EEPROM_ValidateU8(4, 5, 2) == 4
    assert lib.EEPROM_ValidateU8(5, 5, 2) == 2
    assert lib.EEPROM_ValidateBool(1, False) is True
    assert lib.EEPROM_ValidateBool(0xFF, False) is False
    assert lib.EEPROM_ValidateChannel(199, 0, 199, 0xFF) == 199
    assert lib.EEPROM_ValidateChannel(200, 0, 199, 0xFF) == 0xFF
    assert lib.EEPROM_ValidateOutputPower(0) == 0
    assert lib.EEPROM_ValidateOutputPower(2) == 2
    assert lib.EEPROM_ValidateOutputPower(3) == 2
    assert lib.EEPROM_ValidateOutputPower(0xFF) == 2


def _validate_u16(lib, function_name, values):
    array_type = ctypes.c_uint16 * len(values)
    array = array_type(*values)
    valid = getattr(lib, function_name)(array)
    return valid, list(array)


@pytest.mark.parametrize(
    ("values", "expected_valid", "expected"),
    [
        ([1258, 1747, 1876, 1901, 2004, 2300], True, BATTERY_FALLBACK),
        ([0] * 6, False, BATTERY_FALLBACK),
        ([0xFFFF] * 6, False, BATTERY_FALLBACK),
        ([1258, 1747, 1876, 0, 2004, 2300], False, BATTERY_FALLBACK),
        ([1258, 1747, 1876, 1876, 2004, 2300], False, BATTERY_FALLBACK),
    ],
)
def test_battery_calibration_fixtures(validation_library, values, expected_valid, expected):
    valid, result = _validate_u16(validation_library, "EEPROM_ValidateBatteryCalibration", values)

    assert valid is expected_valid
    assert result == expected
    assert result[3] != 0
    assert all(left < right for left, right in zip(result, result[1:]))


@pytest.mark.parametrize(
    ("values", "expected_valid", "expected"),
    [
        ([100, 200, 300, 400], True, [100, 200, 300, 400]),
        ([0] * 4, False, RSSI_FALLBACK),
        ([0xFFFF] * 4, False, RSSI_FALLBACK),
        ([100, 200, 150, 400], False, RSSI_FALLBACK),
    ],
)
def test_rssi_calibration_fixtures(validation_library, values, expected_valid, expected):
    valid, result = _validate_u16(validation_library, "EEPROM_ValidateRssiCalibration", values)

    assert valid is expected_valid
    assert result == expected


@pytest.mark.parametrize(
    ("values", "expected_valid", "expected"),
    [
        ([50, 100, 140], True, [50, 100, 140]),
        ([0] * 3, False, PA_FALLBACK),
        ([0xFF] * 3, False, PA_FALLBACK),
        ([50, 0xFF, 140], False, PA_FALLBACK),
        ([50, 201, 140], False, PA_FALLBACK),
    ],
)
def test_pa_calibration_fixtures(validation_library, values, expected_valid, expected):
    array_type = ctypes.c_uint8 * len(values)
    array = array_type(*values)

    valid = validation_library.EEPROM_ValidatePaCalibration(array)

    assert valid is expected_valid
    assert list(array) == expected
