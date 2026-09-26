#!/usr/bin/env python3
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]; R=ROOT/'results'
for p in list(R.iterdir()):
    if p.name=='README.md': continue
    shutil.rmtree(p) if p.is_dir() else p.unlink()
print('Cleaned generated results under',R)
