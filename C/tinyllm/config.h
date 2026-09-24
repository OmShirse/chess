// config.h — TinyLLM hyperparameters
// All sizes chosen to fit within ESP32 Gen-1 SRAM/Flash budget.
// Changing these requires re-running tools/train_export.py.
#pragma once

// ── Vocabulary ────────────────────────────────────────────────────────────────
// Character-level, full printable ASCII. Token ID == ASCII code point.
#define VOCAB_SIZE   128

// ── Sequence length ───────────────────────────────────────────────────────────
#define CTX_LEN       64   // max tokens in context window

// ── Model dimensions ──────────────────────────────────────────────────────────
#define N_EMBD        64   // embedding / hidden dim
#define N_LAYER        2   // transformer blocks
#define N_HEAD         2   // attention heads
#define HEAD_DIM      32   // N_EMBD / N_HEAD
#define FFN_DIM      128   // feed-forward hidden dim (2x N_EMBD)

// ── Generation ────────────────────────────────────────────────────────────────
#define MAX_NEW_TOKENS 200

// ── Memory estimate (informational) ──────────────────────────────────────────
// KV cache   : 2 * N_LAYER * CTX_LEN * N_EMBD * 4 =  65 536 B (~64 KB)
// Activations: ~4 KB scratch
// Weights    : ~74 KB in Flash (Q8 quantized)
