# MAA v6.21.3 / macOS 13.7.4（Apple Silicon）相容移植

**目前狀態：v6.21.1 是已完成實機驗收的穩定基準；v6.21.3 是獨立更新分支，尚待 GitHub Actions 完整編譯及 macOS 13.7.4 實機驗收。**

本專案從官方 `MaaAssistantArknights/MaaRelease` 下載 v6.21.3 macOS universal DMG，從主程式倉庫 `MaaAssistantArknights/MaaAssistantArknights` 取得同 tag 的 C API 標頭；兩個來源分開鎖定。使用已驗收的 macOS 13 GUI 相容性原始碼，目標為 Apple Silicon arm64、最低部署版本 macOS 13.3。使用者無須升級本機 macOS。

## 版本管理

- 已驗收穩定基準：`v6.21.1`。
- 本次更新目標：`v6.21.3`。
- 版本及官方 DMG SHA-256：`config/release-manifest.json`。
- GitHub Actions 的手動輸入預設值與 manifest 由 `tests/test_release_manifest.py` 檢查，避免版本號漂移。
- 未在 manifest 登記官方 DMG 檔名及 SHA-256 的版本會在下載前停止，不會自動改用其他版本。

## v6.21.3 更新範圍

本次更新核心、執行時框架及資源，保留已在 macOS 13.7.4 實機驗收的 Mac GUI 相容性原始碼。官方 v6.21.3 發行說明沒有列出獨立的 MaaMacGui 專屬變更；PC 客戶端退出等功能不視為 Mac GUI 功能。詳見 `V6.21.3-CHANGELOG-繁中.md`。

## 建置方式

GitHub Actions：`Actions` → `Build MAA for macOS 13` → `Run workflow`，選擇 `update/v6.21.3` 分支，`core_tag` 預設為 `v6.21.3`。

建置會：

1. 從 MaaRelease 下載官方 DMG，失敗時最多重試 3 次，並驗證官方 SHA-256。
2. 從主程式倉庫下載同一 tag 的 `include/` 標頭，逐檔驗證 Git blob SHA-1。
3. 從該版本官方 DMG 提取 Core、框架及資源。
4. 檢查 API 宣告與 arm64 匯出符號。
5. 執行 C、Objective-C++、Swift 匯入檢查。
6. 建立 arm64 XCFramework，編譯 GUI，檢查所有 Mach-O 最低系統版本及簽名。
7. 產生 `MAA-macOS13-arm64-candidate`。

## 驗收規則

- v6.21.1 `main` 分支保持不變，所有 v6.21.3 修改在 `update/v6.21.3` 分支完成。
- GitHub Actions 成功只代表雲端編譯完成；仍須在 macOS 13.7.4 真機測試 GUI 啟動、資源初始化、遊戲連線及任務執行。
- 實機驗收通過後才合併到 `main`，並建立 `macos13-v6.21.3` 標籤。

## 歷史相容性修正

前八輪修正及已驗收基準的詳細記錄保留在 `GUI-changes.diff`、各版 build notes 與 `scripts/`。不要在 v6.21.3 更新時刪除 Objective-C++ Core API 橋接、macOS 13 API 替代方案、核心標頭檢查或避免 `MaaCore` module map 重複的建置設定。
