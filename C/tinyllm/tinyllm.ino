/*
  tinyllm.ino — Tiny character-level GPT on ESP32 Gen-1
  ======================================================
  Serial interface at 115200 baud.

  Commands (type into Serial Monitor, send with Enter):
    <any text>      — use as prompt, generate MAX_NEW_TOKENS characters
    temp:<float>    — set temperature   e.g. "temp:0.8"
    topk:<int>      — set top-k         e.g. "topk:5"
    ctx:reset       — clear KV cache
    help            — show this list

  Generated tokens stream back immediately, one char at a time.
  LED (GPIO2) blinks once per generated token.
*/

#include "config.h"
#include "transformer.h"
#include "tokenizer.h"
#include "sampler.h"
#include <string.h>
#include <stdlib.h>

// ── Globals ───────────────────────────────────────────────────────────────────
static KVCache kv_cache;                  // 64 KB KV cache in SRAM
static float   logits[VOCAB_SIZE];        // 512 bytes

static float g_temp  = 0.85f;            // default temperature
static int   g_top_k = 10;               // default top-k
static int   g_pos   = 0;               // current position in context

#define LED_PIN 2

// ── Helpers ───────────────────────────────────────────────────────────────────

void print_banner(void) {
    Serial.println();
    Serial.println(F("============================================"));
    Serial.println(F("   TinyLLM  |  ESP32 Gen-1  |  2-Layer GPT"));
    Serial.println(F("============================================"));
    Serial.printf( "   Model  : %d vocab, %d ctx, %d embd, %d layers\n",
                   VOCAB_SIZE, CTX_LEN, N_EMBD, N_LAYER);
    Serial.printf( "   Temp   : %.2f   TopK : %d\n", g_temp, g_top_k);
    Serial.println(F("   Type a prompt then press Enter."));
    Serial.println(F("   Commands: temp:<f>  topk:<n>  ctx:reset  help"));
    Serial.println(F("============================================"));
    Serial.println();
}

// Feed a prompt string token-by-token into the model (updates g_pos).
// Returns the last logits for the next predicted token.
void run_prompt(const char* prompt) {
    int n = strlen(prompt);
    for (int i = 0; i < n && g_pos < CTX_LEN; i++) {
        int tok = tok_encode(prompt[i]);
        llm_forward(tok, g_pos, &kv_cache, logits);
        g_pos++;
    }
}

// Generate `n_new` tokens and stream to Serial.
void generate(int n_new) {
    // Sample the first token from the last logits (already computed by run_prompt)
    for (int step = 0; step < n_new && g_pos < CTX_LEN; step++) {
        int next_tok = sampler_sample(logits, g_temp, g_top_k);
        char c = tok_decode(next_tok);
        Serial.print(c);

        // Blink LED
        digitalWrite(LED_PIN, HIGH);
        delayMicroseconds(500);
        digitalWrite(LED_PIN, LOW);

        // Forward pass for the generated token
        llm_forward(next_tok, g_pos, &kv_cache, logits);
        g_pos++;
    }
    Serial.println();

    if (g_pos >= CTX_LEN) {
        Serial.println(F("\n[Context full — type 'ctx:reset' to start over]"));
    }
}

// Parse and handle commands.
// Returns true if the input was a command, false if it was a prompt.
bool handle_command(const char* input) {
    if (strcmp(input, "help") == 0) {
        print_banner();
        return true;
    }
    if (strcmp(input, "ctx:reset") == 0) {
        llm_init(&kv_cache);
        g_pos = 0;
        Serial.println(F("[Context reset]"));
        return true;
    }
    if (strncmp(input, "temp:", 5) == 0) {
        float t = atof(input + 5);
        if (t > 0.0f && t <= 5.0f) {
            g_temp = t;
            Serial.printf("[Temperature set to %.2f]\n", g_temp);
        } else {
            Serial.println(F("[Invalid temp — use 0.01 .. 5.0]"));
        }
        return true;
    }
    if (strncmp(input, "topk:", 5) == 0) {
        int k = atoi(input + 5);
        if (k >= 0 && k <= VOCAB_SIZE) {
            g_top_k = k;
            Serial.printf("[Top-k set to %d]\n", g_top_k);
        } else {
            Serial.println(F("[Invalid top-k]"));
        }
        return true;
    }
    return false;
}

// ── Arduino entry points ──────────────────────────────────────────────────────

void setup() {
    Serial.begin(115200);
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    // Initialise KV cache
    llm_init(&kv_cache);

    // Wait for Serial Monitor
    while (!Serial && millis() < 3000) delay(10);

    print_banner();

    // Report free heap
    Serial.printf("[Free SRAM: %u bytes]\n\n", (unsigned)ESP.getFreeHeap());
}

void loop() {
    static char buf[CTX_LEN + 1];
    static int  buf_len = 0;

    // Read one character at a time
    while (Serial.available()) {
        char c = (char)Serial.read();

        if (c == '\r') continue;   // ignore CR

        if (c == '\n' || buf_len >= CTX_LEN) {
            buf[buf_len] = '\0';
            buf_len = 0;

            if (strlen(buf) == 0) continue;

            Serial.printf("\n> %s\n", buf);

            if (!handle_command(buf)) {
                // It's a prompt — run it then generate
                Serial.print(F("[Generating] "));
                unsigned long t0 = millis();

                run_prompt(buf);
                generate(MAX_NEW_TOKENS);

                unsigned long dt = millis() - t0;
                Serial.printf("[Done in %lu ms | pos=%d/%d]\n\n",
                              dt, g_pos, CTX_LEN);
            }
        } else {
            buf[buf_len++] = c;
        }
    }
}
