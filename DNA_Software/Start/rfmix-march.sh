#!/bin/sh
# RFMix v2.03-r0 (09599c19) appends -march=core2 in Makefile.am.
# AArch64 GCC rejects that value. x64 keeps the upstream flag.
# ARM64 uses the compiler default for the image (armv8-a on Debian arm64).
# Do not add SVE, crypto, or other optional extensions here.
# Run this script from the unpacked source directory, before autoreconf.
set -eu
arch=$(dpkg --print-architecture 2>/dev/null || uname -m)
case "$arch" in
  amd64|x86_64) ;;
  arm64|aarch64)
    # Redirect instead of sed -i so GNU sed and BSD sed both update the file.
    edited=$(mktemp)
    sed 's/ -march=core2//g' Makefile.am > "$edited"
    mv "$edited" Makefile.am
    ;;
  *)
    printf 'RFMix build supports amd64 and arm64 only: %s\n' "$arch" >&2
    exit 1
    ;;
esac
if grep -q -- '-march=core2' Makefile.am; then
  case "$arch" in
    amd64|x86_64) ;;
    *) exit 1 ;;
  esac
else
  case "$arch" in
    arm64|aarch64) ;;
    *) exit 1 ;;
  esac
fi
