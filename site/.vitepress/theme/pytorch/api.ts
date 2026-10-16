export type Verdict = 'AC'|'WA'|'RE'|'CE'|'TLE'|'SYSTEM'|'OK';
export interface TestResult {name:string;public:boolean;status:'passed'|'failed'|'error';matchesExpected?:boolean;message?:string;line?:number;input?:unknown;expected?:unknown;actual?:unknown}
export interface JudgeResult {verdict:Verdict;passed?:number;total?:number;stdout?:string;message?:string;line?:number;elapsedMs?:number;cases:TestResult[]}
export interface Health {ready:boolean;version:string;device:string;message?:string;engines?:Record<string,{ready:boolean;version:string}>}
export class ApiError extends Error {constructor(public status:number,message:string){super(message);}}
export function isLocalSite(){return typeof window!=='undefined'&&['localhost','127.0.0.1','[::1]'].includes(window.location.hostname);}
export function baseUrl(){return isLocalSite()?'http://127.0.0.1:8765':'';}
export function session(){let token=localStorage.getItem('pytorch-oj-session');if(!token){token=crypto.randomUUID();localStorage.setItem('pytorch-oj-session',token);}return token;}
export async function request(path:string,options:RequestInit={},signal?:AbortSignal){
  const base=baseUrl();if(!base)throw Error('请在电脑上启动本地练习服务。');
  const response=await fetch(base+path,{...options,credentials:'omit',headers:{'Content-Type':'application/json','X-OJ-Session':session(),...options.headers},signal});
  const data=await response.json();if(!response.ok)throw new ApiError(response.status,typeof data.detail==='string'?data.detail:'请求未完成，请稍后重试。');return data;
}
export async function health(signal?:AbortSignal):Promise<Health>{return request('/api/health',{},signal);}
async function pause(ms:number,signal:AbortSignal){
  if(signal.aborted)throw new DOMException('Cancelled','AbortError');
  await new Promise<void>((resolve,reject)=>{const abort=()=>{clearTimeout(timer);reject(new DOMException('Cancelled','AbortError'));};const timer=setTimeout(()=>{signal.removeEventListener('abort',abort);resolve();},ms);signal.addEventListener('abort',abort,{once:true});});
}
export async function pollJob(id:string,onStatus:(status:string)=>void,signal:AbortSignal):Promise<JudgeResult>{
  for(;;){
    try{const result=await request('/api/jobs/'+encodeURIComponent(id),{},signal);onStatus(result.status);if(result.status==='done')return result.result;}
    catch(error){if(error instanceof TypeError||error instanceof ApiError&&error.status>=500){onStatus('connecting');await pause(1500,signal);continue;}throw error;}
    await pause(700,signal);
  }
}
export async function judge(payload:{kind:'example'|'run'|'submit';track?:'pytorch'|'agent';problemId?:string;taskKey?:string;code:string},onStatus:(status:string)=>void,signal:AbortSignal,onAccepted?:(id:string)=>void):Promise<JudgeResult>{
  const body=JSON.stringify({...payload,requestId:crypto.randomUUID()});let job;
  for(;;){
    try{job=await request('/api/jobs',{method:'POST',body},signal);break;}
    catch(error){if(error instanceof TypeError||error instanceof ApiError&&(/队列已满|已有代码正在执行/.test(error.message))){onStatus('queued');await pause(1500,signal);continue;}throw error;}
  }
  onAccepted?.(job.id);return pollJob(job.id,onStatus,signal);
}
export async function exportAgentProject(){
 const response=await fetch(baseUrl()+'/api/agent/project',{method:'POST',credentials:'omit',headers:{'Content-Type':'application/json','X-OJ-Session':session()}});
 if(!response.ok){const data=await response.json();throw Error(data.detail||'项目导出失败。');}
 return response.blob();
}
