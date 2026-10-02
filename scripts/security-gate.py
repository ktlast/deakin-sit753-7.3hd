import json
import os
from datetime import date
from pathlib import Path

root = Path(__file__).resolve().parents[1]
reports = Path(os.getenv('RUNTIME_DIR', str(root))) / 'workspace/results/security'
exceptions_path = root / 'security-exceptions.json'
exceptions = json.loads(exceptions_path.read_text())
blocking = []
summary = []
accepted = []
for filename in ['image.json', 'dependencies.json']:
    report = json.loads((reports / filename).read_text())
    for result in report.get('Results', []):
        for finding in result.get('Vulnerabilities', []):
            key = finding['VulnerabilityID'] + ':' + finding['PkgName']
            severity = finding['Severity']
            summary.append(f"{filename}: {key} {severity} installed={finding['InstalledVersion']} fixed={finding.get('FixedVersion', 'none')}")
            exception = exceptions.get(finding['VulnerabilityID'], {})
            allowed = (
                filename == 'image.json' and result.get('Class') == 'os-pkgs'
                and severity == 'HIGH' and not finding.get('FixedVersion')
                and exception.get('packages', {}).get(finding['PkgName']) == finding['InstalledVersion']
                and exception.get('scope') == 'local-runtime-only'
                and exception.get('reason') and exception.get('expires', '') >= date.today().isoformat()
            )
            if severity in {'HIGH', 'CRITICAL'}:
                if allowed:
                    accepted.append(key)
                else:
                    blocking.append(key)
(reports / 'summary.txt').write_text('\n'.join(summary) + '\n')
(reports / 'exceptions.json').write_text(json.dumps(exceptions, indent=2) + '\n')
print(f'Security findings: {len(summary)}; explicitly accepted OS HIGH findings: {len(accepted)}; unaccepted HIGH/CRITICAL: {len(blocking)}')
if blocking:
    print('\n'.join(blocking))
    raise SystemExit(1)
