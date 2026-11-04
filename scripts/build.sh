#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
DEFAULT_MAA_CORE_TAG="$(python3 scripts/release_manifest.py --default)"
: "${MAA_CORE_TAG:=$DEFAULT_MAA_CORE_TAG}"
if [[ ! "$MAA_CORE_TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([.-][A-Za-z0-9.-]+)?$ ]]; then
  echo 'Invalid release tag' >&2; exit 1
fi
xcodebuild -version
swift --version
mkdir -p work/download build output logs
# Run offline regression tests before downloading any release artifacts.
python3 -m unittest discover -s tests -p 'test_*.py'
# Runtime and headers MUST come from the same tag. Never silently substitute latest.
IFS=$'\t' read -r CORE_DMG_NAME CORE_DMG_SHA256 RELEASE_REPOSITORY <<< "$(python3 scripts/release_manifest.py "$MAA_CORE_TAG")"
CORE_DMG_PATH="$PWD/work/download/$CORE_DMG_NAME"
# Release binaries live in MaaRelease; source headers are fetched separately
# from the matching tag in MaaAssistantArknights/MaaAssistantArknights.
asset_ready=0
for attempt in 1 2 3; do
  rm -f "$CORE_DMG_PATH"
  if gh release download "$MAA_CORE_TAG" --repo "$RELEASE_REPOSITORY" \
      --pattern "$CORE_DMG_NAME" --dir work/download \
      && printf '%s  %s\n' "$CORE_DMG_SHA256" "$CORE_DMG_PATH" | shasum -a 256 -c -; then
    asset_ready=1
    break
  fi
  echo "Official DMG download/checksum failed; attempt $attempt/3" >&2
  sleep $((attempt * 5))
done
[[ "$asset_ready" -eq 1 ]] || { echo 'Could not download a verified official MAA DMG' >&2; exit 1; }
# Only the matching release's public headers are needed; do not fetch the
# entire 100+ MB source archive. The Contents API returns each file's Git SHA
# and lets us validate the bytes before using them to build the XCFramework.
mkdir -p work/headers
python3 scripts/fetch_core_headers.py "$MAA_CORE_TAG" work/headers logs
mkdir -p work/mount
hdiutil attach "$CORE_DMG_PATH" \
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
# Import the actual public extension header(s) and verify that the binary
# exports the matching arm64 symbols. Diagnostics are preserved on failure.
python3 scripts/prepare_core_headers.py \
  work/headers \
  work/official.app/Contents/Frameworks/libMaaCore.dylib logs
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
# IMPORTANT: Do not add HEADER_SEARCH_PATHS=$PWD/work/headers here.
# xcodebuild stages the MaaCore XCFramework's module.modulemap under
# DerivedData/Build/Products/Release/include. The original work/headers also
# has a MaaCore module.modulemap for the isolated import probes above. Putting
# both directories on Xcode's global header search path makes Clang see two
# definitions of module MaaCore and breaks all Swift package dependency scans.
# The linked MaaCore.xcframework supplies its own headers to this target.
# A current GUI plus an older core can have an API mismatch; stop on compile/link
# errors rather than constructing an app from mismatched declarations.
xcodebuild -skipMacroValidation -project src/MaaMacGui/MeoAsstMac.xcodeproj -scheme MAA \
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
