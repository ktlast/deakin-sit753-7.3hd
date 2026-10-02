#!/usr/bin/env python3
import argparse
import os
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--runtime-dir', type=Path, default=root)
args = parser.parse_args()
runtime = args.runtime_dir.resolve()
runtime.mkdir(parents=True, exist_ok=True)
local = runtime / '.local'
local.mkdir(exist_ok=True)
os.chmod(local, 0o700)
(runtime / 'workspace').mkdir(exist_ok=True)
(runtime / 'workspace@tmp').mkdir(exist_ok=True)
env = runtime / '.env'
values = dict(line.split('=', 1) for line in env.read_text().splitlines()) if env.exists() else {}
values.update({'PROJECT_DIR': str(root), 'RUNTIME_DIR': str(runtime)})
values.setdefault('JENKINS_ADMIN_PASSWORD', secrets.token_hex(16))
values.setdefault('SONAR_ADMIN_PASSWORD', 'Aa!' + secrets.token_hex(16))
env.write_text(''.join(f'{key}={value}\n' for key, value in values.items()))
os.chmod(env, 0o600)
print('Local settings ready. Credentials are in .env; they are not printed.')
