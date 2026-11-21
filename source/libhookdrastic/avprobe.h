#ifndef DRASTIC_AVPROBE_H
#define DRASTIC_AVPROBE_H

#include "avprofile.h"

/* Inspect the original callback BEFORE installing DSplus's mute/profile wrappers.
 * Never infer private SPU layout from a wrapped callback or an unknown binary. */
static inline const char *AVProbe_configure(AVProfile *profile, uintptr_t base,
		const SDL_AudioSpec *original) {
	profile->ring_read = profile->ring_write = NULL;
	profile->known_delay_sites = 0;
	if (!profile->enabled) return "profiling-disabled";
	if (!base || !original || !original->userdata ||
		(uintptr_t)original->callback != base + 0x8c450) return "callback-mismatch";
	if (original->format != AUDIO_S16SYS) return "unsupported-audio-format";
	static const size_t offsets[] = {0x8c460, 0x8c470, 0x8c478, 0x8c484};
	static const uint32_t signatures[] = {0x91410016, 0x29414ec0, 0x12003e73, 0x54001283};
	for (size_t i = 0; i < sizeof(offsets) / sizeof(offsets[0]); i++) {
		uint32_t instruction;
		memcpy(&instruction, (const void *)(base + offsets[i]), sizeof(instruction));
		if (instruction != signatures[i]) return "instruction-mismatch";
	}
	profile->ring_read = (const uint32_t *)((const Uint8 *)original->userdata + 0x40008);
	profile->ring_write = (const uint32_t *)((const Uint8 *)original->userdata + 0x4000c);
	static const size_t delay_offsets[] = {0x88674, 0x89ff0, 0x8a000, 0x8a0e4, 0xee34, 0xeee0};
	static const uint32_t delay_signatures[] = {
		0x9400065f, 0x5289ba61, 0x17fe0e14, 0x97fe0ddb, 0x9401ec6f, 0x9401ec44
	};
	profile->known_delay_sites = 1;
	for (size_t i = 0; i < sizeof(delay_offsets) / sizeof(delay_offsets[0]); i++) {
		uint32_t instruction;
		memcpy(&instruction, (const void *)(base + delay_offsets[i]), sizeof(instruction));
		if (instruction != delay_signatures[i]) profile->known_delay_sites = 0;
	}
	return "enabled";
}

#endif
