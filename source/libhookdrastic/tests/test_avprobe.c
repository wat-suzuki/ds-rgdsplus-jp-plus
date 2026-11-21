#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "../avprobe.h"

static int callback_count;
static void callback(void *userdata, Uint8 *stream, int size) {
	assert(userdata == &callback_count);
	callback_count++;
	memset(stream, 0x5a, size);
}

int main(void) {
	AVProfile p;
	AVProfile_init(&p, 2);
	Uint8 *binary = calloc(1, 0x90000), *spu = calloc(1, 0x40010);
	assert(binary && spu);
	uintptr_t base = (uintptr_t)binary;
	SDL_AudioSpec original = {.callback=(SDL_AudioCallback)(base+0x8c450),
		.userdata=spu, .format=AUDIO_S16SYS, .channels=2, .freq=44100, .samples=1024};
	assert(strcmp(AVProbe_configure(&p, base, &original), "instruction-mismatch") == 0);
	assert(!p.ring_read && !p.known_delay_sites);
	const size_t offsets[] = {0x8c460,0x8c470,0x8c478,0x8c484,
		0x88674,0x89ff0,0x8a000,0x8a0e4,0xee34,0xeee0};
	const uint32_t instructions[] = {0x91410016,0x29414ec0,0x12003e73,0x54001283,
		0x9400065f,0x5289ba61,0x17fe0e14,0x97fe0ddb,0x9401ec6f,0x9401ec44};
	for (size_t i=0; i<sizeof(offsets)/sizeof(*offsets); i++)
		memcpy(binary+offsets[i], &instructions[i], 4);
	assert(strcmp(AVProbe_configure(&p, base, &original), "enabled") == 0);
	assert(p.ring_read == (const uint32_t *)(spu+0x40008) && p.known_delay_sites);
	binary[0xeee0] ^= 1;
	assert(strcmp(AVProbe_configure(&p, base, &original), "enabled") == 0);
	assert(p.ring_read && !p.known_delay_sites);
	SDL_AudioSpec wrapped = original;
	wrapped.callback = callback;
	assert(strcmp(AVProbe_configure(&p, base, &wrapped), "callback-mismatch") == 0);
	assert(!p.ring_read && !p.known_delay_sites);
	original.format = AUDIO_U8;
	assert(strcmp(AVProbe_configure(&p, base, &original), "unsupported-audio-format") == 0);
	assert(!p.ring_read);
	assert(strcmp(AVProbe_configure(&p, 0, NULL), "callback-mismatch") == 0);
	p.enabled = 0;
	assert(strcmp(AVProbe_configure(&p, base, &wrapped), "profiling-disabled") == 0);

	AVProfile_init(&p, 1);
	p.callback = callback;
	p.audio_userdata = &callback_count;
	Uint8 samples[16];
	AVProfile_audioSpec(&p, &wrapped);
	AVProfile_audioCallback(&p, samples, sizeof(samples));
	assert(p.callbacks == 1 && callback_count == 1);
	AVProfile_pauseAudio(&p, 1);
	AVProfile_audioCallback(&p, samples, sizeof(samples));
	assert(p.callbacks == 1 && callback_count == 2 && !p.last_audio);
	for (size_t i=0; i<sizeof(samples); i++) assert(samples[i] == 0x5a);
	AVProfile_pauseAudio(&p, 0);
	AVProfile_audioCallback(&p, samples, sizeof(samples));
	assert(p.callbacks == 2 && callback_count == 3 && !p.metrics[AV_AUDIO_GAP].count);
	/* Even a pause/resume too short for the audio thread to observe resets its gap. */
	AVProfile_pauseAudio(&p, 1); AVProfile_pauseAudio(&p, 0);
	AVProfile_audioCallback(&p, samples, sizeof(samples));
	assert(p.callbacks == 3 && !p.metrics[AV_AUDIO_GAP].count);
	free(binary); free(spu);
	puts("avprobe: original/wrapped callback validation, signature fallback, delay sites and pause epochs passed");
	return 0;
}
