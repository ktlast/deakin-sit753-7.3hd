#!/usr/bin/env python3
import base64
import argparse
import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('command', choices=['setup-sonar', 'update', 'run', 'status', 'log'])
parser.add_argument('--env-file', type=Path, default=root / '.env')
args = parser.parse_args()
config = dict(line.split('=', 1) for line in args.env_file.read_text().splitlines())
runtime = Path(config.get('RUNTIME_DIR', str(root)))

def client(base, username, password):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    auth = base64.b64encode(f'{username}:{password}'.encode()).decode()
    def request(path, data=None, content_type=None, headers=None):
        body = urllib.parse.urlencode(data).encode() if isinstance(data, dict) else data
        request_headers = {'Authorization': 'Basic ' + auth}
        if content_type:
            request_headers['Content-Type'] = content_type
        request_headers.update(headers or {})
        req = urllib.request.Request(base + path, data=body, headers=request_headers)
        try:
            with opener.open(req, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode()
            raise RuntimeError(f'{path}: HTTP {error.code}: {detail}') from None
    return request

def setup_sonar():
    base = 'http://127.0.0.1:19000'
    for _ in range(60):
        try:
            with urllib.request.urlopen(base + '/api/system/status', timeout=3) as response:
                if json.load(response)['status'] == 'UP':
                    break
        except (OSError, ValueError):
            pass
        time.sleep(2)
    else:
        raise RuntimeError('SonarQube did not become ready')
    sonar = client(base, 'admin', config['SONAR_ADMIN_PASSWORD'])
    try:
        sonar('/api/authentication/validate')
        valid = json.loads(sonar('/api/authentication/validate'))['valid']
    except RuntimeError:
        valid = False
    if not valid:
        default = client(base, 'admin', 'admin')
        default('/api/users/change_password', {'login': 'admin', 'previousPassword': 'admin', 'password': config['SONAR_ADMIN_PASSWORD']})
    projects = json.loads(sonar('/api/projects/search?projects=sit753-decents'))
    if not projects['components']:
        sonar('/api/projects/create', {'project': 'sit753-decents', 'name': 'SIT753 Decents'})
    gates = json.loads(sonar('/api/qualitygates/list'))['qualitygates']
    gate = next((gate for gate in gates if gate['name'] == 'SIT753 Code Health'), None)
    if gate is None:
        gate = json.loads(sonar('/api/qualitygates/create', {'name': 'SIT753 Code Health'}))
    current = json.loads(sonar('/api/qualitygates/show?name=' + urllib.parse.quote(gate['name'])))
    for metric, threshold in [('software_quality_maintainability_rating', '2'), ('software_quality_reliability_rating', '3'), ('duplicated_lines_density', '10')]:
        if not any(condition['metric'] == metric for condition in current['conditions']):
            sonar('/api/qualitygates/create_condition', {'gateName': gate['name'], 'metric': metric, 'op': 'GT', 'error': threshold})
    sonar('/api/qualitygates/select', {'projectKey': 'sit753-decents', 'gateName': gate['name']})
    token_file = runtime / '.local/sonar-token'
    if not token_file.exists():
        token = json.loads(sonar('/api/user_tokens/generate', {'name': 'sit753-pipeline', 'type': 'PROJECT_ANALYSIS_TOKEN', 'projectKey': 'sit753-decents'}))['token']
        token_file.write_text(token + '\n')
        os.chmod(token_file, 0o600)
    print('SonarQube project and code health gate ready.')

def jenkins_command(command):
    jenkins = client('http://127.0.0.1:18080', 'student', config['JENKINS_ADMIN_PASSWORD'])
    path = '/job/sit753-decents'
    if command in {'run', 'update'}:
        crumb = json.loads(jenkins('/crumbIssuer/api/json'))
        headers = {crumb['crumbRequestField']: crumb['crumb']}
        if command == 'update':
            credential_script = '''import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.CredentialsScope
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl
import hudson.util.Secret
def provider = SystemCredentialsProvider.getInstance()
provider.getCredentials().removeAll { it.id == 'sonar-token' }
def token = new File(System.getenv('RUNTIME_DIR'), '.local/sonar-token').text.trim()
provider.getCredentials().add(new StringCredentialsImpl(CredentialsScope.GLOBAL, 'sonar-token', 'Local project analysis token', Secret.fromString(token)))
provider.save()
println 'SonarQube project token configured.'
'''
            jenkins('/scriptText', {'script': credential_script}, headers=headers)
            script = escape((root / 'Jenkinsfile').read_text())
            xml = f'<flow-definition plugin="workflow-job"><description>Build, test, scan and deploy the expense calculation API.</description><keepDependencies>false</keepDependencies><definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps"><script>{script}</script><sandbox>true</sandbox></definition><triggers/><disabled>false</disabled></flow-definition>'
            jenkins(path + '/config.xml', xml.encode(), 'application/xml', headers)
            print('Jenkins job updated from Jenkinsfile.')
        else:
            jenkins(path + '/build', b'', headers=headers)
            print('Jenkins build queued.')
    elif command == 'status':
        data = json.loads(jenkins(path + '/lastBuild/api/json'))
        print(json.dumps({key: data.get(key) for key in ['number', 'building', 'result', 'duration', 'url']}, indent=2))
        try:
            stages = json.loads(jenkins(path + '/lastBuild/wfapi/describe'))
            print(json.dumps([{key: stage.get(key) for key in ['name', 'status']} for stage in stages.get('stages', [])], indent=2))
        except RuntimeError:
            pass
    elif command == 'log':
        print(jenkins(path + '/lastBuild/consoleText').decode()[-12000:])
    else:
        raise SystemExit('Use setup-sonar, update, run, status, or log')

if __name__ == '__main__':
    command = args.command
    if command == 'setup-sonar':
        setup_sonar()
    else:
        jenkins_command(command)
