import { spawn } from 'node:child_process';
import { existsSync, copyFileSync } from 'node:fs';
import path from 'node:path';
import { root, pythonPath, checkNode, findPython, checkEnvironment } from './local-runtime.mjs';

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { cwd: root, stdio: 'inherit', windowsHide: true });
    child.on('error', reject); child.on('exit', code => code === 0 ? resolve() : reject(Error(`安装步骤未完成（退出码 ${code}）。`)));
  });
}
try {
  checkNode();
  if (process.argv.includes('--check')) {
    console.log(`本地环境已就绪：PyTorch ${checkEnvironment()}`);
    process.exit(0);
  }
  if (!existsSync(pythonPath)) {
    const python = findPython(); console.log(`使用 Python ${python.version} 创建 .venv-oj。`);
    await run(python.command, [...python.args, '-m', 'venv', path.join(root, '.venv-oj')]);
  }
  console.log('安装 CPU 版 PyTorch 和判题依赖。');
  const torchArgs = process.platform === 'darwin' ? ['torch==2.14.1'] : ['torch==2.14.1+cpu', '--index-url', 'https://download.pytorch.org/whl/cpu'];
  await run(pythonPath, ['-m', 'pip', 'install', ...torchArgs]);
  await run(pythonPath, ['-m', 'pip', 'install', '-r', 'oj/requirements.txt']);
  if (!existsSync(path.join(root, '.env'))) copyFileSync(path.join(root, '.env.example'), path.join(root, '.env'));
  const npmCli = process.env.npm_execpath;
  if (!npmCli || !existsSync(npmCli)) throw Error('请通过 npm run setup 启动安装。');
  console.log('安装网页依赖。');
  await run(process.execPath, [npmCli, 'ci']);
  console.log(`安装完成：PyTorch ${checkEnvironment()}。运行 npm run learn 开始练习。`);
} catch (error) {
  console.error(error.message); process.exitCode = 1;
}
