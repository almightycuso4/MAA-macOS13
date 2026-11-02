// Swift/C bridge for the official MAA extension API.
// Use the official release header in C++ mode; preflight validates it.
// Compiled by the GUI target: no replacement declarations for upstream
// symbols, no ABI guesses, and no substitute or omitted functionality.
#include "AsstCaller.h"
#include "AsstCallerExtra.h"
#include "MAAMac13Bridge.h"

extern "C" const char *MAAMac13GetMapLevelCode(const char *key) {
    return AsstGetMapLevelKey(key).code;
}

extern "C" const char *MAAMac13GetItemName(const char *id) {
    return AsstGetItemName(id);
}
