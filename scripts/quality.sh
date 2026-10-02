#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
: "${SONAR_TOKEN:?SonarQube credential required}"
mkdir -p "$REPORTS/quality"
scan_status=0
docker run --rm --platform linux/amd64 --network sit753-tools --user "$(id -u):$(id -g)" \
    -e SONAR_HOST_URL=http://sit753-sonarqube:9000 -e SONAR_TOKEN \
    -v "$WORK:/usr/src" -w /usr/src sonarsource/sonar-scanner-cli:latest \
    -Dsonar.projectKey=sit753-decents -Dsonar.projectName=SIT753-Decents \
    -Dsonar.projectVersion="$VERSION" -Dsonar.sources=source/api -Dsonar.tests=source/tests \
    -Dsonar.python.version=3.12 -Dsonar.python.coverage.reportPaths=results/tests/coverage.xml \
    -Dsonar.exclusions='**/__pycache__/**' -Dsonar.qualitygate.wait=true \
    > "$REPORTS/quality/scanner.log" 2>&1 || scan_status=$?
if [[ -f "$WORK/.scannerwork/report-task.txt" ]]; then
    cp "$WORK/.scannerwork/report-task.txt" "$REPORTS/quality/"
fi
curl --fail --silent --user "$SONAR_TOKEN:" \
    'http://sit753-sonarqube:9000/api/qualitygates/project_status?projectKey=sit753-decents' > "$REPORTS/quality/gate.json"
curl --fail --silent --user "$SONAR_TOKEN:" \
    'http://sit753-sonarqube:9000/api/measures/component?component=sit753-decents&metricKeys=software_quality_maintainability_rating,software_quality_reliability_rating,duplicated_lines_density,coverage,complexity,cognitive_complexity,ncloc,code_smells,bugs' > "$REPORTS/quality/metrics.json"
tail -n 12 "$REPORTS/quality/scanner.log"
exit "$scan_status"
