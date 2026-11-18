import { execFileSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

export async function prepareFoundation(folder, task) {
  for (const [file, content] of Object.entries(task.files)) {
    const target = path.join(folder, file);
    await mkdir(path.dirname(target), {recursive:true});
    await writeFile(target, content, 'utf8');
  }
  if (task.subject === 'git') {
    const git = args => execFileSync('git', args, {cwd:folder, windowsHide:true, stdio:'pipe', env:{...process.env, GIT_CONFIG_NOSYSTEM:'1'}});
    git(['init','-b','main']);
    git(['config','user.name','Practice']);
    git(['config','user.email','practice@example.invalid']);
    git(['config','core.autocrlf','false']);
    git(['add','--','README.md']);
    if (task.id === 'git-commit') git(['add','--','.gitignore']);
    git(['commit','-m','初始化练习']);
  }
}
