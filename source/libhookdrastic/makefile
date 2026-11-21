ifeq (,$(CROSS_COMPILE))
$(error missing CROSS_COMPILE for this toolchain)
endif

TARGET=libhookdrastic

REMOTE_ADDR=192.168.7.148
# REMOTE_PATH=/mnt/mmc/system/lib
REMOTE_PATH=/mnt/sdcard/system/lib
REMOTE_DISK=root@$(REMOTE_ADDR)

SSH := sshpass -p root ssh $(REMOTE_DISK)
SCP := sshpass -p root scp

all: build
auth:
	ssh $(REMOTE_DISK) exit
build:
	$(CROSS_COMPILE)gcc $(CPPFLAGS) $(CFLAGS) $(TARGET).c xgl.c -o $(TARGET).so -I/usr/include/libdrm -shared -lSDL2_image -lSDL2 -lGLESv2 -ldrm -lasound -ldl -lpthread -fPIC -O2 $(LDFLAGS)
upload: build
	$(SCP) "$(TARGET).so" "$(REMOTE_DISK):$(REMOTE_PATH)/$(TARGET).so"
	$(SSH) "killall -s kill drastic"
log:
	$(SSH) 'log_file=/tmp/drastic.txt; if [ -r /tmp/drastic-log-path ]; then IFS= read -r log_file < /tmp/drastic-log-path; fi; cat "$$log_file"'
grab:
	$(SCP) "$(REMOTE_DISK):/tmp/capture-game.bmp" . >/dev/null 2>&1 || true
	$(SCP) "$(REMOTE_DISK):/tmp/capture-menu.bmp" . >/dev/null 2>&1 || true
clean:
	rm -rf capture-*.bmp
	rm -rf $(TARGET).so
