"""Shard worker: labels every SHARD_COUNT-th command with the teacher (Ollama)."""
import io
import json
import os

import boto3
import requests

SHARD_INDEX = int(os.environ["SHARD_INDEX"])
SHARD_COUNT = int(os.environ["SHARD_COUNT"])
S3_ENDPOINT = os.environ["S3_ENDPOINT"]
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
PROMPT_FILE = os.environ.get("PROMPT_FILE", "prompts/teacher_prompt.txt")
INPUT_KEY = os.environ.get("INPUT_KEY", "commands_pool.jsonl")


def s3():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )


def ask_teacher(prompt_template, command):
    prompt = prompt_template.replace("{command}", command)
    r = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "phi3.5",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "seed": 42},
        },
        timeout=600,
    )
    r.raise_for_status()
    return r.json()["response"]


def main():
    client = s3()
    body = client.get_object(Bucket="datasets", Key=INPUT_KEY)["Body"].read().decode()
    lines = [l for l in body.splitlines() if l.strip()]
    with open(PROMPT_FILE, encoding="utf-8") as f:
        template = f.read()

    out = io.StringIO()
    for n, line in enumerate(lines):
        if n % SHARD_COUNT != SHARD_INDEX:
            continue
        rec = json.loads(line)
        raw = ask_teacher(template, rec["text"])
        out.write(json.dumps({"id": rec["id"], "text": rec["text"], "teacher_raw": raw}) + "\n")

    client.put_object(
        Bucket="datasets",
        Key=f"teacher/shard-{SHARD_INDEX}.jsonl",
        Body=out.getvalue().encode(),
    )
    print(f"shard {SHARD_INDEX}/{SHARD_COUNT} done")


if __name__ == "__main__":
    main()
