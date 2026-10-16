import { spawn } from 'node:child_process';
import { root, pythonPath, checkEnvironment } from './local-runtime.mjs';
try {
 checkEnvironment();
 const child=spawn(pythonPath,['-X','utf8','-m','agent_project.cli','--root','agent_project/sample',...process.argv.slice(2)],{cwd:root,stdio:'inherit',windowsHide:true});
 child.on('error',error=>{console.error(error.message);process.exitCode=1});
 child.on('exit',code=>process.exitCode=code||0);
} catch(error){console.error(error.message);process.exitCode=1;}
