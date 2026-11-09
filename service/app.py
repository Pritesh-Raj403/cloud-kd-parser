import json
import os
import tempfile
import threading

import boto3
import torch
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_URI = os.environ.get("MODEL_URI", "s3://models/models/v1/")
MODEL_VERSION = os.environ.get("MODEL_VERSION", "v1")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "")
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "64"))
FAULT_INJECT = os.environ.get("FAULT_INJECT", "0")
POD_NAME = os.environ.get("HOSTNAME", "local")

INTENTS = {
    "alarm_set", "alarm_query", "calendar_set", "calendar_query",
    "calendar_remove", "weather_query", "datetime_query", "recommendation_events",
}
KEYS = {"intent", "date", "time", "place"}

app = FastAPI()
state = {"model": None, "tok": None}


class ParseIn(BaseModel):
    text: str


def validate(raw):
    """Return the parsed dict if raw is a valid 4-key output, else None."""
    try:
        obj = json.loads(raw)
    except Exception:
        return None
    if not isinstance(obj, dict) or set(obj) != KEYS:
        return None
    if obj["intent"] not in INTENTS:
        return None
    for k in ("date", "time", "place"):
        if obj[k] is not None and not isinstance(obj[k], str):
            return None
    return obj


def download_model():
    bucket, _, prefix = MODEL_URI.removeprefix("s3://").partition("/")
    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )
    dest = tempfile.mkdtemp()
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    for o in resp.get("Contents", []):
        name = o["Key"][len(prefix):]
        if name and not name.endswith(".sha256"):
            s3.download_file(bucket, o["Key"], os.path.join(dest, name))
    return dest


def load():
    path = download_model()
    state["tok"] = AutoTokenizer.from_pretrained(path)
    state["model"] = AutoModelForCausalLM.from_pretrained(path).eval()


@app.on_event("startup")
def startup():
    threading.Thread(target=load, daemon=True).start()


@app.get("/healthz")
def healthz():
    return {"status": "alive"}


@app.get("/readyz")
def readyz():
    if state["model"] is None:
        return JSONResponse({"status": "loading"}, status_code=503)
    return {"status": "ready"}


def generate(text):
    tok, model = state["tok"], state["model"]
    ids = tok(f"Command: {text}\nJSON:", return_tensors="pt")
    with torch.no_grad():
        out = model.generate(
            **ids, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
            pad_token_id=tok.eos_token_id,
        )
    gen = tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)
    return gen.strip().split("\n")[0].strip()


@app.post("/parse")
def parse(body: ParseIn):
    if state["model"] is None:
        return JSONResponse({"error": "model_not_ready"}, status_code=503)
    raw = generate(body.text)
    if FAULT_INJECT == "1":
        raw = "not json"
    obj = validate(raw)
    if obj is None:
        return JSONResponse({"error": "invalid_model_output"}, status_code=500)
    headers = {"X-Model-Version": MODEL_VERSION, "X-Served-By": POD_NAME}
    return JSONResponse(obj, headers=headers)
