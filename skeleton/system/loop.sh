#!/bin/sh

# disable led
led off

# additional update logic
UPDATE_PATH=$SDCARD_PATH/system/update.sh
if [ -f $UPDATE_PATH ]; then
	$UPDATE_PATH
	rm $UPDATE_PATH
fi

# Update the FIT boot logos when the BMP files on the SD card have changed.
# Keep a report on the SD card so resource-tool failures are visible in Windows.
BOOTLOGO_LOG="$SDCARD_PATH/userdata/logs/bootlogo-update.log"
mkdir -p "$(dirname "$BOOTLOGO_LOG")"
BOOTLOGO_STATUS=127
{
	echo "bootlogo update: $(date)"
	echo "SDCARD_PATH=$SDCARD_PATH"
	for tool in bootlogo dumpimage fdtget rsce_tool; do
		printf '%s=' "$tool"
		command -v "$tool" || true
	done
	for logo in bootlogo-0.bmp bootlogo-1.bmp; do
		if [ -f "$SDCARD_PATH/$logo" ]; then md5sum "$SDCARD_PATH/$logo"; else echo "missing $SDCARD_PATH/$logo"; fi
	done
	bootlogo "$SDCARD_PATH"
	BOOTLOGO_STATUS=$?
	echo "bootlogo exit status=$BOOTLOGO_STATUS"
	sync
} > "$BOOTLOGO_LOG" 2>&1
if [ "$BOOTLOGO_STATUS" -eq 0 ]; then reboot; fi

# drastic
EXEC_LOOP=/tmp/exec_loop
touch $EXEC_LOOP
while [ -f $EXEC_LOOP ]; do
	$SDCARD_PATH/system/run.sh
	sync
done

# reenable led and say goodnight
led on
shutdown
