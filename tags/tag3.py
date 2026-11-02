#!/usr/bin/env python3
import subprocess,sys
raise SystemExit(subprocess.call([sys.executable,'tag.py','--tag','SALST-003','--seed','3']+sys.argv[1:]))
