"""Private worker startup. -I disables user site packages and injected PYTHONPATH."""
import runpy
import sys
import os
import json
import signal
from pathlib import Path
for stream in (sys.stdin,sys.stdout,sys.stderr):
    stream.reconfigure(encoding='utf-8',errors='replace')
sys.path.insert(0,str(Path(__file__).parent.resolve()))
print(json.dumps({'workerPid':os.getpid()}),flush=True)
runpy.run_path(str(Path(__file__).with_name('worker.py')),run_name='__main__')
