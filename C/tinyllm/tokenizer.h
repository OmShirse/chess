// tokenizer.h — ASCII character-level tokenizer
// Token ID == ASCII code point (0-127).
// Printable range: 32 (' ') to 126 ('~'), plus newline (10).
// Tokens outside this range are mapped to '?' (63) on decode.
#pragma once
#include <stdint.h>

// Encode a single character to a token ID.
static inline int tok_encode(char c) {
    return (uint8_t)c & 0x7F;   // mask to 7-bit ASCII
}

// Decode a token ID back to a character.
static inline char tok_decode(int id) {
    if (id < 32 || id > 126) {
        if (id == 10) return '\n';
        return '?';
    }
    return (char)id;
}

// Encode a null-terminated string into token array.
// Returns number of tokens written (max = buf_len).
static inline int tok_encode_str(const char* s, int* buf, int buf_len) {
    int n = 0;
    while (*s && n < buf_len) {
        buf[n++] = tok_encode(*s++);
    }
    return n;
}
