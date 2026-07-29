import ctypes

import pytest

from tests.host_tools import ROOT, compile_c, shared_library_path


@pytest.fixture(scope="session")
def hardware_library(tmp_path_factory):
    output_dir = tmp_path_factory.mktemp("hardware-timeout")
    library = shared_library_path(output_dir, "hardware_timeout")
    compile_c(
        output=library,
        sources=[ROOT / "driver" / "hardware.c"],
        shared=True,
    )

    loaded = ctypes.CDLL(str(library))
    loaded.HARDWARE_WaitForRegister.argtypes = [
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
    ]
    loaded.HARDWARE_WaitForRegister.restype = ctypes.c_bool
    loaded.HARDWARE_ReportFault.argtypes = [ctypes.c_int]
    loaded.HARDWARE_GetLastFault.restype = ctypes.c_int
    loaded.HARDWARE_TakePendingFault.restype = ctypes.c_int
    loaded.HARDWARE_ClearFault.argtypes = []
    return loaded


def test_register_wait_succeeds_when_mask_matches(hardware_library):
    register = ctypes.c_uint32(0xA5)

    assert hardware_library.HARDWARE_WaitForRegister(
        ctypes.byref(register), 0x0F, 0x05, 8
    )


def test_register_wait_times_out_for_stuck_peripheral(hardware_library):
    register = ctypes.c_uint32(0)

    assert not hardware_library.HARDWARE_WaitForRegister(
        ctypes.byref(register), 0x01, 0x01, 8
    )
    assert not hardware_library.HARDWARE_WaitForRegister(
        ctypes.byref(register), 0x01, 0x01, 0
    )


def test_fault_latch_preserves_diagnostics_and_consumes_pending_state(hardware_library):
    lib = hardware_library
    lib.HARDWARE_ClearFault()

    assert lib.HARDWARE_GetLastFault() == 0
    assert lib.HARDWARE_TakePendingFault() == 0

    lib.HARDWARE_ReportFault(4)
    assert lib.HARDWARE_GetLastFault() == 4
    assert lib.HARDWARE_TakePendingFault() == 4
    assert lib.HARDWARE_TakePendingFault() == 0
    assert lib.HARDWARE_GetLastFault() == 4
