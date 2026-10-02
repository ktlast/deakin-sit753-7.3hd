#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
mkdir -p "$REPORTS/tests"
docker build --build-arg "APP_IMAGE=$IMAGE" -t "sit753-tests:$VERSION" -f "$ROOT/docker/Dockerfile.tests" "$ROOT"
cleanup() {
    docker logs sit753-decents-ci > "$REPORTS/tests/container.log" 2>&1 || true
    docker rm -f sit753-decents-ci >/dev/null 2>&1 || true
}
trap cleanup EXIT
docker run -d --name sit753-decents-ci --network sit753-tools -e APP_ENV=ci \
    --cap-drop ALL --security-opt no-new-privileges "$IMAGE_ID"
check_ready sit753-decents-ci
docker run --rm --network sit753-tools -e APP_ENV=ci -e TEST_API_URL=http://sit753-decents-ci:8080 \
    -v "$WORK/source:/app" -v "$REPORTS/tests:/reports" \
    "sit753-tests:$VERSION" tests \
    --junitxml=/reports/junit.xml --cov=api --cov-report=xml:/reports/coverage.xml --cov-report=term \
    > "$REPORTS/tests/pytest.log" 2>&1 || { cat "$REPORTS/tests/pytest.log"; exit 1; }
tail -n 8 "$REPORTS/tests/pytest.log"
python3 -c 'import sys, xml.etree.ElementTree as E; p=sys.argv[1]; t=E.parse(p); [setattr(s, "text", "source/api") for s in t.findall("./sources/source")]; t.write(p)' "$REPORTS/tests/coverage.xml"
check_api sit753-decents-ci ci > "$REPORTS/tests/api-check.json"
