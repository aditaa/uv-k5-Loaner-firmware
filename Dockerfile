FROM archlinux:latest

ARG TOOLCHAIN_VERSION=10.3-2021.10
ARG TOOLCHAIN_ARCHIVE=gcc-arm-none-eabi-${TOOLCHAIN_VERSION}-x86_64-linux.tar.bz2
ARG TOOLCHAIN_URL="https://developer.arm.com/-/media/Files/downloads/gnu-rm/${TOOLCHAIN_VERSION}/${TOOLCHAIN_ARCHIVE}?rev=78196d3461ba4c9089a67b5f33edf82a&revision=78196d34-61ba-4c90-89a6-7b5f33edf82a&hash=B94A380A17942218223CD08320496FB1"

RUN pacman -Syyu --noconfirm \
    base-devel \
    git \
    python-pip \
    python-crcmod \
    python-pytest \
    cppcheck \
    ca-certificates \
    curl \
    tar

RUN curl -L "${TOOLCHAIN_URL}" -o "/tmp/${TOOLCHAIN_ARCHIVE}" \
    && tar -xjf "/tmp/${TOOLCHAIN_ARCHIVE}" -C /opt \
    && rm "/tmp/${TOOLCHAIN_ARCHIVE}"

ENV PATH="/opt/gcc-arm-none-eabi-${TOOLCHAIN_VERSION}/bin:${PATH}"

WORKDIR /app
COPY . .

RUN git submodule update --init --recursive
