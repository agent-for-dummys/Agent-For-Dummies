import { mkdir, mkdtemp, copyFile, writeFile, readFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { WebSocketServer } from 'ws';

import { foundationTasks } from '../exercises/foundations/tasks.mjs';
import { prepareFoundation } from './foundation-workspace.mjs';

const endpoint = '/__local-docker-practice';
const loopback = new Set(['127.0.0.1', '::1', '::ffff:127.0.0.1']);
const localHost = /^(?:localhost|127\.0\.0\.1|\[::1\])(?::\d+)?$/i;

function shell() {
  if (process.platform !== 'win32') {
    return { executable: process.env.SHELL || '/bin/sh', args: ['-i'] };
  }
  return {
    executable: 'powershell.exe',
    args: ['-NoLogo', '-NoProfile', '-NoExit', '-Command',
      '[Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()'],
  };
}

export function dockerPractice(root) {
  let server;
  let sockets;
  let upgrade;
  return {
    name: 'local-docker-practice',
    configureServer(vite) {
      server = vite.httpServer;
      if (!server) return;
      const route = vite.config.base.replace(/\/$/, '') + endpoint;
      sockets = new WebSocketServer({ noServer: true, maxPayload: 1024 * 1024 });
      upgrade = (request, socket, head) => {
        const host = request.headers.host || '';
        const url = new URL(request.url || '/', 'http://localhost');
        if (url.pathname !== route) return;
        const level = url.searchParams.get('level');
        const task = foundationTasks.find(task => task.id === url.searchParams.get('task'));
        if (!loopback.has(request.socket.remoteAddress) || !localHost.test(host) ||
            request.headers.origin !== 'http://' + host || (!task && !['1', '2'].includes(level))) {
          socket.end('HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n');
          return;
        }
        if (sockets.clients.size >= 8) {
          socket.end('HTTP/1.1 503 Service Unavailable\r\nConnection: close\r\n\r\n');
          return;
        }
        sockets.handleUpgrade(request, socket, head, ws => startSession(ws, root, level, task));
      };
      server.on('upgrade', upgrade);
    },
    closeBundle() {
      if (upgrade) server?.off('upgrade', upgrade);
      for (const socket of sockets?.clients ?? []) socket.terminate();
      sockets?.close();
    },
  };
}

function startSession(socket, root, level, task) {
  let folder;
  let terminal;
  let pending = Promise.resolve();
  let closed = false;
  const send = event => {
    if (socket.readyState !== socket.OPEN) return;
    if (socket.bufferedAmount > 2 * 1024 * 1024) {
      socket.close(1008, 'Terminal output buffer full');
      return;
    }
    socket.send(JSON.stringify(event));
  };
  const report = error => send({ type: 'message', data: error.message });

  socket.on('message', data => {
    pending = pending.then(async () => {
      if (closed) return;
      const event = JSON.parse(data.toString('utf8'));
      if (event.type === 'start' && !terminal) {
        const packageName = 'node-pty';
        const { spawn } = await import(packageName).catch(() => {
          throw Error('本地终端组件未安装。请在项目目录运行 npm install，再重启本地服务。');
        });
        if (closed) return;
        const workspace = path.join(root, 'work', 'docker-practice');
        await mkdir(workspace, { recursive: true });
        const work = await mkdtemp(path.join(workspace, 'session-'));
        folder = path.join(work, task?.id ?? 'step' + level);
        await mkdir(folder);
        if (task) {
          await prepareFoundation(folder, task);
          for (const file of task.editable) await saveDraft(file, event.files?.[file] ?? task.files[file]);
        } else await Promise.all([
          copyFile(path.join(root, 'exercises', 'docker', 'main.cpp'), path.join(folder, 'main.cpp')),
          saveDraft('dockerfile', event.files?.dockerfile),
          saveDraft('Makefile', event.files?.Makefile),
        ]);
        if (closed) return;
        const { executable, args } = task?.subject === 'linux'
          ? process.platform === 'win32'
            ? {executable:'wsl.exe', args:['--cd', folder, '--exec', 'bash', '--noprofile', '--norc', '-i']}
            : {executable:'/bin/bash', args:['--noprofile','--norc','-i']}
          : shell();
        terminal = spawn(executable, args, {
          name: 'xterm-256color', cwd: folder, env: { ...process.env, TERM: 'xterm-256color' },
          ...size(event),
        });
        terminal.onData(text => send({ type: 'output', data: text }));
        terminal.onExit(({ exitCode }) => {
          send({ type: 'message', data: '终端已退出（' + exitCode + '）。' });
          socket.close();
        });
      } else if (terminal && event.type === 'input' && typeof event.data === 'string') {
        terminal.write(event.data);
      } else if (terminal && event.type === 'resize') {
        const { cols, rows } = size(event);
        terminal.resize(cols, rows);
      } else if (terminal && event.type === 'read' && task?.files[event.file] !== undefined) {
        send({type:'file', file:event.file, data:await readFile(path.join(folder,event.file),'utf8')});
      } else if (terminal && event.type === 'draft') {
        await saveDraft(event.file, event.draft);
      }
    }).catch(error => {
      report(error);
      if (!terminal) socket.close();
    });
  });

  async function saveDraft(file, draft) {
    if (task ? !task.editable.includes(file) : file !== 'dockerfile' && file !== 'Makefile') throw Error('无法同步该练习文件。');
    if (typeof draft !== 'string' || Buffer.byteLength(draft) > 64 * 1024) {
      throw Error(file + ' 内容无效或超过终端支持的大小。');
    }
    await writeFile(path.join(folder, file), draft, 'utf8');
  }

  socket.on('error', () => socket.terminate());
  socket.on('close', () => {
    closed = true;
    try { terminal?.kill(); } catch {}
    void pending.then(async () => {
      if (folder) await rm(path.dirname(folder), { recursive: true, force: true, maxRetries: 2 });
    }).catch(() => {});
  });
}

function size(event) {
  const clamp = (value, fallback, min, max) => Number.isInteger(value) ? Math.min(max, Math.max(min, value)) : fallback;
  return { cols: clamp(event.cols, 80, 2, 300), rows: clamp(event.rows, 24, 2, 120) };
}
