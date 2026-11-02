# MAA v6.21.1 / macOS 13.7.4（Apple Silicon）相容移植

**狀態：第八版原始碼候選。尚未完成 GitHub Actions 全量編譯與 macOS 13.7.4 實機測試。不是已可執行的 MAA.app。**

本專案將 GUI 部署版本設為 macOS 13.3，使用官方 MAA v6.21.1 同版本核心、資源及標頭，以 GitHub Actions macos-26／Xcode 26 進行 arm64 建置；不要求使用者升級本機 macOS。

## 第八次修正：移除 105 MB 全量原始碼下載

第七次 `build-logs (1)(1).zip` 在 `curl` 下載官方 v6.21.1 標籤的原始碼壓縮包時發生 `curl: (56) Recv failure: Operation timed out`。此時尚未進入 GUI 編譯；這次的日誌**無法驗證或否定第七版的模組衝突修正**。

先前腳本下載約 105 MB 的整個原始碼壓縮包，只是為了取得 `include/` 裡的官方 C API 標頭。改為 `scripts/fetch_core_headers.py` 使用 GitHub Contents API 逐個下載該標籤 `include/` 的檔案，遞迴保留路徑，逐一驗證檔案大小及 Git blob SHA-1，遇到網路暫時故障才重試，並把結果保存到 `logs/core-header-download.txt`。GitHub Actions 使用已存在的 `GH_TOKEN`（`contents: read`），不需要個人金鑰；對錯誤的 tag 或持續的 API 錯誤會停止，不改抓最新版本。

**本版未修改 GUI、核心橋接、Xcode 工程或第七版已修正的模組搜尋路徑。** 已通過 `bash -n`、`py_compile` 及下載器 7 個離線單元測試。現有環境沒有 GitHub 連線與 macOS/Xcode，故尚未對官方 API 實際下載，也尚未驗證第八次完整編譯。

## 第七次修正

第六次 GitHub Actions `build-logs(4).zip` 顯示 `module 'MaaCore'` 重複定義，兩份模組映射分別在 `work/headers/module.modulemap` 及 `work/DerivedData/Build/Products/Release/include/module.modulemap`。此前 `scripts/build.sh` 將原始標頭目錄設為整個 Xcode 建置的全域 `HEADER_SEARCH_PATHS`，Xcode 又會將 XCFramework 的模組映射加入衍生產出目錄，因此在同一個 Clang 模組搜尋環境出現衝突。依賴掃描失敗後其他系統／套件模組也連鎖報錯。

**修補：移除全域 `HEADER_SEARCH_PATHS` 設定，改由 Xcode 自動取得已連結 `MaaCore.xcframework` 的標頭與模組映射。** 獨立的 C、Objective-C++、Swift 核心 API 檢查仍在正式 Xcode 建置前進行。未修改核心版本及 GUI 核心 API 呼叫。

前六次已修改 GUI 對 macOS 14 的 Observation／SwiftUI API 使用，以及 v6.21.1 擴充 C API 的 Objective-C++ 橋接；細節見各輪說明文件及 `GUI-changes.diff`。

## 操作及驗收

見 `UPDATE-GITHUB-繁中.txt`。推送新提交後，使用 GitHub 網頁 `Actions` → `Build MAA for macOS 13` → `Run workflow`，設定 `core_tag=v6.21.1`。

- 編譯成功：下載 `MAA-macOS13-arm64-candidate`，於 macOS 13.7.4 真機測試啟動、設定、資源載入、裝置連線與基本任務。
- 編譯失敗：上傳該次執行的 `build-logs` ZIP；依最先出現的實際錯誤分析，而不是把後續大量連鎖錯誤當成獨立問題。

本地驗證：`bash -n scripts/build.sh`、`python3 -m py_compile`、`python3 -m unittest discover -s tests -p test_fetch_core_headers.py`（7 項通過）。工作環境沒有 macOS/Xcode，因此仍不能聲稱成功完成完整編譯或實機驗證。
