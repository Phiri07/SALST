#!/usr/bin/env python3
import subprocess,sys,signal,os
from pathlib import Path
root=Path(__file__).resolve().parent
procs=[subprocess.Popen([sys.executable,str(root/f'tag{i}.py')],cwd=root,env=os.environ.copy()) for i in range(1,5)]
print('Started four software tags. Press Ctrl+C to stop.',flush=True)
try:
 for p in procs:p.wait()
except KeyboardInterrupt:pass
finally:
 for p in procs:p.terminate()
 for p in procs:
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill()
