"""Sequence-level distillation: fine-tune pythia-70m on teacher replies. Reads only training/config.yaml."""
import argparse
import csv
import json
import os
import random

import numpy as np
import torch
import yaml
from torch.utils.data import DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="training/config.yaml")
    ap.add_argument("--train", default="data/train.jsonl")
    ap.add_argument("--out", default="out/v1")
    ap.add_argument("--subset", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=0, help="override epochs (used for v2)")
    ap.add_argument("--seed", type=int, default=0, help="override seed (used for v2)")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    seed = args.seed or cfg["seed"]
    epochs = args.epochs or cfg["epochs"]
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(os.cpu_count() or 1)

    n = args.subset or cfg["train_records"]
    recs = [json.loads(l) for l in open(args.train) if l.strip()][:n]

    tok = AutoTokenizer.from_pretrained(cfg["base_model"])
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(cfg["base_model"])

    texts = [f"Command: {r['text']}\nJSON: {r['teacher_raw'].strip()}{tok.eos_token}" for r in recs]
    enc = tok(texts, truncation=True, max_length=cfg["max_seq_length"], padding="max_length", return_tensors="pt")
    labels = enc["input_ids"].clone()
    labels[enc["attention_mask"] == 0] = -100
    ds = list(zip(enc["input_ids"], enc["attention_mask"], labels))

    g = torch.Generator().manual_seed(seed)
    loader = DataLoader(ds, batch_size=cfg["batch_size"], shuffle=True, generator=g)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["learning_rate"])

    os.makedirs(args.out, exist_ok=True)
    os.makedirs("training", exist_ok=True)
    rows = []
    model.train()
    for ep in range(1, epochs + 1):
        total, steps = 0.0, 0
        for ids, mask, lab in loader:
            loss = model(input_ids=ids, attention_mask=mask, labels=lab).loss
            loss.backward()
            opt.step()
            opt.zero_grad()
            total += loss.item()
            steps += 1
        rows.append((ep, total / steps))
        print(f"epoch {ep} loss {total / steps:.4f}")

    with open("training/loss.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["epoch", "loss"])
        w.writerows(rows)

    model.save_pretrained(args.out)
    tok.save_pretrained(args.out)
    print("saved to", args.out)


if __name__ == "__main__":
    main()
