## Summary

<!-- What changed, why, and which firmware areas are affected? -->

Closes #

## Release impact

- [ ] No user-visible or release impact
- [ ] User-visible behavior changed; release notes are needed
- [ ] Release-blocking fix
- [ ] EEPROM, UART/CHIRP, packed metadata, or version compatibility changed

## Firmware size

<!-- Run a clean ARM build. Use N/A only for documentation-only changes. -->

| Measurement | Bytes |
| --- | ---: |
| Before | |
| After | |
| Delta | |

## Validation

- [ ] `pytest -q`
- [ ] changed-line clang-format check
- [ ] cppcheck
- [ ] clean ARM build
- [ ] two-build reproducibility check
- [ ] CHIRP compatibility checked, or not affected

## Hardware validation

- [ ] Hardware is not required for this change
- [ ] Hardware testing completed and results are included below
- [ ] Hardware testing is still required and is tracked in issue #

<!-- Radio model, test steps, expected/actual results, RF observations, logs, or screenshots. -->

## Checklist

- [ ] The PR is focused and linked to its issue
- [ ] New or changed behavior is documented
- [ ] Optional `ENABLE_*` configurations touched by this change still build
- [ ] I reviewed the [contributor guide](../CONTRIBUTING.md) and [release checklist](../docs/release-checklist.md)
