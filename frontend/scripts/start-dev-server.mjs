import { spawn } from 'node:child_process';

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
