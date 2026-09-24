// transformer.cpp — TinyLLM inference engine for ESP32
// Architecture: 2-layer character-level GPT with RoPE, RMSNorm, GELU, Q8 weights.
// All weight tensors live in Flash (PROGMEM). Activations and KV cache in SRAM.

#include "transformer.h"
#include "weights.h"
#include "config.h"
#include <string.h>
#include <math.h>

// ── Static scratch buffers (avoid stack pressure) ────────────────────────────
// Total scratch: ~4 KB
static float s_x   [N_EMBD];      // current hidden state
static float s_xb  [N_EMBD];      // post-norm scratch
static float s_xb2 [N_EMBD];      // attention output scratch
static float s_q   [N_EMBD];      // query
static float s_k   [N_EMBD];      // key  (current token)
static float s_v   [N_EMBD];      // value (current token)
static float s_hb  [FFN_DIM];     // FFN hidden buffer
static float s_attn[CTX_LEN];     // attention scores (one head at a time)

// ── Math primitives ───────────────────────────────────────────────────────────

// Root-Mean-Square normalisation.
// w is Q8 in Flash; scale converts int8 → float32.
static void rmsnorm(float* __restrict__ out,
                    const float* __restrict__ x,
                    const int8_t* w, float w_scale, int size) {
    float ss = 0.0f;
    for (int i = 0; i < size; i++) ss += x[i] * x[i];
    ss = 1.0f / sqrtf(ss / (float)size + 1e-5f);
    for (int i = 0; i < size; i++)
        out[i] = ss * x[i] * ((float)w[i] * w_scale);
}

// Numerically-stable softmax over x[0..n-1] in-place.
static void softmax(float* x, int n) {
    float mx = x[0];
    for (int i = 1; i < n; i++) if (x[i] > mx) mx = x[i];
    float sum = 0.0f;
    for (int i = 0; i < n; i++) { x[i] = expf(x[i] - mx); sum += x[i]; }
    float inv = 1.0f / sum;
    for (int i = 0; i < n; i++) x[i] *= inv;
}

// Q8 matrix-vector multiply: out[o] = sum_i(x[i] * W[o,i]) * scale
// W is stored row-major in Flash as int8.
static void q8_mv(float* __restrict__ out,
                  const float* __restrict__ x,
                  const int8_t* W, float scale,
                  int out_dim, int in_dim) {
    for (int o = 0; o < out_dim; o++) {
        float acc = 0.0f;
        const int8_t* row = W + (int32_t)o * in_dim;
        for (int i = 0; i < in_dim; i++)
            acc += x[i] * (float)row[i];
        out[o] = acc * scale;
    }
}

// GELU activation (tanh approximation).
static inline float gelu(float x) {
    const float c = 0.7978845608028654f;   // sqrt(2/pi)
    float inner = c * (x + 0.044715f * x * x * x);
    return 0.5f * x * (1.0f + tanhf(inner));
}

// Rotary Position Embedding applied to a single vector in-place.
// head_dim must be even.
static void rope(float* vec, int pos, int head_dim) {
    for (int i = 0; i < head_dim; i += 2) {
        float freq  = 1.0f / powf(10000.0f, (float)i / (float)head_dim);
        float angle = (float)pos * freq;
        float c = cosf(angle), s = sinf(angle);
        float v0 = vec[i], v1 = vec[i + 1];
        vec[i]     = v0 * c - v1 * s;
        vec[i + 1] = v0 * s + v1 * c;
    }
}

// ── Public API ────────────────────────────────────────────────────────────────

void llm_init(KVCache* kv) {
    memset(kv, 0, sizeof(KVCache));
}

void llm_forward(int token, int pos, KVCache* kv, float* logits) {
    // 1. Token embedding lookup (row `token` from wte)
    const int8_t* emb_row = W_WTE + (int32_t)token * N_EMBD;
    for (int i = 0; i < N_EMBD; i++)
        s_x[i] = (float)emb_row[i] * W_SCALE_WTE;

    // 2. Transformer blocks
    for (int l = 0; l < N_LAYER; l++) {
        // ── Attention block ───────────────────────────────────────────────────

        // RMSNorm #1
        rmsnorm(s_xb, s_x, W_LN1[l], W_SCALE_LN1[l], N_EMBD);

        // Q, K, V projections
        q8_mv(s_q, s_xb, W_WQ[l], W_SCALE_WQ[l], N_EMBD, N_EMBD);
        q8_mv(s_k, s_xb, W_WK[l], W_SCALE_WK[l], N_EMBD, N_EMBD);
        q8_mv(s_v, s_xb, W_WV[l], W_SCALE_WV[l], N_EMBD, N_EMBD);

        // Apply RoPE to each head's Q and K slice
        for (int h = 0; h < N_HEAD; h++) {
            rope(s_q + h * HEAD_DIM, pos, HEAD_DIM);
            rope(s_k + h * HEAD_DIM, pos, HEAD_DIM);
        }

        // Store current K, V into the cache
        memcpy(kv->k[l][pos], s_k, N_EMBD * sizeof(float));
        memcpy(kv->v[l][pos], s_v, N_EMBD * sizeof(float));

        // Multi-head causal self-attention
        memset(s_xb2, 0, sizeof(s_xb2));
        const float scale = 1.0f / sqrtf((float)HEAD_DIM);

        for (int h = 0; h < N_HEAD; h++) {
            const float* q_h  = s_q + h * HEAD_DIM;
            float*       out_h = s_xb2 + h * HEAD_DIM;

            // Attention scores over all past tokens (causal: t <= pos)
            for (int t = 0; t <= pos; t++) {
                const float* k_t = kv->k[l][t] + h * HEAD_DIM;
                float dot = 0.0f;
                for (int i = 0; i < HEAD_DIM; i++) dot += q_h[i] * k_t[i];
                s_attn[t] = dot * scale;
            }
            softmax(s_attn, pos + 1);

            // Weighted sum of V
            for (int t = 0; t <= pos; t++) {
                const float* v_t = kv->v[l][t] + h * HEAD_DIM;
                float a = s_attn[t];
                for (int i = 0; i < HEAD_DIM; i++) out_h[i] += a * v_t[i];
            }
        }

        // Output projection + residual connection
        q8_mv(s_xb, s_xb2, W_WO[l], W_SCALE_WO[l], N_EMBD, N_EMBD);
        for (int i = 0; i < N_EMBD; i++) s_x[i] += s_xb[i];

        // ── FFN block ─────────────────────────────────────────────────────────

        // RMSNorm #2
        rmsnorm(s_xb, s_x, W_LN2[l], W_SCALE_LN2[l], N_EMBD);

        // W1 (expand) → GELU → W2 (project) → residual
        q8_mv(s_hb, s_xb, W_W1[l], W_SCALE_W1[l], FFN_DIM, N_EMBD);
        for (int i = 0; i < FFN_DIM; i++) s_hb[i] = gelu(s_hb[i]);
        q8_mv(s_xb, s_hb, W_W2[l], W_SCALE_W2[l], N_EMBD, FFN_DIM);
        for (int i = 0; i < N_EMBD; i++) s_x[i] += s_xb[i];
    }

    // 3. Final RMSNorm
    rmsnorm(s_x, s_x, W_LNF, W_SCALE_LNF, N_EMBD);

    // 4. LM head (weight-tied to wte): logits = s_x @ wte.T
    // Out dim = VOCAB_SIZE, in dim = N_EMBD
    q8_mv(logits, s_x, W_WTE, W_SCALE_WTE, VOCAB_SIZE, N_EMBD);
}
