import { spawn } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const envPath = resolve(scriptDir, '..', '..', '.env');

if (existsSync(envPath)) {
  const envFile = readFileSync(envPath, 'utf8');
  for (const line of envFile.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) {
      continue;
    }
    const [key, ...valueParts] = trimmed.split('=');
    if (!process.env[key]) {
      process.env[key] = valueParts.join('=');
    }
  }
}

const host = process.env.BIND_HOST || '127.0.0.1';
const port = process.env.FRONTEND_PORT || '4200';
const npx = process.platform === 'win32' ? 'npx.cmd' : 'npx';

const child = spawn(
  npx,
  ['ng', 'serve', '--host', host, '--port', port, '--proxy-config', 'proxy.conf.js'],
  { stdio: 'inherit' }
);

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  }
  process.exit(code ?? 0);
});
