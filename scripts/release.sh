#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
mkdir -p "$REPORTS/release"
test "$(cat "$REPORTS/deploy/image-id.txt")" = "$IMAGE_ID"
previous=$(docker inspect sit753-decents-prod -f '{{.Image}}' 2>/dev/null || true)
printf '%s\n' "$previous" > "$REPORTS/release/previous-image-id.txt"
docker rm -f sit753-decents-prod >/dev/null 2>&1 || true
docker run -d --name sit753-decents-prod --network sit753-tools -e APP_ENV=production \
    --cap-drop ALL --security-opt no-new-privileges \
    --restart unless-stopped -p 127.0.0.1:18082:8080 "$IMAGE_ID"
if ! check_ready sit753-decents-prod || ! check_api sit753-decents-prod production > "$REPORTS/release/api-check.json"; then
    docker logs sit753-decents-prod > "$REPORTS/release/failed-container.log" 2>&1
    docker rm -f sit753-decents-prod >/dev/null
    if [[ -n "$previous" ]]; then
        docker run -d --name sit753-decents-prod --network sit753-tools -e APP_ENV=production \
            --cap-drop ALL --security-opt no-new-privileges \
            --restart unless-stopped -p 127.0.0.1:18082:8080 "$previous"
        check_ready sit753-decents-prod
        echo "Restored previous image $previous" > "$REPORTS/release/rollback.txt"
    fi
    exit 1
fi
docker image tag "$IMAGE_ID" "sit753-decents:release-$VERSION"
docker inspect sit753-decents-prod -f '{{.Image}}' > "$REPORTS/release/image-id.txt"
test "$(cat "$REPORTS/release/image-id.txt")" = "$IMAGE_ID"
docker logs sit753-decents-prod > "$REPORTS/release/container.log" 2>&1
echo "Released the same verified image: $IMAGE_ID"
