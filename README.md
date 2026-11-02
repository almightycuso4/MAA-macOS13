# MAA v6.21.1 / macOS 13 ARM64 相容移植

**狀態：第四次雲端編譯候選原始碼；尚未通過 GitHub Actions 編譯及 macOS 13 真機測試。不是可直接執行的 MAA.app。**

目標：Apple Silicon、macOS 13.7.4，不升級系統。沿用官方 v6.21.1 核心、同版本資源與標頭；GUI 使用 GitHub Actions macos-26／Xcode 26 編譯，部署目標設為 macOS 13.3。

## 第三次編譯日誌：實際發現

第三次日誌只剩兩個 Swift 編譯錯誤，均位於 `MeoAsstMac/Core/Maa.swift`：

- `AsstGetMapLevelKey` 未匯入 Swift（原第 34 行）。
- `AsstGetItemName` 未匯入 Swift（原第 44 行）。

`logs/core-api-check.txt` 已證實**兩者均在官方 v6.21.1 的 `AsstCallerExtra.h` 中有宣告，並由 arm64 `libMaaCore.dylib` 匯出**。問題位於 C→Swift 介面，不需要升級 macOS 或更換核心。`MaaCore` module umbrella 已包含 AsstCallerExtra.h；仍無法直接在 Swift 找到兩個函式，因此上一版單純增加標頭的修正不足。

## 第四次修正

1. `scripts/prepare_core_headers.py` 從官方標頭產生 `MAAMac13Bridge.h`：兩個 `static inline` C 函式呼叫真正的 `AsstGetMapLevelKey` 與 `AsstGetItemName`，提供 Swift 容易匯入的 `const char *` 回傳值，不偽造官方符號及宣告。
2. `Maa.swift` 透過 `MAAMac13GetMapLevelCode` / `MAAMac13GetItemName` 呼叫相容介面，保留原本查詢關卡代碼、物品名稱的業務行為。
3. Module umbrella 同時包含 `MaaCore.h`（若官方標頭存在），消除缺少該 header 的警告。
4. **在 Xcode 編譯 GUI 之前**新增 Clang C 語法與 Swift 匯入型別檢查，失敗時記錄 `core-c-import-check.txt` 或 `core-swift-import-check.txt` 供精確修正。

上次已修復的 Combine／協定／macOS 13 顏色相容問題均保留。未啟用官方 Sparkle 程式更新入口。

## 編譯、回報與驗證

請依 `UPDATE-GITHUB-繁中.txt` 把修補檔合併至**原有** GitHub 倉庫。不要重新建立倉庫。新建一筆 Actions workflow run（`core_tag=v6.21.1`），不要對舊執行結果按 `Re-run jobs`。

- 綠色成功：在 `Artifacts` 下載 `MAA-macOS13-arm64-candidate`，解壓後在 macOS 13.7.4 實機測試；先備份設定，勿覆蓋現有 MAA.app。
- 紅色失敗：在 `Artifacts` 下載 `build-logs` ZIP，上傳完整檔案。會含 `build.log`、核心 API 檢查、nm 匯出符號、C／Swift 匯入診斷（執行到該步驟時）。

**驗證範圍：**在本地 Linux 已使用模擬的 C API 標頭驗證橋接程式能通過 Clang 和 Swift 匯入型別檢查，並檢查 Python/Bash 語法。實際 v6.21.1 的 Apple 專用標頭、Xcode 編譯、動態連結與 macOS 13.7.4 實機運行，仍待下一次 Actions／實機檢驗。

官方來源：<https://github.com/MaaAssistantArknights/MaaAssistantArknights>、<https://github.com/MaaAssistantArknights/MaaMacGui>。


## 第五次修補（2026-11-02）

- 修正第四次編譯遇到的 `AsstCallerExtra.h` C 語言函式宣告不可見問題：改用 GUI 內 Objective-C++ 橋接來源，Swift 只讀取純 C 介面。
- 增加官方 C++ 標頭、C 介面、Swift 匯入的前置檢查與診斷日誌。
- 這是待 GitHub Actions 編譯及 macOS 13.7.4 實機測試的修正版原始碼，不是已驗證的 App。
