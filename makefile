.PHONY: build package-fonts

BUILD_HASH:=$(shell git rev-parse --short HEAD)
RELEASE_DIRT:=$(if $(shell git status --porcelain; git log @{upstream}..HEAD --oneline),-dirty,)
RELEASE_TIME:=$(shell TZ=GMT date +%Y%m%d)
RELEASE_BASE=ds-rgdsplus-jp-plus-$(RELEASE_TIME)
RELEASE_DOT:=$(shell find ./releases/. -regex ".*/${RELEASE_BASE}-[0-9]+\(-dirty\)?\.zip" 2>/dev/null | wc -l | sed 's/ //g')
RELEASE_NAME=$(RELEASE_BASE)-$(RELEASE_DOT)$(RELEASE_DIRT)

all: setup build package done

setup:
	@echo "building $(RELEASE_NAME)..."
	tty -s # make sure we're running in an input device
	rm -rf ./build
	mkdir -p ./releases
	cp -R ./skeleton ./build
	cd ./build && find . -type f -name '.keep' -delete

build:
	cd source/libhookdrastic && make
	
package-fonts:
	mkdir -p ./build/system/assets ./build/system/lib
	cp fonts/NotoSansJP-Bold.ttf ./build/system/assets/font.ttf
	cp fonts/OFL.txt ./build/system/assets/OFL.txt
	@set -e; \
		ttf_libdir="$$(pkg-config --variable=libdir SDL2_ttf)"; \
		ttf_lib="$$ttf_libdir/libSDL2_ttf-2.0.so.0"; \
		test -f "$$ttf_lib" || { printf '%s\n' 'SDL2_ttf runtime is missing; install SDL2_ttf in the aarch64 toolchain.' >&2; exit 1; }; \
		cp -L "$$ttf_lib" ./build/system/lib/libSDL2_ttf-2.0.so.0; \
		ldd "$$ttf_lib" | while read -r soname arrow path rest; do \
			[ "$$arrow" = "=>" ] || continue; \
			[ "$$path" != "not" ] || { printf 'Missing SDL2_ttf dependency: %s\n' "$$soname" >&2; exit 1; }; \
			case "$$path" in /*) ;; *) continue ;; esac; \
			case "$$soname" in libSDL2-2.0.so.0|libc.so.*|libm.so.*|libpthread.so.*|libdl.so.*|librt.so.*|libgcc_s.so.*|ld-linux-aarch64.so.*) continue ;; esac; \
			cp -L "$$path" "./build/system/lib/$$soname"; \
		done

package: package-fonts
	cp source/libhookdrastic/libhookdrastic.so ./build/system/lib/
	cd ./build/system && echo "$(RELEASE_NAME)\n$(BUILD_HASH)" > version.txt
	cd ./build && find . -type f -name '.DS_Store' -delete
	cd ./build && zip -r system.zip system && rm -rf system
	cd ./build && zip -r ../releases/$(RELEASE_NAME).zip .

done:
	@echo "$(RELEASE_NAME) done!"
	say "done" 2>/dev/null || true
