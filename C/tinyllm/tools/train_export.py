#!/usr/bin/env python3
"""
train_export.py — Train a tiny char-level GPT and export Q8 weights as weights.h

Usage:
    python tools/train_export.py [--data FILE] [--out ../weights.h] [--steps N]

Options:
    --data FILE     Text corpus to train on  (default: bundled Shakespeare)
    --out  FILE     Output weights.h path    (default: ../weights.h)
    --steps N       Training iterations      (default: 3000)
    --lr   FLOAT    Learning rate            (default: 3e-4)
    --batch INT     Batch size               (default: 32)

After running, copy the generated weights.h into the tinyllm/ sketch folder
and recompile in the Arduino IDE.
"""

import argparse, math, os, struct, sys, time, urllib.request
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError:
    sys.exit("PyTorch is required.  Install with: pip install torch numpy")

# ── Hyperparameters (must match config.h) ────────────────────────────────────
VOCAB_SIZE = 128
CTX_LEN    = 64
N_EMBD     = 64
N_LAYER    = 2
N_HEAD     = 2
FFN_DIM    = 128

# ── Shakespeare download (fallback dataset) ───────────────────────────────────
SHAKESPEARE_URL = (
    "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/"
    "tinyshakespeare/input.txt"
)

def fetch_shakespeare():
    cache = os.path.join(os.path.dirname(__file__), "_shakespeare.txt")
    if not os.path.exists(cache):
        print("Downloading tinyshakespeare...", flush=True)
        urllib.request.urlretrieve(SHAKESPEARE_URL, cache)
    with open(cache, "r", encoding="utf-8") as f:
        return f.read()

# ── Tokenizer (identity: char → ASCII) ───────────────────────────────────────
def encode(text):
    return [ord(c) & 0x7F for c in text]

def decode(ids):
    return "".join(chr(i) for i in ids)

