#!/bin/sh

: "${SDCARD_PATH:?Set SDCARD_PATH to the SD card root}"
DIR="$SDCARD_PATH/system/drastic"
LIB="$SDCARD_PATH/system/lib"

cd "$DIR" || exit 1
export HOME="$DIR"

if [ "${DRASTIC_LOG:-0}" = 1 ]; then
	# Preserve diagnostic logs across game switches and automatic Hi-Res restarts.
	LOG_DIR="$SDCARD_PATH/userdata/logs"
	LOG_FILE=/tmp/drastic.txt
	if mkdir -p "$LOG_DIR"; then
		log_prefix="$LOG_DIR/drastic-$(date +%Y%m%d-%H%M%S)-$$"
		log_candidate="$log_prefix.log"
		log_index=0
		while :; do
			if (set -C; : > "$log_candidate") 2>/dev/null; then
				LOG_FILE="$log_candidate"
				break
			fi
			[ -e "$log_candidate" ] || break
			[ -w "$log_candidate" ] || break
			log_index=$((log_index + 1))
			log_candidate="$log_prefix-$log_index.log"
		done
	fi
	# A convenience pointer for `make log`; failure must not prevent startup.
	printf '%s\n' "$LOG_FILE" > /tmp/drastic-log-path 2>/dev/null || :
	{
		printf 'Launcher: renderer=XGL DRASTIC_PROFILE=%s DRASTIC_PRESENT_ORDER=%s DRASTIC_DRM_OVERLAY=%s log=%s\n' \
			"${DRASTIC_PROFILE:-0}" "${DRASTIC_PRESENT_ORDER:-batched}" \
			"${DRASTIC_DRM_OVERLAY:-0}" "$LOG_FILE"
		LD_PRELOAD="$LIB/libhookdrastic.so" ./drastic
	} > "$LOG_FILE" 2>&1
else
	LD_PRELOAD="$LIB/libhookdrastic.so" ./drastic >/dev/null 2>&1
fi
