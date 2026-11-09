#!/usr/bin/env bash
# Creates the S3 credentials as Kubernetes Secrets. Keys are generated at run time,
# so nothing secret is stored in the repository.
set -euo pipefail
AK="${S3_ACCESS_KEY:-$(head -c 12 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 16)}"
SK="${S3_SECRET_KEY:-$(head -c 24 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 32)}"

kubectl apply -f k8s/00-namespaces.yaml

cat > /tmp/s3.json <<EOF
{"identities":[{"name":"admin","credentials":[{"accessKey":"$AK","secretKey":"$SK"}],"actions":["Admin","Read","Write","List"]}]}
EOF
kubectl -n data create secret generic s3-config --from-file=s3.json=/tmp/s3.json --dry-run=client -o yaml | kubectl apply -f -
rm -f /tmp/s3.json

for ns in pipeline app; do
  kubectl -n "$ns" create secret generic s3-creds \
    --from-literal=AWS_ACCESS_KEY_ID="$AK" \
    --from-literal=AWS_SECRET_ACCESS_KEY="$SK" \
    --dry-run=client -o yaml | kubectl apply -f -
done
echo "Secrets created."
