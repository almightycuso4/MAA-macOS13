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
        issues.append(f'{symbol}: missing API name in release headers')
    if not exported:
        issues.append(f'{symbol}: missing exported arm64 symbol in official libMaaCore.dylib')

(logs / 'core-api-check.txt').write_text('\n'.join(lines + issues) + '\n')
print('\n'.join(lines), flush=True)
if issues:
    raise SystemExit('Core / GUI API mismatch at the chosen release: ' + '; '.join(issues))

# The extra API is exported by MaaCore but is not declared to a C
# translation unit in this release (see round-four Clang diagnostics).
# Expose only Swift-safe C entry points in the module. Their actual
# implementations are compiled as Objective-C++ in the GUI target, with the
# real release's AsstCallerExtra.h in a C++ compilation context.
bridge = headers / 'MAAMac13Bridge.h'
bridge.write_text("""// Generated C facade for the official MaaCore extension APIs.
#pragma once
#ifdef __cplusplus
extern "C" {
#endif
const char *MAAMac13GetMapLevelCode(const char *key);
const char *MAAMac13GetItemName(const char *id);
#ifdef __cplusplus
}
#endif
""")

# IMPORTANT: do not put AsstCallerExtra.h in the Swift Clang module:
# Swift imports C, while the extra API declarations are not visible there.
umbrella = headers / 'MAAModuleUmbrella.h'
umbrella.write_text(
    '// Swift-visible C interfaces only.\n'
    '#include "AsstCaller.h"\n'
    '#include "MAAMac13Bridge.h"\n'
)
(headers / 'module.modulemap').write_text(
    'module MaaCore {\n'
    '    header "AsstCaller.h"\n'
    '    header "MAAMac13Bridge.h"\n'
    '    export *\n'
    '}\n'
)

# Save exact upstream extra header for troubleshooting when its declarations
# differ across tags; the log should not rely on filename/text matching alone.
extra = headers / 'AsstCallerExtra.h'
if not extra.is_file():
    raise SystemExit('AsstCallerExtra.h is missing from the selected release')
(logs / 'core-extra-header.txt').write_bytes(extra.read_bytes())

# Verify C can import the facade, C++ can actually see the official symbols,
# and Swift can import the facade (before the full Xcode build).
probe_c = logs / 'core-api-probe.c'
probe_c.write_text(
    '#include "MAAModuleUmbrella.h"\n'
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
objcxx = Path(__file__).resolve().parent.parent / 'src/MaaMacGui/MeoAsstMac/Core/MAAMac13Bridge.mm'
if not objcxx.is_file():
    raise SystemExit(f'Missing Xcode source file: {objcxx}')
checks = [
    ('core-c-import-check.txt', ['clang', '-x', 'c', '-std=c11', '-fsyntax-only',
                                 '-I', str(headers), str(probe_c)]),
    ('core-cxx-bridge-check.txt', ['clang++', '-x', 'objective-c++', '-std=c++20',
                                  '-fsyntax-only', '-I', str(headers), str(objcxx)]),
    ('core-swift-import-check.txt', ['swiftc', '-typecheck', '-target',
                                     'arm64-apple-macos13.3', '-I', str(headers),
                                     str(probe_swift)]),
]
for log_name, cmd in checks:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    (logs / log_name).write_text(
        '$ ' + ' '.join(cmd) + '\n' + result.stdout + result.stderr
        + f'\nExit code: {result.returncode}\n'
    )
    if result.returncode:
        raise SystemExit(f'{log_name} failed; inspect attached build-logs')
    print(f'{log_name}: PASS', flush=True)
print('Swift Clang module contains C-only interfaces. C++ extension API checked.', flush=True)
