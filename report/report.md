# Cloud Computing Mini Project: Knowledge Distillation and Deployment of a Command Parser

Name: Pritesh Raj    Roll number: FILL    GitHub: FILL (tag `final`)

Lines marked FILL need your real measured values. Delete this note and the markers before submitting. Keep measured results and assumptions separate.

## 1. Architecture

A phi3.5 teacher (Ollama, temperature 0, seed 42) labels 3,000 commands. The replies are cleaned and used to fine-tune EleutherAI/pythia-70m (sequence-level distillation). The student is stored in SeaweedFS (S3 API), downloaded by a FastAPI service at start-up, and served from a k3d (k3s) cluster behind a Traefik Ingress. Namespaces: `data` (SeaweedFS), `pipeline` (labelling workers), `app` (service).

## 2. Task 1: Object storage and parallel labelling

Setup: cluster from `cluster/k3d.yaml`; SeaweedFS in `data` with buckets `datasets` and `models`; teacher prompt in `prompts/teacher_prompt.txt`.

Sharding: each worker reads `SHARD_INDEX` and `SHARD_COUNT`. Command line number n (from 0) belongs to the worker where n % SHARD_COUNT == SHARD_INDEX. Every line therefore goes to exactly one worker, with no gaps and no overlap, and workers need no coordination. Each writes its own object `datasets/teacher/shard-<i>.jsonl`, so there are no write conflicts. Round-robin spreads the work evenly even if later lines are harder. FILL: number of workers used and time taken.

Cleaning counts (from `worker/clean.py`):

| Input | Not valid JSON (a) | Wrong keys (b) | Bad intent (c) | Slot not in command (d) | Duplicates | Kept |
|---|---|---|---|---|---|---|
| FILL | FILL | FILL | FILL | FILL | FILL | FILL |

Check: input = a + b + c + d + duplicates + kept. train.sha256: FILL.

## 3. Task 2: Training the student

Config (`training/config.yaml`): seed 42, learning rate 5e-4, batch size 8, 3 epochs, max length 128. Training example format: `Command: <text>\nJSON: <teacher reply>`. FILL: per-epoch loss from `training/loss.csv`, v1 and v2 differences, release asset checksum.

Validation results (from `results/`):

| Model | json_validity | intent | date | time | place | full_frame |
|---|---|---|---|---|---|---|
| Teacher phi3.5 | FILL | FILL | FILL | FILL | FILL | FILL |
| Pythia-70M untrained | FILL | FILL | FILL | FILL | FILL | FILL |
| Student v1 | FILL | FILL | FILL | FILL | FILL | FILL |

Discussion: FILL (what changed after training, where the student still fails, suitability of a 70M model).

Sequence-level vs logit-based distillation. Sequence-level distillation trains the student on the text the teacher generated, as ordinary supervised targets. Logit-based distillation trains the student to match the teacher's probability distribution over the next token at every position. It is not possible here because the two models use different tokenizers and vocabularies (phi3.5 vs Pythia), so their output distributions cannot be compared token by token, and the project only stores the teacher's text replies, not its logits. One limitation: the student copies the teacher's mistakes (any wrong label that passed cleaning is learned as correct), and only 1,500 examples are used.

## 4. Task 3: Inference service

Endpoints: POST /parse (4-key JSON, headers X-Model-Version and X-Served-By), GET /healthz, GET /readyz (503 until the model is loaded). Every output is validated; invalid output gives HTTP 500 `{"error": "invalid_model_output"}`. FAULT_INJECT=1 forces `not json`. Config only through MODEL_URI, MODEL_VERSION, S3_ENDPOINT, MAX_NEW_TOKENS; credentials from a Kubernetes Secret. Image uses CPU-only torch with pinned versions and no weights. FILL: image size, 50-request test at 1 CPU / 1 GiB, peak memory with command output.

## 5. Task 4: Kubernetes deployment, scaling, reliability

FILL for each: requests/limits used, HPA evidence (1 to 2 and back), rolling update failed-request %, X-Model-Version after rollback, recovery test, three cold-start times and median, per-replica request counts (each at least 30%).

Limitation: the cluster is a single node on one laptop, so it shows Pod-level recovery but not fault tolerance across machines; if the laptop goes down everything goes down. FILL: other HPA limits you saw (for example metrics delay).

## 6. Task 5: Subnetting and NACL

| Subnet | Network | Prefix | Usable range | Broadcast | Usable hosts |
|---|---|---|---|---|---|
| app | 10.20.0.0 | /22 | 10.20.0.1 - 10.20.3.254 | 10.20.3.255 | 1022 |
| public | 10.20.4.0 | /24 | 10.20.4.1 - 10.20.4.254 | 10.20.4.255 | 254 |
| data | 10.20.5.0 | /25 | 10.20.5.1 - 10.20.5.126 | 10.20.5.127 | 126 |
| management | 10.20.5.128 | /27 | 10.20.5.129 - 10.20.5.158 | 10.20.5.159 | 30 |

A NACL is stateless, so a reply packet is judged as a new packet and needs its own rule (ephemeral ports 1024-65535). Rules are checked lowest number first and the first match wins, so the deny for 198.51.100.0/24 must have a lower number than the allow rules for TCP 80/443, otherwise the allow would match first. FILL: nacl_sim.py output.

## 7. Task 6: Reproducibility, testing, CI/CD

`make up` builds and deploys from a fresh clone; `make down` deletes the cluster. The workflow runs lint, unit tests, model evaluation (model from the GitHub Release), and a quality gate (`--min-validity 95`), plus gitleaks. FILL: link to the failed run with the untrained model, gitleaks result.

## 8. Task 7: Performance, cost, review

FILL: p50, p95, requests per second, error rate, `kubectl top pods` output, cold-start time (Section 5).

Cost per 1,000 requests = (hourly cost of all running replicas / requests served per hour) x 1000. FILL: rates from `rate_card.json`, each step, result.

SLO: FILL target (for example 99% of requests succeed), window (one load-test run), error budget in requests = total requests x (1 - target), budget used FILL.

| Component | Evidence (measured) | Limitation | Improvement |
|---|---|---|---|
| Data and storage | FILL | FILL | FILL |
| Model quality | FILL | FILL | FILL |
| Latency and throughput | FILL | FILL | FILL |
| Resource utilisation | FILL | FILL | FILL |
| Reliability and recovery | FILL | FILL | FILL |
| Security and cost | FILL | FILL | FILL |
