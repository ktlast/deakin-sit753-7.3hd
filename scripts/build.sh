#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
# Keep earlier reports instead of deleting them.
if [[ -d "$REPORTS" ]]; then
    mkdir -p "$WORK/history"
    mv "$REPORTS" "$WORK/history/$(date +%Y%m%d-%H%M%S)-${BUILD_NUMBER:-local}"
fi
if [[ -d "$WORK/source" ]]; then
    mkdir -p "$WORK/history"
    mv "$WORK/source" "$WORK/history/source-$(date +%Y%m%d-%H%M%S)-${BUILD_NUMBER:-local}"
fi
mkdir -p "$WORK/source" "$REPORTS/build"
rsync -a --exclude='.env*' --exclude='__pycache__' "$ROOT/app/" "$WORK/source/"
docker build --label "org.opencontainers.image.revision=$COMMIT" -t "$IMAGE" "$WORK/source"
docker image inspect "$IMAGE" -f '{{.Id}}' > "$REPORTS/build/image-id.txt"
docker image inspect "$IMAGE" > "$REPORTS/build/image.json"
mkdir -p "$WORK/security-context"
docker run --rm "$IMAGE" python -m pip freeze > "$WORK/security-context/requirements.txt"
cp "$WORK/security-context/requirements.txt" "$REPORTS/build/runtime-requirements.txt"
printf '%s\n' "$COMMIT" > "$REPORTS/build/source-commit.txt"
docker save "$IMAGE" | gzip > "$REPORTS/build/image.tar.gz"
echo "Built $IMAGE from $COMMIT"
