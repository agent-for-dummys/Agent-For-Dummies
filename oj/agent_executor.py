import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from executor import windows_job


def execute_project(payload, on_event=lambda event: None, on_files=lambda files: None):
    timeout = 120 if payload['mode'] == 'live' else 30
    started = time.monotonic()
    env = {key: value for key, value in os.environ.items() if key in {'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'LOCALAPPDATA'}}
    env.update(PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1', LANGSMITH_TRACING='false')
    cleanup = None
    with tempfile.TemporaryDirectory(prefix='mini-pi-run-') as scratch:
        root = Path(scratch)
        for name, content in payload['files'].items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
        config_text = payload['files'].get('.env', '')
        from dotenv import dotenv_values
        import io
        secrets = [value for key, value in dotenv_values(stream=io.StringIO(config_text), interpolate=False).items()
                   if value and ('KEY' in key.upper() or 'SECRET' in key.upper())]
        def clean(value):
            if isinstance(value,dict):return {key:clean(item) for key,item in value.items()}
            if isinstance(value,list):return [clean(item) for item in value]
            if isinstance(value,str):
                for secret in secrets:value=value.replace(secret,'[redacted]')
            return value
        proc = subprocess.Popen([sys.executable, '-I', '-B', '-u', str(Path(__file__).with_name('agent_worker_entry.py'))],
                                cwd=scratch, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding='utf-8', errors='replace', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        messages = queue.Queue()
        output_thread=threading.Thread(target=lambda: [messages.put(line) for line in proc.stdout], daemon=True)
        output_thread.start()
        diagnostics = []
        error_thread=threading.Thread(target=lambda: [diagnostics.append(line) for line in proc.stderr], daemon=True)
        error_thread.start()
        try:
            handshake = json.loads(messages.get(timeout=8))
            cleanup = windows_job(handshake['workerPid'])
            proc.stdin.write(json.dumps({key: value for key, value in payload.items() if key not in {'files','cancel_event'}}, ensure_ascii=False))
            proc.stdin.close()
            while time.monotonic() - started < timeout:
                if payload.get('cancel_event') and payload['cancel_event'].is_set():
                    return {'verdict': 'CANCELLED', 'message': '运行已停止。', 'cases': []}
                try:
                    message = json.loads(messages.get(timeout=.15))
                except queue.Empty:
                    if proc.poll() is not None:
                        return {'verdict': 'RE', 'message': '运行进程异常退出。', 'cases': []}
                    continue
                if 'event' in message:
                    on_event(clean(message['event']))
                elif 'updates' in message:
                    on_files(clean(message['updates']))
                elif 'result' in message:
                    result = clean(message['result'])
                    result['elapsedMs'] = round((time.monotonic() - started) * 1000)
                    return result
            return {'verdict': 'TLE', 'message': f'运行超过 {timeout} 秒。', 'cases': []}
        except Exception as error:
            return {'verdict': 'SYSTEM', 'message': f'运行未完成：{type(error).__name__}', 'cases': []}
        finally:
            if cleanup:
                cleanup()
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=3)
            output_thread.join(timeout=1)
            error_thread.join(timeout=1)
            proc.stdout.close()
            proc.stderr.close()
