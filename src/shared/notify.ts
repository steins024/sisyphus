import { exec } from 'node:child_process';

export function sendNotification(title: string, message: string): void {
  if (process.platform !== 'darwin') return;
  const escapedTitle = title.replace(/"/g, '\\"');
  const escapedMsg = message.replace(/"/g, '\\"');
  const script = `display notification "${escapedMsg}" with title "${escapedTitle}"`;
  exec(`osascript -e '${script}'`, () => { /* ignore errors */ });
}