# ── Model definition ──────────────────────────────────────────────────────────
class CausalSelfAttention(nn.Module):
    def __init__(self):
        super().__init__()
        self.wq = nn.Linear(N_EMBD, N_EMBD, bias=False)
        self.wk = nn.Linear(N_EMBD, N_EMBD, bias=False)
        self.wv = nn.Linear(N_EMBD, N_EMBD, bias=False)
        self.wo = nn.Linear(N_EMBD, N_EMBD, bias=False)

    def forward(self, x):
        B, T, C = x.shape
        q = self.wq(x).view(B, T, N_HEAD, C // N_HEAD).transpose(1, 2)
        k = self.wk(x).view(B, T, N_HEAD, C // N_HEAD).transpose(1, 2)
        v = self.wv(x).view(B, T, N_HEAD, C // N_HEAD).transpose(1, 2)
        # Scaled dot-product attention with causal mask
        att = (q @ k.transpose(-2, -1)) / math.sqrt(q.size(-1))
        causal = torch.tril(torch.ones(T, T, device=x.device)).bool()
        att = att.masked_fill(~causal, float('-inf'))
        att = F.softmax(att, dim=-1)
        y = (att @ v).transpose(1, 2).contiguous().view(B, T, C)
        return self.wo(y)

class FFN(nn.Module):
    def __init__(self):
        super().__init__()
        self.w1 = nn.Linear(N_EMBD, FFN_DIM, bias=False)
        self.w2 = nn.Linear(FFN_DIM, N_EMBD, bias=False)

    def forward(self, x):
        return self.w2(F.gelu(self.w1(x)))

class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.ln1  = nn.RMSNorm(N_EMBD)
        self.attn = CausalSelfAttention()
        self.ln2  = nn.RMSNorm(N_EMBD)
        self.ffn  = FFN()

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.ffn(self.ln2(x))
        return x

class TinyGPT(nn.Module):
    def __init__(self):
        super().__init__()
        self.wte    = nn.Embedding(VOCAB_SIZE, N_EMBD)
        self.blocks = nn.ModuleList([Block() for _ in range(N_LAYER)])
        self.lnf    = nn.RMSNorm(N_EMBD)
        # Weight tying: lm_head shares wte weights
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, std=0.02)

    def forward(self, idx):
        B, T = idx.shape
        x = self.wte(idx)
        for block in self.blocks:
            x = block(x)
        x = self.lnf(x)
        # Tied embedding as LM head
        logits = x @ self.wte.weight.T
        return logits

# ── Training ──────────────────────────────────────────────────────────────────
def get_batch(data, batch_size, device):
    ix = torch.randint(len(data) - CTX_LEN, (batch_size,))
    x  = torch.stack([data[i   : i + CTX_LEN    ] for i in ix])
    y  = torch.stack([data[i+1 : i + CTX_LEN + 1] for i in ix])
    return x.to(device), y.to(device)

def train(model, data, steps, lr, batch_size, device):
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=steps)
    model.train()
    t0 = time.time()
    for step in range(1, steps + 1):
        x, y = get_batch(data, batch_size, device)
        logits = model(x)                          # [B, T, VOCAB]
        loss   = F.cross_entropy(logits.view(-1, VOCAB_SIZE), y.view(-1))
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        if step % 200 == 0 or step == steps:
            elapsed = time.time() - t0
            print(f"  step {step:5d}/{steps}  loss={loss.item():.4f}  "
                  f"lr={scheduler.get_last_lr()[0]:.2e}  {elapsed:.0f}s")
    return model

# ── Q8 Quantisation ───────────────────────────────────────────────────────────
def quantize_q8(tensor: torch.Tensor):
    """Return (int8 numpy array, float32 scale)."""
    t = tensor.detach().float().numpy()
    scale = float(np.max(np.abs(t))) / 127.0
    if scale == 0:
        scale = 1e-7
    q = np.clip(np.round(t / scale), -127, 127).astype(np.int8)
    return q, scale

# ── C-header export ───────────────────────────────────────────────────────────
def fmt_array(name, arr_1d, scale, comment=""):
    vals = ", ".join(str(int(v)) for v in arr_1d)
    n    = len(arr_1d)
    s    = f"// {name}  [{n}]  scale={scale:.6e}"
    if comment:
        s += f"  ({comment})"
    s += f"\nstatic const float  W_SCALE_{name} = {scale:.8e}f;\n"
    s += f"static const int8_t PROGMEM {name}[{n}] = {{{vals}}};\n"
    return s

def export(model, out_path):
    lines = []
    lines.append("// weights.h — Q8-quantized TinyLLM weights")
    lines.append("// Auto-generated by tools/train_export.py — do not edit manually.")
    lines.append("#pragma once")
    lines.append("#include <stdint.h>")
    lines.append("#include <Arduino.h>")
    lines.append("")

    def add(name, tensor, comment=""):
        q, s = quantize_q8(tensor)
        lines.append(fmt_array(name, q.flatten(), s, comment))

    # Token embedding (also used as LM head — weight tied)
    add("W_WTE", model.wte.weight,
        f"{VOCAB_SIZE}x{N_EMBD} = {VOCAB_SIZE*N_EMBD} bytes")

    for l in range(N_LAYER):
        blk = model.blocks[l]
        add(f"W_LN1_{l}", blk.ln1.weight,          f"layer {l} RMSNorm-1 weight")
        add(f"W_WQ_{l}",  blk.attn.wq.weight,      f"layer {l} Q proj  [{N_EMBD}x{N_EMBD}]")
        add(f"W_WK_{l}",  blk.attn.wk.weight,      f"layer {l} K proj")
        add(f"W_WV_{l}",  blk.attn.wv.weight,      f"layer {l} V proj")
        add(f"W_WO_{l}",  blk.attn.wo.weight,      f"layer {l} O proj")
        add(f"W_LN2_{l}", blk.ln2.weight,           f"layer {l} RMSNorm-2 weight")
        add(f"W_W1_{l}",  blk.ffn.w1.weight,       f"layer {l} FFN expand [{FFN_DIM}x{N_EMBD}]")
        add(f"W_W2_{l}",  blk.ffn.w2.weight,       f"layer {l} FFN project [{N_EMBD}x{FFN_DIM}]")

    add("W_LNF", model.lnf.weight, "final RMSNorm weight")

    # Pointer tables for layer-indexed access
    lines.append("// ── Pointer tables ───────────────────────────────────────────────────────────")
    for arr_base, scale_base in [
        ("W_LN1", "W_SCALE_LN1"), ("W_WQ", "W_SCALE_WQ"), ("W_WK", "W_SCALE_WK"),
        ("W_WV",  "W_SCALE_WV"),  ("W_WO", "W_SCALE_WO"), ("W_LN2", "W_SCALE_LN2"),
        ("W_W1",  "W_SCALE_W1"),  ("W_W2", "W_SCALE_W2"),
    ]:
        ptrs   = ", ".join(f"{arr_base}_{l}"   for l in range(N_LAYER))
        scales = ", ".join(f"{scale_base}_{l}" for l in range(N_LAYER))
        lines.append(
            f"static const int8_t* const {arr_base}[{N_LAYER}] = {{{ptrs}}};"
        )
        lines.append(
            f"static const float {scale_base}[{N_LAYER}] = {{{scales}}};"
        )
    lines.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    size = os.path.getsize(out_path)
    print(f"\nExported {out_path}  ({size:,} bytes)")
    flash_est = VOCAB_SIZE * N_EMBD + N_LAYER * (64 + 4 * N_EMBD * N_EMBD + 2 * FFN_DIM * N_EMBD + 64) + 64
    print(f"Flash estimate : ~{flash_est // 1024} KB Q8 weights")

# ── Generate sample text ──────────────────────────────────────────────────────
@torch.no_grad()
def sample(model, prompt="To be, or", n=200, temp=0.85, top_k=10, device="cpu"):
    model.eval()
    ctx = torch.tensor([encode(prompt)], dtype=torch.long, device=device)
    out = list(encode(prompt))
    for _ in range(n):
        logits = model(ctx[:, -CTX_LEN:])[:, -1, :]  # [1, VOCAB]
        logits = logits / temp
        # Top-k filter
        if top_k > 0:
            vals, _ = torch.topk(logits, min(top_k, logits.size(-1)))
            logits[logits < vals[:, -1:]] = float('-inf')
        probs = F.softmax(logits, dim=-1)
        nxt   = torch.multinomial(probs, 1).item()
        out.append(nxt)
        ctx = torch.cat([ctx, torch.tensor([[nxt]], device=device)], dim=1)
    return decode(out)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data",  default=None,        help="training text file")
    ap.add_argument("--out",   default=os.path.join(os.path.dirname(__file__),
                                                    "..", "weights.h"))
    ap.add_argument("--steps", type=int,   default=3000)
    ap.add_argument("--lr",    type=float, default=3e-4)
    ap.add_argument("--batch", type=int,   default=32)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device : {device}")

    # Load corpus
    if args.data:
        with open(args.data, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = fetch_shakespeare()
    print(f"Corpus : {len(text):,} characters")

    data = torch.tensor(encode(text), dtype=torch.long)
    n_params = sum(p.numel() for p in TinyGPT().parameters())
    print(f"Params : {n_params:,}  ({n_params // 1024} K)")

    model = TinyGPT().to(device)
    print(f"\nTraining for {args.steps} steps...")
    train(model, data, args.steps, args.lr, args.batch, device)

    # Sample
    print("\n── Sample output ────────────────────────────────────────────────────────────")
    print(sample(model, prompt="To be, or", device=device))
    print("─────────────────────────────────────────────────────────────────────────────\n")

    # Export
    out_path = os.path.abspath(args.out)
    export(model, out_path)
    print(f"\nDone!  Copy {out_path} into your tinyllm/ sketch folder and recompile.")

if __name__ == "__main__":
    main()
