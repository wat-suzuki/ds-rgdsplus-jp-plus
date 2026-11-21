#ifndef DRASTIC_UTF8_H
#define DRASTIC_UTF8_H

#include <stddef.h>
#include <stdint.h>

/* Invalid/truncated sequences consume one byte, never a byte beyond NUL. */
static inline size_t UTF8_charBytes(const unsigned char *p) {
	size_t length;
	if (*p >= 0xc2 && *p <= 0xdf) length = 2;
	else if (*p >= 0xe0 && *p <= 0xef) length = 3;
	else if (*p >= 0xf0 && *p <= 0xf4) length = 4;
	else return 1;
	for (size_t i = 1; i < length; i++)
		if ((p[i] & 0xc0) != 0x80) return 1;
	if ((*p == 0xe0 && p[1] < 0xa0) || (*p == 0xed && p[1] >= 0xa0) ||
		(*p == 0xf0 && p[1] < 0x90) || (*p == 0xf4 && p[1] >= 0x90)) return 1;
	return length;
}

static inline uint32_t UTF8_next(const char **text) {
	const unsigned char *p = (const unsigned char *)*text;
	size_t length = UTF8_charBytes(p);
	uint32_t value = p[0];
	if (length > 1) {
		value &= (1u << (7 - length)) - 1;
		for (size_t i = 1; i < length; i++) value = (value << 6) | (p[i] & 0x3f);
	}
	*text += length;
	return value;
}

#endif
