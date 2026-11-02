# MAA v6.21.1 / macOS 13.7.4（Apple Silicon）相容移植

**狀態：第七版原始碼候選。尚未完成 GitHub Actions 全量編譯與 macOS 13.7.4 實機測試。不是已可執行的 MAA.app。**

本專案將 GUI 部署版本設為 macOS 13.3，使用官方 MAA v6.21.1 同版本核心、資源及標頭，以 GitHub Actions macos-26／Xcode 26 進行 arm64 建置；不要求使用者升級本機 macOS。

## 第七次修正

第六次 GitHub Actions `build-logs(4).zip` 顯示 `module 'MaaCore'` 重複定義，兩份模組映射分別在 `work/headers/module.modulemap` 及 `work/DerivedData/Build/Products/Release/include/module.modulemap`。此前 `scripts/build.sh` 將原始標頭目錄設為整個 Xcode 建置的全域 `HEADER_SEARCH_PATHS`，Xcode 又會將 XCFramework 的模組映射加入衍生產出目錄，因此在同一個 Clang 模組搜尋環境出現衝突。依賴掃描失敗後其他系統／套件模組也連鎖報錯。

**修補：移除全域 `HEADER_SEARCH_PATHS` 設定，改由 Xcode 自動取得已連結 `MaaCore.xcframework` 的標頭與模組映射。** 獨立的 C、Objective-C++、Swift 核心 API 檢查仍在正式 Xcode 建置前進行。未修改核心版本及 GUI 核心 API 呼叫。

前六次已修改 GUI 對 macOS 14 的 Observation／SwiftUI API 使用，以及 v6.21.1 擴充 C API 的 Objective-C++ 橋接；細節見各輪說明文件及 `GUI-changes.diff`。

## 操作及驗收

見 `UPDATE-GITHUB-繁中.txt`。推送新提交後，使用 GitHub 網頁 `Actions` → `Build MAA for macOS 13` → `Run workflow`，設定 `core_tag=v6.21.1`。

- 編譯成功：下載 `MAA-macOS13-arm64-candidate`，於 macOS 13.7.4 真機測試啟動、設定、資源載入、裝置連線與基本任務。
- 編譯失敗：上傳該次執行的 `build-logs` ZIP；依最先出現的實際錯誤分析，而不是把後續大量連鎖錯誤當成獨立問題。

本地驗證：`bash -n scripts/build.sh`、靜態核對原始 `xcodebuild` 命令及第六次日誌。工作環境沒有 macOS/Xcode，因此仍不能聲稱成功完成完整編譯或實機驗證。
