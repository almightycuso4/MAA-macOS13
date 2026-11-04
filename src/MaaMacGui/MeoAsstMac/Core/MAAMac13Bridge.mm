// Swift/C bridge for the official MAA extension API.
// Use the official release header in C++ mode; preflight validates it.
// Compiled by the GUI target: no replacement declarations for upstream
// symbols, no ABI guesses, and no substitute or omitted functionality.
// In the pinned MAA Core release, the extension declarations are guarded by
// #if ASST_WITH_EXTRA_CALLERS. The official dylib exports both entry points,
// but clients must explicitly enable their declarations before including the
// extension header. Keep the flag local to this ObjC++ translation unit: the
// Swift-facing MaaCore module continues to import only plain C declarations.
#ifndef ASST_WITH_EXTRA_CALLERS
#define ASST_WITH_EXTRA_CALLERS 1
#endif
#if !ASST_WITH_EXTRA_CALLERS
#error "MAAMac13Bridge requires ASST_WITH_EXTRA_CALLERS=1"
#endif
#include "AsstCaller.h"
#include "AsstCallerExtra.h"
#include "MAAMac13Bridge.h"

extern "C" const char *MAAMac13GetMapLevelCode(const char *key) {
    return AsstGetMapLevelKey(key).code;
}

extern "C" const char *MAAMac13GetItemName(const char *id) {
    return AsstGetItemName(id);
}
