#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
mkdir -p "$REPORTS/deploy"
docker rm -f sit753-decents-test >/dev/null 2>&1 || true
docker run -d --name sit753-decents-test --network sit753-tools -e APP_ENV=test \
    --cap-drop ALL --security-opt no-new-privileges \
    --restart unless-stopped -p 127.0.0.1:18081:8080 "$IMAGE_ID"
check_ready sit753-decents-test
check_api sit753-decents-test test > "$REPORTS/deploy/api-check.json"
docker inspect sit753-decents-test -f '{{.Image}}' > "$REPORTS/deploy/image-id.txt"
docker logs sit753-decents-test > "$REPORTS/deploy/container.log" 2>&1
