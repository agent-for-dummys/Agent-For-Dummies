import asyncio
import importlib.metadata
import ipaddress
import json
import os
import time
import uuid
import threading
from collections import defaultdict,deque
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI,HTTPException,Request,Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field
from executor import execute

ORIGINS=['http://127.0.0.1:4173','http://localhost:4173','http://[::1]:4173']
COURSE=json.loads(Path(__file__).with_name('course.json').read_text(encoding='utf-8'))
PROBLEMS={p['id']:p for p in COURSE['problems']}
AGENT_COURSE=json.loads(Path(__file__).with_name('agent_course.json').read_text(encoding='utf-8'))
AGENT_CHAPTERS={p['id']:p for p in AGENT_COURSE['chapters']}
jobs={};rates=defaultdict(deque);queue=asyncio.Queue(maxsize=16);tasks=[]

async def runner():
    while True:
        job=await queue.get()
        try:
            job['status']='running'
            payload=job.pop('payload')
            if payload.get('track')=='agent':
                from agent_executor import execute_project
                from agent_workspace import write_file, valid_name
                def files_changed(changed):
                    from agent_workspace import path_for
                    for name,content in changed.items():
                        if valid_name(name) and name.startswith('workspace/'):
                            # Preserve reader edits made while the immutable run was executing.
                            path=path_for(job['owner'],name)
                            existing=path.read_text(encoding='utf-8') if path.exists() else None
                            if existing==payload['files'].get(name):
                                write_file(job['owner'],name,content)
                                payload['files'][name]=content
                            elif existing!=content:
                                job['events'].append({'type':'file_conflict','path':name,'message':'文件已有新的修改，请核对运行结果。'})
                job['result']=await asyncio.to_thread(execute_project,payload,lambda event:job['events'].append(event) if len(job['events'])<5000 else None,files_changed)
                files_changed(job['result'].pop('changedFiles',{}))
            else:
                job['result']=await asyncio.to_thread(execute,payload)
            job['status']='done';job['finishedAt']=time.time()
        except Exception:job.update(status='done',result={'verdict':'SYSTEM','message':'判题服务暂时不可用。','cases':[]})
        finally:queue.task_done()

@asynccontextmanager
async def lifespan(app):
    tasks.extend(asyncio.create_task(runner()) for _ in range(2))
    yield
    for task in tasks:task.cancel()
    await asyncio.gather(*tasks,return_exceptions=True)

app=FastAPI(title='PyTorch OJ',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=ORIGINS,allow_methods=['GET','POST'],allow_headers=['Content-Type','X-OJ-Session'])

@app.middleware('http')
async def boundary(request,call_next):
    from starlette.responses import JSONResponse
    origin=request.headers.get('origin')
    if origin and origin not in ORIGINS:return JSONResponse({'detail':'来源未授权。'},status_code=403)
    from urllib.parse import urlsplit
    host=urlsplit('//'+request.headers.get('host','')).hostname
    try:local=ipaddress.ip_address(request.client.host).is_loopback
    except ValueError:local=False
    if not local or host not in {'127.0.0.1','localhost','::1'}:return JSONResponse({'detail':'本地练习只接受本机请求。'},status_code=403)
    length=request.headers.get('content-length','0')
    max_bytes=1500000 if request.url.path.startswith('/api/agent/') else 24000
    if length.isdigit() and int(length)>max_bytes:return JSONResponse({'detail':'请求过大。'},status_code=413)
    if request.method=='POST':
        body=await request.body()
        if len(body)>max_bytes:return JSONResponse({'detail':'请求过大。'},status_code=413)
    return await call_next(request)

class BodyTooLarge(Exception):pass

class BodyLimit:
    def __init__(self,app,max_bytes=24000):self.app=app;self.max_bytes=max_bytes
    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        size=0
        async def limited_receive():
            nonlocal size
            message=await receive()
            if message['type']=='http.request':
                size+=len(message.get('body',b''))
                limit=1500000 if scope.get('path','').startswith('/api/agent/') else self.max_bytes
                if size>limit:raise BodyTooLarge()
            return message
        try:await self.app(scope,limited_receive,send)
        except BodyTooLarge:
            from starlette.responses import JSONResponse
            await JSONResponse({'detail':'请求过大。'},status_code=413)(scope,receive,send)

app.add_middleware(BodyLimit)

@app.get('/api/health')
async def health():
    ready=True;message=''
    try:version=importlib.metadata.version('torch')
    except importlib.metadata.PackageNotFoundError:version='未安装';ready=False;message='请先运行 npm run setup 安装本地环境。'
    agent_ready=True
    try:agent_version=importlib.metadata.version('langgraph');importlib.metadata.version('langgraph-checkpoint-sqlite');importlib.metadata.version('langchain-openai');importlib.metadata.version('langchain')
    except importlib.metadata.PackageNotFoundError:agent_version='未安装';agent_ready=False
    return {'service':'agent-for-dummies-oj','ready':ready,'engine':'PyTorch','version':version,'device':'CPU','message':message,'engines':{'pytorch':{'ready':ready,'version':version},'agent':{'ready':agent_ready,'version':agent_version}},'limits':{'seconds':20,'memoryMb':1024 if os.name=='nt' else None,'maxCodeBytes':20000}}

class Submission(BaseModel):
    kind:str
    track:str='pytorch'
    problemId:str|None=None
    code:str=Field(min_length=1,max_length=20000)
    requestId:str|None=Field(default=None,min_length=16,max_length=64)

def owner(token):
    if not token or len(token)<16 or len(token)>128:raise HTTPException(400,'缺少有效的练习会话。')
    return token

