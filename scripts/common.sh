#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
WORK="${RUNTIME_DIR:-$ROOT}/workspace"
REPORTS="$WORK/results"
mkdir -p "$REPORTS"
COMMIT=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || printf '%s' local)
VERSION="${BUILD_NUMBER:-local}-${COMMIT:0:12}"
IMAGE="sit753-decents:$VERSION"
if [[ -f "$REPORTS/build/image-id.txt" ]]; then
    IMAGE_ID=$(cat "$REPORTS/build/image-id.txt")
fi

check_ready() {
    local name=$1
    for attempt in {1..30}; do
        if docker exec "$name" python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3).read()" >/dev/null 2>&1; then
            return 0
        fi
        if [[ $(docker inspect -f '{{.State.Running}}' "$name") != true ]]; then
            break
        fi
        sleep 2
    done
    docker logs "$name" >&2
    return 1
}

check_api() {
    local name=$1 environment=$2
    docker exec -i "$name" python - "$environment" < "$ROOT/scripts/check-api.py"
}
