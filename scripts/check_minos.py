#!/usr/bin/env python3
"""Check all Mach-O arm64 images, including framework helpers and dylibs.
This checks declared deployment targets, not missing imports or runtime behavior.
"""
import re
import subprocess
import sys
from pathlib import Path

def version(v):
    parts=tuple(map(int,v.split('.')))
    return parts+(0,)*(3-len(parts))

failed=[]
for p in sorted(Path(sys.argv[1]).rglob('*')):
    if not p.is_file() or p.is_symlink(): continue
    result=subprocess.run(['file','-b',str(p)],capture_output=True,text=True,check=True)
    if 'Mach-O' not in result.stdout: continue
    archs=subprocess.run(['lipo','-archs',str(p)],capture_output=True,text=True,check=True).stdout.split()
    if 'arm64' not in archs:
        # x86-only optional images are reported, not claimed arm64-compatible.
        print(f'NO ARM64: {p}: {" ".join(archs)}')
        continue
    result=subprocess.run(['otool','-arch','arm64','-l',str(p)],capture_output=True,text=True,check=True)
    match=re.search(r'cmd LC_BUILD_VERSION\b(?:(?!\nLoad command).)*?\bminos\s+([\d.]+)',result.stdout,re.S)
    if not match:
        match=re.search(r'cmd LC_VERSION_MIN_MACOSX\b(?:(?!\nLoad command).)*?\bversion\s+([\d.]+)',result.stdout,re.S)
    if not match:
        failed.append(f'No macOS deployment target: {p}'); continue
    minimum=match.group(1)
    print(f'{minimum}\t{p}')
    if version(minimum)>version('13.7.4'): failed.append(f'Requires {minimum}: {p}')
if failed:
    raise SystemExit('\n'.join(failed))
