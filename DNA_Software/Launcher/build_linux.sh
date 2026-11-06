#!/bin/sh
# Build the Linux release zip on Linux. Windows uses build.ps1.
set -eu
HERE=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$HERE/release_tools.py" --target linux
