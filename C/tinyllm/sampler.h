// sampler.h — Temperature + Top-K sampling using ESP32 hardware RNG
#pragma once
#include "config.h"
#include <math.h>
#include <esp_random.h>

// Draw a uniform float in [0, 1) from the hardware RNG.
static inline float rand_f32(void) {
    return (float)(esp_random() >> 8) / (float)(1 << 24);
}

// Apply temperature scaling in-place.
static inline void sampler_apply_temp(float* logits, int n, float temp) {
    if (temp <= 0.0f) temp = 1e-6f;
    for (int i = 0; i < n; i++) logits[i] /= temp;
}

// Softmax in-place (numerically stable).
static inline void sampler_softmax(float* x, int n) {
    float max = x[0];
    for (int i = 1; i < n; i++) if (x[i] > max) max = x[i];
    float sum = 0.0f;
    for (int i = 0; i < n; i++) { x[i] = expf(x[i] - max); sum += x[i]; }
    for (int i = 0; i < n; i++) x[i] /= sum;
}

// Comparison helper for qsort (descending probability).
typedef struct { float p; int idx; } ProbIdx;
static int _cmp_desc(const void* a, const void* b) {
    float da = ((ProbIdx*)a)->p, db = ((ProbIdx*)b)->p;
    return (da < db) - (da > db);
}

// Sample from logits using temperature and top-k.
// temp=1.0 is neutral; top_k=0 means no top-k cutoff (pure sampling).
// Returns the sampled token ID.
static inline int sampler_sample(float* logits, float temp, int top_k) {
    // Apply temperature
    sampler_apply_temp(logits, VOCAB_SIZE, temp);
    sampler_softmax(logits, VOCAB_SIZE);

    // Build sorted index array for top-k
    static ProbIdx pi[VOCAB_SIZE];
    for (int i = 0; i < VOCAB_SIZE; i++) { pi[i].p = logits[i]; pi[i].idx = i; }

    int k = (top_k > 0 && top_k < VOCAB_SIZE) ? top_k : VOCAB_SIZE;
    // Partial sort — find top-k by simple selection (k is small)
    for (int i = 0; i < k; i++) {
        int best = i;
        for (int j = i+1; j < VOCAB_SIZE; j++)
            if (pi[j].p > pi[best].p) best = j;
        ProbIdx tmp = pi[i]; pi[i] = pi[best]; pi[best] = tmp;
    }

    // Re-normalise over top-k
    float sum = 0.0f;
    for (int i = 0; i < k; i++) sum += pi[i].p;

    // Draw from hardware RNG
    float r = rand_f32() * sum;
    float cum = 0.0f;
    for (int i = 0; i < k; i++) {
        cum += pi[i].p;
        if (r <= cum) return pi[i].idx;
    }
    return pi[k-1].idx;   // fallback
}

// Greedy (argmax) decode — fast, deterministic.
static inline int sampler_argmax(const float* logits) {
    int best = 0;
    for (int i = 1; i < VOCAB_SIZE; i++)
        if (logits[i] > logits[best]) best = i;
    return best;
}
