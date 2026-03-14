import { fork, ChildProcess } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Task } from './task.js';
import { saveTask, loadTask, taskFilePath } from './task.js';
import { sendNotification } from '../shared/notify.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

export type WorkerDoneCallback = (task: Task) => void;

const activeWorkers = new Map<string, ChildProcess>();

/** Default worker timeout: 5 minutes */
const DEFAULT_TIMEOUT_MS = 5 * 60 * 1000;

export function spawnWorker(
  workerName: string,
  task: Task,
  onDone?: WorkerDoneCallback,
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): void {
  task.status = 'running';
  task.assignedTo = workerName;
  saveTask(task);

  const runnerPath = join(__dirname, 'worker-runner.js');
  const taskPath = taskFilePath(task.id);

  const child = fork(runnerPath, [taskPath, workerName], {
    detached: false,
    stdio: 'ignore',
  });

  activeWorkers.set(task.id, child);

  // Timeout handler
  const timer = setTimeout(() => {
    if (activeWorkers.has(task.id)) {
      try { child.kill('SIGKILL'); } catch { /* noop */ }
      activeWorkers.delete(task.id);
      const current = loadTask(task.id);
      if (current && current.status === 'running') {
        current.status = 'failed';
        current.error = `Worker timed out after ${Math.round(timeoutMs / 1000)}s`;
        saveTask(current);
        sendNotification('Sisyphus ⏰', `Task timed out: ${current.description}`);
        if (onDone) onDone(current);
      }
    }
  }, timeoutMs);

  child.on('exit', (code) => {
    clearTimeout(timer);
    activeWorkers.delete(task.id);
    const updatedTask = loadTask(task.id);
    if (updatedTask) {
      if (code !== 0 && updatedTask.status === 'running') {
        updatedTask.status = 'failed';
        updatedTask.error = `Worker exited with code ${code}`;
        saveTask(updatedTask);
      }
      if (updatedTask.status === 'done') {
        sendNotification('Sisyphus ✅', `Task completed: ${updatedTask.description}`);
      } else if (updatedTask.status === 'failed') {
        sendNotification('Sisyphus ❌', `Task failed: ${updatedTask.description}`);
      }
      if (onDone) onDone(updatedTask);
    }
  });

  child.on('error', (err) => {
    clearTimeout(timer);
    activeWorkers.delete(task.id);
    const current = loadTask(task.id);
    if (current && current.status === 'running') {
      current.status = 'failed';
      current.error = `Worker spawn error: ${err.message}`;
      saveTask(current);
      sendNotification('Sisyphus ❌', `Task failed: ${current.description}`);
      if (onDone) onDone(current);
    }
  });
}
