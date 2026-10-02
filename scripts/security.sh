#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
mkdir -p "$REPORTS/security"
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v sit753-trivy-cache:/root/.cache/ \
    -v "$REPORTS/security:/reports" aquasec/trivy:latest image --scanners vuln \
    --format json --output /reports/image.json "$IMAGE_ID"
docker run --rm -v sit753-trivy-cache:/root/.cache/ -v "$WORK/security-context:/source:ro" \
    -v "$REPORTS/security:/reports" aquasec/trivy:latest fs --scanners vuln \
    --format json --output /reports/dependencies.json /source
python3 "$ROOT/scripts/security-gate.py"
