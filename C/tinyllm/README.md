# TinyLLM — Character-level GPT on ESP32 Gen 1

A 2-layer transformer that runs fully on the ESP32 (no cloud, no extra RAM).
Weights are Q8-quantized and stored in Flash. Inference happens at ~1-3 tokens/sec.

## Project layout

```
tinyllm/
├── tinyllm.ino        Main Arduino sketch
├── config.h           Hyperparameters (must match train_export.py)
├── transformer.h/cpp  Inference engine
├── tokenizer.h        ASCII char tokenizer
├── sampler.h          Temperature + top-k sampler
├── weights.h          Q8 model weights (replace with trained version)
└── tools/
    ├── train_export.py  Train & export weights
    └── requirements.txt Python deps
```

## Quick start (placeholder weights)

1. Open `tinyllm/` in the Arduino IDE.
2. Select board: **ESP32 Dev Module** (or your specific Gen-1 board).
3. Flash partition scheme: **Default 4MB with spiffs** (or any that gives >300 KB Flash for sketch).
4. Upload. Open Serial Monitor at **115200 baud**.
5. Type a prompt and press Enter.

The placeholder `weights.h` has all-zero weights, so the model outputs random
ASCII characters. That proves the pipeline works.

## Training real weights (optional but recommended)

Requirements: Python 3.9+, PyTorch 2.0+

```bash
pip install -r tools/requirements.txt

# Train on bundled Shakespeare (auto-downloaded, ~1 MB)
python tools/train_export.py --steps 3000

# Or use your own text file
python tools/train_export.py --data my_corpus.txt --steps 5000
```

After ~5 minutes on CPU (seconds on GPU), the script:
1. Prints a sample generation.
2. Overwrites `weights.h` with Q8-quantized values.
3. Re-upload the sketch to flash new weights.

## Serial commands

| Command | Effect |
|---|---|
| `<any text>` | Use as prompt, generate up to 200 characters |
| `temp:0.7` | Set temperature (0.1 = focused, 1.5 = wild) |
| `topk:5` | Set top-k (0 = no cutoff) |
| `ctx:reset` | Clear KV cache and restart |
| `help` | Print command list |

## Memory budget

| Resource | Used | Available |
|---|---|---|
| Flash (weights) | ~74 KB | 4 MB |
| SRAM (KV cache) | ~64 KB | ~300 KB usable |
| SRAM (activations) | ~4 KB | |

## Hyperparameters (config.h)

| Param | Value |
|---|---|
| Vocabulary | 128 (ASCII) |
| Context | 64 tokens |
| Embedding dim | 64 |
| Layers | 2 |
| Heads | 2 |
| FFN dim | 128 |
| Parameters | ~77 K |
