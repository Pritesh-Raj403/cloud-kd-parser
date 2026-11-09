# cloud-kd-parser

Sequence-level knowledge distillation of a command parser (phi3.5 teacher -> pythia-70m student), deployed on a local k3d cluster.

## Setup
1. Copy the course `student_kit` contents into this repo: `data/`, `tools/`, `network/packets_sample.jsonl`.
2. Install: Docker, k3d, kubectl, Ollama, Python 3.11. Then `ollama pull phi3.5`.

## Build and deploy
```
make up
```
Port-forward SeaweedFS to create buckets and upload data (see steps below), then deploy workers.

## Task 1: teacher labelling
```
kubectl -n data port-forward svc/seaweedfs 8333:8333 &
export S3_ENDPOINT=http://localhost:8333
export AWS_ACCESS_KEY_ID=$(kubectl -n app get secret s3-creds -o jsonpath='{.data.AWS_ACCESS_KEY_ID}' | base64 -d)
export AWS_SECRET_ACCESS_KEY=$(kubectl -n app get secret s3-creds -o jsonpath='{.data.AWS_SECRET_ACCESS_KEY}' | base64 -d)
python -c "import boto3,os;c=boto3.client('s3',endpoint_url=os.environ['S3_ENDPOINT']);[c.create_bucket(Bucket=b) for b in ('datasets','models')];c.upload_file('data/commands_pool.jsonl','datasets','commands_pool.jsonl')"
OLLAMA_HOST=0.0.0.0 ollama serve &
kubectl apply -f k8s/20-workers.yaml
python worker/clean.py
```

## Task 2: train
```
python scripts/s3util.py get datasets v1/train.jsonl data/train.jsonl
make train SUBSET=50     # smoke test
make train               # v1
python scripts/s3util.py put-dir out/v1 models v1
make train-v2
python scripts/s3util.py put-dir out/v2 models v2
make eval-teacher eval-base eval-student
```

## Test the service
```
curl -X POST localhost:8080/parse -H 'content-type: application/json' -d '{"text":"what is the weather in london"}'
locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/loadtest
```

## Tear down
```
make down
```
