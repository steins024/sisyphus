import { readFileSync, existsSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { PID_FILE } from '../shared/constants.js';
import { ensureDataDir } from '../shared/utils.js';
import type { DaemonStatus } from '../shared/types.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

function getDaemonStatus(): DaemonStatus {
  if (!existsSync(PID_FILE)) {
    return { running: false };
  }
  const pid = parseInt(readFileSync(PID_FILE, 'utf-8').trim(), 10);
  try {
    process.kill(pid, 0);
    return { running: true, pid };
  } catch {
    return { running: false };
  }
}

export function status(): void {
  const s = getDaemonStatus();
  if (s.running) {
    console.log(`Daemon is running (PID: ${s.pid})`);
  } else {
    console.log('Daemon is stopped');
  }
}

export function start(): void {
  ensureDataDir();
  const s = getDaemonStatus();
  if (s.running) {
    console.log(`Daemon is already running (PID: ${s.pid})`);
    return;
  }

  const serverPath = join(__dirname, '..', 'daemon', 'server.js');
  const child = spawn(process.execPath, [serverPath], {
    detached: true,
    stdio: 'ignore',
  });
  child.unref();
  console.log(`Daemon starting (PID: ${child.pid})`);
}

export function stop(): void {
  const s = getDaemonStatus();
  if (!s.running || !s.pid) {
    console.log('Daemon is not running');
    return;
  }
  process.kill(s.pid, 'SIGTERM');
  console.log(`Sent SIGTERM to daemon (PID: ${s.pid})`);
}
