"""Run the teacher (Ollama phi3.5) over validation.jsonl -> predictions for score.py."""
import json
import sys

import requests

OLLAMA = "http://localhost:11434"


def main():
    inp, out = sys.argv[1:3]
    template = open("prompts/teacher_prompt.txt", encoding="utf-8").read()
    with open(inp) as f, open(out, "w") as o:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            resp = requests.post(
                f"{OLLAMA}/api/generate",
                json={
                    "model": "phi3.5",
                    "prompt": template.replace("{command}", r["text"]),
                    "stream": False,
                    "options": {"temperature": 0, "seed": 42},
                },
                timeout=600,
            )
            o.write(json.dumps({"id": r["id"], "prediction": resp.json()["response"]}) + "\n")


if __name__ == "__main__":
    main()
