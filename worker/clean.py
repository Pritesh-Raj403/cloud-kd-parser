"""Merge shard outputs, drop bad records, write datasets/v1/train.jsonl + sha256."""
import hashlib
import json
import os

import boto3

INTENTS = {
    "alarm_set", "alarm_query", "calendar_set", "calendar_query",
    "calendar_remove", "weather_query", "datetime_query", "recommendation_events",
}
KEYS = {"intent", "date", "time", "place"}


def s3():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )


def reject_reason(rec):
    raw = rec["teacher_raw"].strip()
    try:
        obj = json.loads(raw)
    except Exception:
        return "a"
    if not isinstance(obj, dict) or set(obj.keys()) != KEYS:
        return "b"
    if obj["intent"] not in INTENTS:
        return "c"
    text = rec["text"].lower()
    for k in ("date", "time", "place"):
        v = obj[k]
        if v is None:
            continue
        if not isinstance(v, str) or v.lower() not in text:
            return "d"
    return None


def main():
    client = s3()
    records = []
    token = None
    while True:
        kw = {"Bucket": "datasets", "Prefix": "teacher/"}
        if token:
            kw["ContinuationToken"] = token
        resp = client.list_objects_v2(**kw)
        for o in resp.get("Contents", []):
            body = client.get_object(Bucket="datasets", Key=o["Key"])["Body"].read().decode()
            records += [json.loads(l) for l in body.splitlines() if l.strip()]
        token = resp.get("NextContinuationToken")
        if not token:
            break

    records.sort(key=lambda r: r["id"])
    counts = {"input": len(records), "a": 0, "b": 0, "c": 0, "d": 0, "duplicates": 0, "kept": 0}
    seen, kept = set(), []
    for rec in records:
        reason = reject_reason(rec)
        if reason:
            counts[reason] += 1
            continue
        if rec["text"] in seen:
            counts["duplicates"] += 1
            continue
        seen.add(rec["text"])
        kept.append(rec)
    counts["kept"] = len(kept)

    data = "".join(json.dumps(r) + "\n" for r in kept).encode()
    digest = hashlib.sha256(data).hexdigest()
    client.put_object(Bucket="datasets", Key="v1/train.jsonl", Body=data)
    client.put_object(Bucket="datasets", Key="v1/train.sha256", Body=(digest + "  train.jsonl\n").encode())
    print(json.dumps(counts, indent=2))
    print("sha256:", digest)


if __name__ == "__main__":
    main()
