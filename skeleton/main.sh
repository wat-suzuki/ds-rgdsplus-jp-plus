#!/bin/sh

SDCARD_PATH=$(CDPATH= cd "$(dirname "$0")" && pwd) || exit 1
export SDCARD_PATH
export PATH="$SDCARD_PATH/system/bin:$PATH"
export LD_LIBRARY_PATH="$SDCARD_PATH/system/lib:$LD_LIBRARY_PATH"
export DRASTIC_PROFILE="${DRASTIC_PROFILE:-0}"
export DRASTIC_PRESENT_ORDER="${DRASTIC_PRESENT_ORDER:-batched}"
export DRASTIC_DRM_OVERLAY="${DRASTIC_DRM_OVERLAY:-1}"

# update
if [ -f "$SDCARD_PATH/system.zip" ]; then
	cd "$SDCARD_PATH" || exit 1
	rm -rf system
	unzip -q system.zip
	rm -f system.zip
fi

# loop
"$SDCARD_PATH/system/loop.sh"
