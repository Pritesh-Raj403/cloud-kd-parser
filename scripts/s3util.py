"""Small S3 helper: upload/download a folder, write sha256 of model files.
Usage:
  python scripts/s3util.py put-dir out/v1 models v1
  python scripts/s3util.py get <bucket> <key> <local_path>
"""
import hashlib
import os
import sys

import boto3


def client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )


def sha_of_dir(path):
    h = hashlib.sha256()
    for name in sorted(os.listdir(path)):
        if name == "model.sha256":
            continue
        with open(os.path.join(path, name), "rb") as f:
            h.update(name.encode())
            h.update(f.read())
    return h.hexdigest()


def main():
    cmd = sys.argv[1]
    c = client()
    if cmd == "put-dir":
        _, _, folder, bucket, version = sys.argv[:5]
        digest = sha_of_dir(folder)
        with open(os.path.join(folder, "model.sha256"), "w") as f:
            f.write(digest + "\n")
        for name in os.listdir(folder):
            c.upload_file(os.path.join(folder, name), bucket, f"models/{version}/{name}" if bucket == "models" else f"{version}/{name}")
        print("sha256:", digest)
    elif cmd == "get":
        _, _, bucket, key, local = sys.argv[:5]
        c.download_file(bucket, key, local)


if __name__ == "__main__":
    main()
