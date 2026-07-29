# Firmware feature inventory

This inventory separates the behavior shipped in the default loaner image from
optional source retained for upstream compatibility. A disabled `ENABLE_*`
option is not linked into the default image unless the table says otherwise.

| Feature family | Default image | Repository decision | Reason |
| --- | --- | --- | --- |
| UART and CHIRP programming | Enabled and linked | Retain | Required to program and clone the loaner channel plan. |
| Channel and CSS scanning | Linked | Retain | Used to find active channels and tones in the field. |
| Boot-time maintenance menu | Linked | Retain | Holding Side 1 during boot exposes service and frequency-lock settings. The normal Menu-key entry remains blocked. |
| DTMF signaling | Linked | Retain | Supports interoperability workflows; removal would need a separate product decision and radio tests. |
| Voice prompts and battery/RSSI UI | Linked | Retain | Supports loaner usability and field diagnostics. |
| Aircopy | `ENABLE_AIRCOPY=0`; app/UI objects are not linked | Retain optional source | No default firmware-size cost, while retaining an upstream-compatible option. |
| FM broadcast receiver | `ENABLE_FMRADIO=0`; app/UI/driver objects are not linked | Retain optional source | No default firmware-size cost, while retaining an upstream-compatible option. |
| NOAA mode | `ENABLE_NOAA=0`; guarded paths are compiled out | Retain optional source | Disabled in the default loaner image; source deletion would not reduce that image. |
| Alarm and optional 1750-Hz feature paths | `ENABLE_ALARM=0`, `ENABLE_TX1750=0`; guarded paths are compiled out | Retain optional source | Disabled in the default loaner image; interoperability behavior should not be removed as mechanical cleanup. |
| SRAM overlay | `ENABLE_OVERLAY=0`; overlay/flash objects are not linked | Retain optional source | Avoids the overlay complexity in the default image without making upstream merges harder. |
| SWD support | `ENABLE_SWD=0`; guarded support is compiled out | Retain optional source | Not needed in release images, but useful for development builds. |

## Cleanup rule

Delete code only when its path is demonstrably unreachable or a separately
approved feature-removal issue defines the user impact and hardware validation.
Do not delete optional source merely to reduce repository file count: the
linker already excludes disabled object files and guarded paths from the
default image.

The normal key dispatcher rejects `KEY_MENU` before `MAIN_ProcessKeys`, so the
old main-screen Menu handler and its switch arm were unreachable. Side-key
events are handled by `ACTION_Handle` before the same dispatcher, so its legacy
side-key remap was also ineffective. Those leftovers were removed without
changing the boot-time maintenance menu or side-key behavior.
