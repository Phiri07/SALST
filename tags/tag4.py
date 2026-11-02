#!/usr/bin/env python3
import subprocess,sys
raise SystemExit(subprocess.call([sys.executable,'tag.py','--tag','SALST-004','--seed','4']+sys.argv[1:]))
