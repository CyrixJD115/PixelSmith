#!/bin/sh
# Thin shell wrapper around build.py: ./build.sh --uv  ==  python3 build.py --uv
set -e
exec python3 "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/build.py" "$@"
