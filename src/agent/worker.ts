import { fork } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Task } from './task.js';
import { saveTask, taskFilePath } from './task.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

export function spawnWorker(workerName: string, task: Task): void {
  task.status = 'running';
  task.assignedTo = workerName;
  saveTask(task);

  const runnerPath = join(__dirname, 'worker-runner.js');
  const taskPath = taskFilePath(task.id);

  const child = fork(runnerPath, [taskPath, workerName], {
    detached: false,
    stdio: 'ignore',
  });

  child.on('error', (err) => {
    console.error(`[worker:${workerName}] Failed to spawn: ${err.message}`);
  });

  child.on('exit', (code) => {
    if (code !== 0) {
      console.error(`[worker:${workerName}] Exited with code ${code}`);
    }
  });

  child.unref();
}
