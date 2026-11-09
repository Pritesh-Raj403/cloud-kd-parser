"""Run a local model folder over a jsonl of commands -> predictions.jsonl for score.py.
Usage: python scripts/predict.py <model_dir> <commands.jsonl> <out.jsonl>
"""
import json
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    model_dir, inp, out = sys.argv[1:4]
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir).eval()
    with open(inp) as f, open(out, "w") as o:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            ids = tok(f"Command: {r['text']}\nJSON:", return_tensors="pt")
            with torch.no_grad():
                g = model.generate(**ids, max_new_tokens=64, do_sample=False, pad_token_id=tok.eos_token_id)
            text = tok.decode(g[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)
            pred = text.strip().split("\n")[0].strip()
            o.write(json.dumps({"id": r["id"], "prediction": pred}) + "\n")


if __name__ == "__main__":
    main()
