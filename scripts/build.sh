#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${MAA_CORE_TAG:=v6.21.1}"
if [[ ! "$MAA_CORE_TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([.-][A-Za-z0-9.-]+)?$ ]]; then
  echo 'Invalid release tag' >&2; exit 1
fi
xcodebuild -version
swift --version
mkdir -p work/download build output logs
# Runtime and headers MUST come from the same tag. Never silently substitute latest.
gh release download "$MAA_CORE_TAG" --repo MaaAssistantArknights/MaaAssistantArknights \
  --pattern "MAA-${MAA_CORE_TAG}-macos-universal.dmg" --dir work/download
curl --fail --location --retry 3 \
  "https://github.com/MaaAssistantArknights/MaaAssistantArknights/archive/refs/tags/${MAA_CORE_TAG}.tar.gz" \
  -o work/core-source.tar.gz
mkdir -p work/core-source
tar -xzf work/core-source.tar.gz --strip-components=1 -C work/core-source
mkdir -p work/mount
hdiutil attach "work/download/MAA-${MAA_CORE_TAG}-macos-universal.dmg" \
  -nobrowse -readonly -mountpoint "$PWD/work/mount"
trap 'hdiutil detach "$PWD/work/mount" >/dev/null 2>&1 || true' EXIT
stock_app=$(find "$PWD/work/mount" -maxdepth 3 -name MAA.app -type d -print -quit)
[[ -n "$stock_app" ]] || { echo 'MAA.app missing in disk image'; exit 1; }
ditto "$stock_app" "$PWD/work/official.app"
hdiutil detach "$PWD/work/mount"
trap - EXIT
python3 scripts/check_minos.py work/official.app/Contents/Frameworks
# The project expects the main repository layout src/MaaMacGui, build, resource.
ditto work/official.app/Contents/Resources/resource resource
mkdir -p work/headers
ditto work/core-source/include work/headers
cat > work/headers/module.modulemap <<'MAP'
module MaaCore {
    header "AsstCaller.h"
    export *
}
MAP
python3 - <<'PY'
from pathlib import Path
import subprocess
root=Path.cwd(); libs=root/'work/official.app/Contents/Frameworks'
for name,pattern in [('MaaCore','libMaaCore.dylib'),('MaaUtils','libMaaUtils.dylib'),('OpenCV','libopencv_world*.dylib'),('ONNXRuntime','libonnxruntime*.dylib'),('fastdeploy_ppocr','libfastdeploy_ppocr.dylib')]:
    matches=list(libs.glob(pattern))
    if len(matches)!=1: raise SystemExit(f'{name}: expected one library; found {matches}')
    cmd=['xcodebuild','-create-xcframework','-library',str(matches[0])]
    if name=='MaaCore': cmd+=['-headers',str(root/'work/headers')]
    cmd+=['-output',str(root/'build'/f'{name}.xcframework')]
    subprocess.run(cmd,check=True)
PY
# A current GUI plus an older core can have an API mismatch; stop on compile/link
# errors rather than constructing an app from mismatched declarations.
xcodebuild -project src/MaaMacGui/MeoAsstMac.xcodeproj -scheme MAA \
  -configuration Release -destination 'generic/platform=macOS' \
  -derivedDataPath "$PWD/work/DerivedData" \
  ARCHS=arm64 ONLY_ACTIVE_ARCH=YES MACOSX_DEPLOYMENT_TARGET=13.3 \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO \
  MARKETING_VERSION="${MAA_CORE_TAG#v}" CURRENT_PROJECT_VERSION=1 \
  build
candidate="$PWD/work/DerivedData/Build/Products/Release/MAA.app"
[[ -d "$candidate" ]]
# Include any runtime-loaded libraries/plugins from the official app without
# overwriting the freshly built Swift packages and embedded frameworks.
rsync -a --ignore-existing work/official.app/Contents/Frameworks/ "$candidate/Contents/Frameworks/"
python3 scripts/check_minos.py "$candidate" | tee logs/minos.txt
# Ad-hoc signing for local execution, not Developer ID notarization.
codesign --force --deep --sign - "$candidate"
codesign --verify --deep --strict "$candidate"
ditto -c -k --sequesterRsrc --keepParent "$candidate" output/MAA-macOS13-arm64-candidate.zip
