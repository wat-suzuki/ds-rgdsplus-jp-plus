#!/bin/sh

# disable led
led off

# additional update logic
UPDATE_PATH=$SDCARD_PATH/system/update.sh
if [ -f $UPDATE_PATH ]; then
	$UPDATE_PATH
	rm $UPDATE_PATH
fi

# update bootlogo if changed
bootlogo $SDCARD_PATH && reboot

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
