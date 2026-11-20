#!/bin/sh
set -e

# migrate old style states and screenshots
{
	STATES_PATH=$SDCARD_PATH/userdata/states
	SHOTS_PATH=$SDCARD_PATH/userdata/screenshots
	SNAPS_PATH=$SDCARD_PATH/userdata/snaps

	mkdir -p "$SNAPS_PATH"

	SLOT=0
	for STATE_PATH in "$STATES_PATH"/*.st0; do
		[ -f "$STATE_PATH" ] || continue
	
		GAME_NAME=${STATE_PATH##*/}
		GAME_NAME=${GAME_NAME%.st0}
		GAME_PATH=$STATES_PATH/$GAME_NAME
		SNAP_PATH=$SNAPS_PATH/$GAME_NAME

		mkdir -p "$GAME_PATH" "$SNAP_PATH"
		cp -p "$STATE_PATH" "$GAME_PATH/$SLOT.dss"
	
		for SCREEN in 0 1; do
			SRC_PATH="$SHOTS_PATH/$GAME_NAME-$SCREEN.bmp"
			DST_PATH="$SNAP_PATH/$SLOT-$SCREEN.bmp"
			if [ -f "$SRC_PATH" ]; then
				mv "$SRC_PATH" "$DST_PATH"
			fi
		done
		rm "$STATE_PATH"
	done
	rm -rf "$SHOTS_PATH"
}
