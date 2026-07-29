import ctypes

import pytest

from tests.host_tools import ROOT, compile_c, shared_library_path


@pytest.fixture(scope="session")
def eeprom_driver_library(tmp_path_factory):
    output_dir = tmp_path_factory.mktemp("eeprom-driver")
    library = shared_library_path(output_dir, "eeprom_driver")
    compile_c(
        output=library,
        sources=[
            ROOT / "driver" / "eeprom.c",
            ROOT / "driver" / "hardware.c",
            ROOT / "tests" / "host" / "eeprom_driver_harness.c",
        ],
        shared=True,
    )

    loaded = ctypes.CDLL(str(library))
    loaded.HOST_EepromDriver_Reset.argtypes = [ctypes.c_bool, ctypes.c_bool]
    loaded.EEPROM_ReadBuffer.argtypes = [
        ctypes.c_uint16,
        ctypes.c_void_p,
        ctypes.c_uint8,
    ]
    loaded.EEPROM_ReadBuffer.restype = ctypes.c_bool
    loaded.EEPROM_WriteBuffer.argtypes = [ctypes.c_uint16, ctypes.c_void_p]
    loaded.EEPROM_WriteBuffer.restype = ctypes.c_bool
    loaded.HARDWARE_GetLastFault.restype = ctypes.c_int
    loaded.HARDWARE_ClearFault.argtypes = []
    return loaded


def test_eeprom_read_success_propagates_data(eeprom_driver_library):
    lib = eeprom_driver_library
    output = (ctypes.c_uint8 * 8)()
    lib.HARDWARE_ClearFault()
    lib.HOST_EepromDriver_Reset(False, False)

    assert lib.EEPROM_ReadBuffer(0x100, output, len(output))
    assert list(output) == [0x5A] * len(output)
    assert lib.HARDWARE_GetLastFault() == 0


def test_eeprom_ack_failure_returns_safe_erased_defaults(eeprom_driver_library):
    lib = eeprom_driver_library
    output = (ctypes.c_uint8 * 8)(*([0x12] * 8))
    lib.HARDWARE_ClearFault()
    lib.HOST_EepromDriver_Reset(True, False)

    assert not lib.EEPROM_ReadBuffer(0x100, output, len(output))
    assert list(output) == [0xFF] * len(output)
    assert lib.HARDWARE_GetLastFault() == 5


def test_eeprom_data_write_failure_is_reported(eeprom_driver_library):
    lib = eeprom_driver_library
    data = (ctypes.c_uint8 * 8)(*range(8))
    lib.HARDWARE_ClearFault()
    lib.HOST_EepromDriver_Reset(False, True)

    assert not lib.EEPROM_WriteBuffer(0x100, data)
    assert lib.HARDWARE_GetLastFault() == 5
