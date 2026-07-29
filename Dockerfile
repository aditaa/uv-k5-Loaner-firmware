# linux/amd64 image published 2026-07-27. Update this digest and the
# ARCH_REPOSITORY_DATE together; see ci/dependencies.md.
FROM archlinux:base-devel@sha256:33c534be6c990710a878b37192904dd448e162ade06a201d95a80b42be2110c7

ARG ARCH_REPOSITORY_DATE=2026/07/28
ARG TOOLCHAIN_VERSION=10.3-2021.10

COPY ci/container-packages.txt /tmp/container-packages.txt

RUN printf 'Server = https://archive.archlinux.org/repos/%s/$repo/os/$arch\n' \
        "${ARCH_REPOSITORY_DATE}" > /etc/pacman.d/mirrorlist \
    && pacman -Syyu --noconfirm --needed \
        $(grep -Ev '^[[:space:]]*(#|$)' /tmp/container-packages.txt) \
    && pacman -Scc --noconfirm

COPY ci/requirements-ci.txt /tmp/requirements-ci.txt

RUN python -m pip install --break-system-packages --disable-pip-version-check \
        --no-cache-dir -r /tmp/requirements-ci.txt

COPY ci/install-arm-toolchain.sh ci/gcc-arm-none-eabi-10.3-2021.10.sha256 /tmp/toolchain/

RUN bash /tmp/toolchain/install-arm-toolchain.sh /opt

ENV BUILD_CONTAINER_BASE="archlinux:base-devel@sha256:33c534be6c990710a878b37192904dd448e162ade06a201d95a80b42be2110c7" \
    BUILD_PACKAGE_SNAPSHOT="${ARCH_REPOSITORY_DATE}" \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH="/opt/gcc-arm-none-eabi-${TOOLCHAIN_VERSION}/bin:${PATH}" \
    TZ=UTC

WORKDIR /app
COPY . .
