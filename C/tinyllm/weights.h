// weights.h — Q8-quantized model weights in Flash (PROGMEM)
// PLACEHOLDER: all weights zero-initialized.
// Run  python tools/train_export.py  to replace with trained weights.
//
// Each int8_t array is stored in Flash via PROGMEM.
// On ESP32 all Flash is directly addressable — no pgm_read needed.
#pragma once
#include <stdint.h>
#include <Arduino.h>   // for PROGMEM

// ── Scale factors (float32, one per tensor) ─────────────────────────────────
static const float W_SCALE_WTE  = 0.02f;

static const float W_SCALE_LN1_0 = 0.02f;
static const float W_SCALE_WQ_0  = 0.02f;
static const float W_SCALE_WK_0  = 0.02f;
static const float W_SCALE_WV_0  = 0.02f;
static const float W_SCALE_WO_0  = 0.02f;
static const float W_SCALE_LN2_0 = 0.02f;
static const float W_SCALE_W1_0  = 0.02f;
static const float W_SCALE_W2_0  = 0.02f;

static const float W_SCALE_LN1_1 = 0.02f;
static const float W_SCALE_WQ_1  = 0.02f;
static const float W_SCALE_WK_1  = 0.02f;
static const float W_SCALE_WV_1  = 0.02f;
static const float W_SCALE_WO_1  = 0.02f;
static const float W_SCALE_LN2_1 = 0.02f;
static const float W_SCALE_W1_1  = 0.02f;
static const float W_SCALE_W2_1  = 0.02f;

static const float W_SCALE_LNF  = 0.02f;

// ── Weight arrays (int8, PROGMEM) ────────────────────────────────────────────
// W_WTE  [8192]
static const int8_t PROGMEM W_WTE[8192] = {0};

// W_LN1_0  [64]
static const int8_t PROGMEM W_LN1_0[64] = {0};

// W_WQ_0  [4096]
static const int8_t PROGMEM W_WQ_0[4096] = {0};

// W_WK_0  [4096]
static const int8_t PROGMEM W_WK_0[4096] = {0};

// W_WV_0  [4096]
static const int8_t PROGMEM W_WV_0[4096] = {0};

// W_WO_0  [4096]
static const int8_t PROGMEM W_WO_0[4096] = {0};

// W_LN2_0  [64]
static const int8_t PROGMEM W_LN2_0[64] = {0};

// W_W1_0  [8192]
static const int8_t PROGMEM W_W1_0[8192] = {0};

// W_W2_0  [8192]
static const int8_t PROGMEM W_W2_0[8192] = {0};

// W_LN1_1  [64]
static const int8_t PROGMEM W_LN1_1[64] = {0};

// W_WQ_1  [4096]
static const int8_t PROGMEM W_WQ_1[4096] = {0};

// W_WK_1  [4096]
static const int8_t PROGMEM W_WK_1[4096] = {0};

// W_WV_1  [4096]
static const int8_t PROGMEM W_WV_1[4096] = {0};

// W_WO_1  [4096]
static const int8_t PROGMEM W_WO_1[4096] = {0};

// W_LN2_1  [64]
static const int8_t PROGMEM W_LN2_1[64] = {0};

// W_W1_1  [8192]
static const int8_t PROGMEM W_W1_1[8192] = {0};

// W_W2_1  [8192]
static const int8_t PROGMEM W_W2_1[8192] = {0};

// W_LNF  [64]
static const int8_t PROGMEM W_LNF[64] = {0};

// ── Pointer tables for layer-indexed access ──────────────────────────────────
static const int8_t* const W_LN1[2]  = {W_LN1_0,  W_LN1_1};
static const float         W_SCALE_LN1[2] = {W_SCALE_LN1_0, W_SCALE_LN1_1};
static const int8_t* const W_WQ[2]   = {W_WQ_0,   W_WQ_1};
static const float         W_SCALE_WQ[2]  = {W_SCALE_WQ_0,  W_SCALE_WQ_1};
static const int8_t* const W_WK[2]   = {W_WK_0,   W_WK_1};
static const float         W_SCALE_WK[2]  = {W_SCALE_WK_0,  W_SCALE_WK_1};
static const int8_t* const W_WV[2]   = {W_WV_0,   W_WV_1};
static const float         W_SCALE_WV[2]  = {W_SCALE_WV_0,  W_SCALE_WV_1};
static const int8_t* const W_WO[2]   = {W_WO_0,   W_WO_1};
static const float         W_SCALE_WO[2]  = {W_SCALE_WO_0,  W_SCALE_WO_1};
static const int8_t* const W_LN2[2]  = {W_LN2_0,  W_LN2_1};
static const float         W_SCALE_LN2[2] = {W_SCALE_LN2_0, W_SCALE_LN2_1};
static const int8_t* const W_W1[2]   = {W_W1_0,   W_W1_1};
static const float         W_SCALE_W1[2]  = {W_SCALE_W1_0,  W_SCALE_W1_1};
static const int8_t* const W_W2[2]   = {W_W2_0,   W_W2_1};
static const float         W_SCALE_W2[2]  = {W_SCALE_W2_0,  W_SCALE_W2_1};

