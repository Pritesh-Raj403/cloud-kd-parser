SUBSET ?= 0
PY ?= python

.PHONY: train train-v2 up down eval-teacher eval-base eval-student

# Reads only training/config.yaml. Needs data/train.jsonl (download from SeaweedFS first, see README).
train:
	$(PY) training/train.py --config training/config.yaml --train data/train.jsonl --out out/v1 --subset $(SUBSET)

# Second version: different seed and one more epoch
train-v2:
	$(PY) training/train.py --config training/config.yaml --train data/train.jsonl --out out/v2 --epochs 4 --seed 7

eval-teacher:
	$(PY) scripts/teacher_validation.py data/validation.jsonl results/teacher_predictions.jsonl
	$(PY) tools/score.py results/teacher_predictions.jsonl data/validation.jsonl --out results/teacher_validation.json

eval-base:
	$(PY) scripts/predict.py EleutherAI/pythia-70m data/validation.jsonl results/base_predictions.jsonl
	$(PY) tools/score.py results/base_predictions.jsonl data/validation.jsonl --out results/base_validation.json

eval-student:
	$(PY) scripts/predict.py out/v1 data/validation.jsonl results/student_predictions.jsonl
	$(PY) tools/score.py results/student_predictions.jsonl data/validation.jsonl --out results/student_validation.json

# make up: build + deploy everything (cluster, storage, secrets, images, app)
up:
	k3d cluster create --config cluster/k3d.yaml || true
	bash scripts/create-secrets.sh
	kubectl apply -f k8s/10-seaweedfs.yaml
	docker build -t nanoparse-service:latest -f service/Dockerfile .
	docker build -t nanoparse-worker:latest -f worker/Dockerfile .
	k3d image import nanoparse-service:latest nanoparse-worker:latest -c nanocloud
	kubectl apply -f k8s/30-app.yaml

down:
	k3d cluster delete nanocloud