@app.post('/api/jobs',status_code=202)
async def submit(body:Submission,request:Request,x_oj_session:str=Header(default='')):
    session=owner(x_oj_session)
    if body.kind not in {'example','run','submit'}:raise HTTPException(400,'未知运行模式。')
    if body.track!='pytorch':raise HTTPException(400,'请使用组件项目运行接口。')
    if body.kind!='example' and body.problemId not in PROBLEMS:raise HTTPException(404,'题目不存在。')
    if len(body.code.encode('utf-8'))>20000:raise HTTPException(413,'代码超过 20 KB。')
    if body.requestId:
        existing=next((job for job in jobs.values() if job['owner']==session and job.get('requestId')==body.requestId),None)
        if existing:
            if existing.get('snapshot')!=body.model_dump():raise HTTPException(409,'这次请求已经提交，不能替换代码。')
            return {'id':existing['id'],'status':existing['status']}
    now=time.time()
    for key in [key for key,value in jobs.items() if value['status']=='done' and now-value.get('finishedAt',value['createdAt'])>900]:jobs.pop(key,None)
    for key in [key for key,times in rates.items() if not times or now-times[-1]>60]:rates.pop(key,None)
    bucket=rates[request.client.host]
    while bucket and now-bucket[0]>60:bucket.popleft()
    if len(bucket)>=20:raise HTTPException(429,'操作过于频繁，请稍后重试。')
    if queue.full() or len(jobs)>=500:raise HTTPException(503,'判题队列已满，请稍后重试。')
    job={'id':uuid.uuid4().hex,'owner':session,'status':'queued','createdAt':now,'requestId':body.requestId,'payload':body.model_dump(),'snapshot':body.model_dump()}
    bucket.append(now);jobs[job['id']]=job;queue.put_nowait(job)
    return {'id':job['id'],'status':'queued'}

@app.get('/api/jobs/{job_id}')
async def job_status(job_id:str,x_oj_session:str=Header(default='')):
    job=jobs.get(job_id)
    if not job or job['owner']!=owner(x_oj_session):raise HTTPException(404,'找不到这次运行。')
    return {key:job[key] for key in ('id','status','result','events') if key in job}

@app.get('/api/agent/files')
async def project_files(x_oj_session:str=Header(default='')):
    from agent_workspace import read_files
    return {'files':read_files(owner(x_oj_session))}

class FileSave(BaseModel):
    name:str
    content:str=Field(max_length=100000)

@app.post('/api/agent/files')
async def save_project_file(body:FileSave,x_oj_session:str=Header(default='')):
    from agent_workspace import write_file
    try:write_file(owner(x_oj_session),body.name,body.content)
    except ValueError as error:raise HTTPException(400,str(error))
    return {'saved':True}

@app.post('/api/agent/project')
async def project_export(x_oj_session:str=Header(default='')):
    from agent_workspace import export_project
    from fastapi.responses import Response
    data=export_project(owner(x_oj_session))
    return Response(data,media_type='application/zip',headers={'Content-Disposition':'attachment; filename="mini-pi.zip"'})

class ComponentRun(BaseModel):
    chapterId:str
    mode:str='check'
    question:str=Field(default='',max_length=4000)
    threadId:str=Field(default='main',min_length=1,max_length=64,pattern=r'^[A-Za-z0-9_-]+$')
    approval:bool|None=None
    requestId:str=Field(min_length=16,max_length=64)

@app.post('/api/agent/jobs',status_code=202)
async def component_run(body:ComponentRun,x_oj_session:str=Header(default='')):
    session=owner(x_oj_session)
    if body.chapterId not in AGENT_CHAPTERS or body.mode not in {'check','live','run'}:raise HTTPException(400,'组件或运行模式不正确。')
    if body.mode=='live' and not AGENT_CHAPTERS[body.chapterId].get('live'):raise HTTPException(400,'当前任务使用离线检查。')
    existing=next((j for j in jobs.values() if j['owner']==session and j.get('requestId')==body.requestId),None)
    if existing:
        if existing.get('snapshot')!=body.model_dump():raise HTTPException(409,'不能替换已经接受的运行。')
        return {'id':existing['id'],'status':existing['status']}
    if queue.full():raise HTTPException(503,'判题队列已满，请稍后重试。')
    if any(j['owner']==session and j['status']!='done' and j.get('events') is not None for j in jobs.values()):raise HTTPException(503,'已有代码正在执行，请等待当前运行完成。')
    from agent_workspace import read_files,directory,COURSE as PROJECT
    files=read_files(session)
    if body.mode!='live':files['.env']=PROJECT['files']['.env']
    payload={**body.model_dump(),'track':'agent','files':files,'dataRoot':str(directory(session)/'.runtime'),'cancel_event':threading.Event()}
    now=time.time()
    for key in [key for key,value in jobs.items() if value['status']=='done' and now-value.get('finishedAt',value['createdAt'])>900]:jobs.pop(key,None)
    if len(jobs)>=500:raise HTTPException(503,'判题队列已满，请稍后重试。')
    job={'id':uuid.uuid4().hex,'owner':session,'status':'queued','createdAt':now,'requestId':body.requestId,'payload':payload,'snapshot':body.model_dump(),'events':[],'cancel_event':payload['cancel_event']}
    jobs[job['id']]=job;queue.put_nowait(job)
    return {'id':job['id'],'status':'queued'}

@app.post('/api/agent/jobs/{job_id}/cancel')
async def cancel_component(job_id:str,x_oj_session:str=Header(default='')):
    job=jobs.get(job_id)
    if not job or job['owner']!=owner(x_oj_session) or 'cancel_event' not in job:raise HTTPException(404,'找不到这次运行。')
    job['cancel_event'].set()
    return {'cancelled':True}
