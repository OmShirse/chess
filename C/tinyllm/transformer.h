// transformer.h — Tiny GPT inference engine (public API)
#pragma once
#include "config.h"
#include <stdint.h>

// ── KV cache (lives in SRAM, allocated by caller) ─────────────────────────────
// Size: 2 * N_LAYER * CTX_LEN * N_EMBD * 4 = 65 536 bytes
typedef struct {
    float k[N_LAYER][CTX_LEN][N_EMBD];
    float v[N_LAYER][CTX_LEN][N_EMBD];
} KVCache;

// Initialise / zero-out the KV cache.
void llm_init(KVCache* kv);

// Run a single forward pass for one token at position `pos`.
// - `token`  : integer token ID (0..VOCAB_SIZE-1)
// - `pos`    : position in sequence (0..CTX_LEN-1)
// - `kv`     : KV cache (must persist across calls for one generation)
// - `logits` : output buffer [VOCAB_SIZE] — caller allocates
void llm_forward(int token, int pos, KVCache* kv, float* logits);
