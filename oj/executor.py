import json
import os
import subprocess
import sys
import tempfile
import queue
import threading
import time
from pathlib import Path

ROOT=Path(__file__).parent.resolve()
def windows_job(pid):
    """Cap the exercise process and reclaim it when the local service closes."""
    if os.name!='nt':return None
    import ctypes
    from ctypes import wintypes
    class BASIC(ctypes.Structure):
        _fields_=[('ProcessUserTimeLimit',ctypes.c_int64),('JobUserTimeLimit',ctypes.c_int64),('LimitFlags',wintypes.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),('ActiveProcessLimit',wintypes.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',wintypes.DWORD),('SchedulingClass',wintypes.DWORD)]
    class IO(ctypes.Structure):
        _fields_=[(name,ctypes.c_uint64) for name in ['ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount']]
    class EXTENDED(ctypes.Structure):
        _fields_=[('BasicLimitInformation',BASIC),('IoInfo',IO),('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR];api.CreateJobObjectW.restype=wintypes.HANDLE
    api.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
    api.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE]
    api.CloseHandle.argtypes=[wintypes.HANDLE]
    api.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];api.OpenProcess.restype=wintypes.HANDLE
    process_handle=api.OpenProcess(0x0100|0x0001|0x0400,False,pid)
    handle=api.CreateJobObjectW(None,None);info=EXTENDED()
    info.BasicLimitInformation.LimitFlags=0x2000|0x100|0x8
    info.BasicLimitInformation.ActiveProcessLimit=1;info.ProcessMemoryLimit=1024*1024*1024
    assigned=process_handle and handle and api.SetInformationJobObject(handle,9,ctypes.byref(info),ctypes.sizeof(info)) and api.AssignProcessToJobObject(handle,process_handle)
    if process_handle:api.CloseHandle(process_handle)
    if not assigned:
        if handle:api.CloseHandle(handle)
        raise RuntimeError('无法给本地判题进程设置限制。')
    return lambda:api.CloseHandle(handle)

def execute(payload,timeout=None):
    timeout=timeout or float(os.environ.get('OJ_TIMEOUT_SECONDS','20'))
    env={k:v for k,v in os.environ.items() if k in {'SYSTEMROOT','WINDIR','PATH','TEMP','TMP','LOCALAPPDATA'}}
    env.update(PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OJ_TIMEOUT_SECONDS=str(timeout))
    cleanup=None;proc=None;started=time.monotonic();execution_started=None
    with tempfile.TemporaryDirectory(prefix='pytorch-oj-') as scratch:
        entry='worker_entry.py'
        command=[sys.executable,'-I','-B','-u',str(ROOT/entry)]
        try:
            proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=scratch,env=env,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            handshake=queue.Queue(maxsize=1)
            threading.Thread(target=lambda:handshake.put(proc.stdout.readline()),daemon=True).start()
            try:ready=json.loads(handshake.get(timeout=min(8,timeout)))
            except queue.Empty:raise subprocess.TimeoutExpired(command,timeout)
            cleanup=windows_job(ready['workerPid'])
            prepared=queue.Queue(maxsize=1)
            threading.Thread(target=lambda:prepared.put(proc.stdout.readline()),daemon=True).start()
            try:prepared_message=json.loads(prepared.get(timeout=60))
            except queue.Empty:raise subprocess.TimeoutExpired(command,60)
            if prepared_message.get('workerReady') is not True:raise RuntimeError('本地 Python 环境未能准备完成。')
            execution_started=time.monotonic()
            stdout,stderr=proc.communicate(json.dumps(payload,ensure_ascii=False),timeout=timeout)
            if proc.returncode in {-14,142}:return {'verdict':'TLE','message':f'超过 {timeout:g} 秒时间限制。','cases':[],'elapsedMs':round((time.monotonic()-execution_started)*1000)}
            if proc.returncode!=0:return {'verdict':'RE','message':'判题进程异常退出，可能超过内存限制。','cases':[],'diagnostic':stderr[-1000:]}
            result=json.loads(stdout)
            result['startupMs']=round((execution_started-started)*1000)
            return result
        except subprocess.TimeoutExpired:
            elapsed=round((time.monotonic()-execution_started)*1000) if execution_started else None
            if cleanup:cleanup();cleanup=None
            if proc:
                if proc.poll() is None:proc.kill()
                try:proc.communicate(timeout=2)
                except Exception:pass
            if execution_started is None:return {'verdict':'SYSTEM','message':'本地 Python 环境准备超时，请稍后重试。','cases':[]}
            return {'verdict':'TLE','message':f'超过 {timeout:g} 秒时间限制。','cases':[],'elapsedMs':elapsed}
        except Exception as error:
            if cleanup:cleanup();cleanup=None
            if proc and proc.poll() is None:
                proc.kill()
                try:proc.communicate(timeout=2)
                except Exception:pass
            return {'verdict':'SYSTEM','message':f'判题服务不可用：{type(error).__name__}','cases':[],'diagnostic':str(error)}
        finally:
            if cleanup:cleanup()
