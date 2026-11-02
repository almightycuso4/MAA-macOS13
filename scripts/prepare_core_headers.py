#!/usr/bin/env python3
"""Expose the matching release's public Core API to Swift, then verify symbols.

This script deliberately does NOT invent declarations for APIs absent from the
selected release. It runs in the macOS Actions job after the official DMG and
matching source tree have been downloaded.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit('Usage: prepare_core_headers.py HEADERS_DIR LIBMAACORE.DYLIB LOG_DIR')
headers = Path(sys.argv[1]).resolve()
core = Path(sys.argv[2]).resolve()
logs = Path(sys.argv[3]).resolve()
logs.mkdir(parents=True, exist_ok=True)
required = ('AsstGetMapLevelKey', 'AsstGetItemName')
header_files = sorted([*headers.rglob('*.h'), *headers.rglob('*.hpp')])
assert (headers / 'AsstCaller.h').is_file(), 'Missing AsstCaller.h from matching release'

results: dict[str, list[Path]] = {}
for symbol in required:
    regex = re.compile(r'\b' + re.escape(symbol) + r'\s*\(')
    matches = [p for p in header_files if regex.search(p.read_text(errors='replace'))]
    results[symbol] = matches

nm = subprocess.run(
    ['nm', '-arch', 'arm64', '-gU', str(core)],
    text=True, capture_output=True, check=False,
)
(logs / 'maacore-nm.txt').write_text(nm.stdout + '\n' + nm.stderr)
if nm.returncode:
    raise SystemExit('nm could not inspect arm64 exports of official MaaCore; see logs/maacore-nm.txt')

lines = [f'Core library: {core}', f'Headers directory: {headers}']
issues = []
for symbol in required:
    paths = results[symbol]
    exported = bool(re.search(r'\b_' + re.escape(symbol) + r'\s*$', nm.stdout, re.M))
    lines.append(f'{symbol}: header(s)={[str(p.relative_to(headers)) for p in paths]}, exported={exported}')
    if not paths:
        issues.append(f'{symbol}: missing public C declaration in release headers')
    if not exported:
        issues.append(f'{symbol}: missing exported arm64 symbol in official libMaaCore.dylib')

(logs / 'core-api-check.txt').write_text('\n'.join(lines + issues) + '\n')
print('\n'.join(lines), flush=True)
if issues:
    raise SystemExit('Core / GUI API mismatch at the chosen release: ' + '; '.join(issues))

# A function present in a Clang header is not necessarily importable by Swift:
# if a result uses a type the importer cannot represent, Swift can hide the
# entire declaration. A C-inline adapter exposes only simple pointer types,
# while using the upstream C declaration and ABI without guessing signatures.
# The C compiler validates this adapter, and Swift typechecking validates its
# import before the expensive full GUI build.
bridge = headers / 'MAAMac13Bridge.h'
bridge.write_text("""// Generated for Swift import of v6.21.1 Core extra APIs.
#pragma once
#include \"AsstCallerExtra.h\"
static inline const char *MAAMac13GetMapLevelCode(const char *key) {
    return AsstGetMapLevelKey(key).code;
}
static inline const char *MAAMac13GetItemName(const char *id) {
    return AsstGetItemName(id);
}
""")

# Including MaaCore.h also silences Clang's missing-umbrella warning. Include
# real release headers, never synthetic prototypes for upstream symbols.
included = {Path('AsstCaller.h'), Path('AsstCallerExtra.h'), Path('MAAMac13Bridge.h')}
if (headers / 'MaaCore.h').is_file():
    included.add(Path('MaaCore.h'))
for hits in results.values():
    included.update(p.relative_to(headers) for p in hits if p.suffix == '.h')
    if all(p.suffix != '.h' for p in hits):
        raise SystemExit('C API found only in C++ headers; not safe to import into Swift')

umbrella = headers / 'MAAModuleUmbrella.h'
umbrella.write_text(
    '// Generated from the official release public headers.\n'
    + ''.join(f'#include "{p.as_posix()}"\n' for p in sorted(included))
)
(headers / 'module.modulemap').write_text(
    'module MaaCore {\n'
    '    umbrella header "MAAModuleUmbrella.h"\n'
    '    export *\n'
    '}\n'
)

# Stop before GUI compilation if the extension header is not C-callable or
# Swift cannot import the adapter. Save full diagnostics to build-logs.
probe_c = logs / 'core-api-probe.c'
probe_c.write_text(
    '#include "MAAMac13Bridge.h"\n'
    'const char *maa_map(const char *x) { return MAAMac13GetMapLevelCode(x); }\n'
    'const char *maa_name(const char *x) { return MAAMac13GetItemName(x); }\n'
)
probe_swift = logs / 'core-api-probe.swift'
probe_swift.write_text(
    'import MaaCore\n'
    'func maaMap(_ key: String) -> String? {\n'
    '    let ptr = key.withCString { MAAMac13GetMapLevelCode($0) }\n'
    '    return ptr.map { String(cString: $0) }\n'
    '}\n'
    'func maaName(_ key: String) -> String? {\n'
    '    let ptr = key.withCString { MAAMac13GetItemName($0) }\n'
    '    return ptr.map { String(cString: $0) }\n'
    '}\n'
)
for log_name, cmd in [
    ('core-c-import-check.txt', ['clang', '-x', 'c', '-std=c11', '-fsyntax-only',
                                   '-I', str(headers), str(probe_c)]),
    ('core-swift-import-check.txt', ['swiftc', '-typecheck', '-target',
                                       'arm64-apple-macos13.3', '-I', str(headers),
                                       str(probe_swift)]),
]:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    (logs / log_name).write_text(
        '$ ' + ' '.join(cmd) + '\n' + result.stdout + result.stderr
        + f'\nExit code: {result.returncode}\n'
    )
    if result.returncode:
        raise SystemExit(f'{log_name} failed; inspect attached build-logs')
    print(f'{log_name}: PASS', flush=True)
print('Clang module umbrella headers:', *(str(p) for p in sorted(included)), sep='\n  ')
