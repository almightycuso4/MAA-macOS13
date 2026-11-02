# MAA v6.21.1 / macOS 13 ARM64 相容移植

**狀態：第三次雲端編譯候選原始碼；尚未經 Xcode、macOS 13 真機驗證，不是已編譯的 App。**

目標機：Apple Silicon、macOS 13.7.4（22H420），不升級系統。最低部署版本為 macOS 13.3，官方核心、資源與 C 標頭固定同一 `core_tag`（預設 `v6.21.1`），保留原本 GitHub Actions 雲端建置方式。不要把本包覆蓋到已安裝的 MAA.app。

## 針對第二次日誌的修補

1. `LogStore` 協定中誤加的 `@Published` 已移除，模型自身的 `@Published` 保留。
2. 原 `UserDefaults+KVO.swift` 中 macOS 14 `ObservationRegistrar` 已撤除。唯一使用者 `CopilotContext.category` 現改為 `@Published`，沿用 `CopilotContentCategory` 偏好設定鍵；啟動時恢復分類、切換時儲存，並監看 `UserDefaults.didChangeNotification` 通知後同步 UI。原檔在 Xcode 專案中保留說明註解，避免遺留檔案參照。
3. `CapsulePicker` 改以 macOS 13 存在的 `NSColor.controlBackgroundColor` 處理未選取狀態，保留系統明暗模式。
4. `CheckForUpdatesView` 不再訂閱 Sparkle 的 `canCheckForUpdates`，維持停用程式更新；資源更新不受影響。
5. **核心 API 原因仍待實際確認**。建置階段執行 `scripts/prepare_core_headers.py`：從**同版本**核心原始碼的 `include` 找出 `AsstGetMapLevelKey` / `AsstGetItemName` 所在 C 標頭，產生 module umbrella header，並以 `nm -arch arm64 -gU` 確認官方 `libMaaCore.dylib` 有這兩個匯出符號。若沒有標頭或符號，將在此階段直接失敗並寫入 `logs/core-api-check.txt` / `logs/maacore-nm.txt`，不會偽造宣告，也不會改用不相容核心。

## 編譯入口

已存在的倉庫不必重建。依 `UPDATE-GITHUB-繁中.txt` 更新檔案，從 GitHub 網頁手動執行：

`Actions` → `Build MAA for macOS 13` → `Run workflow` → `core_tag=v6.21.1` → `Run workflow`。

- 綠色成功：下載 `MAA-macOS13-arm64-candidate`，解壓 artifact 再解壓內層 ZIP 得到 `MAA.app`。
- 紅色失敗：下載 `build-logs` ZIP，**不只**複製網頁錯誤文字；其中含 `build.log` 及核心 API 診斷檔。
- 建置使用 `macos-26` 與 Xcode 26；本地 macOS 13 不用安裝 Xcode。`-skipMacroValidation` 已保留，避免重遇第一次宏信任失敗。

## 能力邊界

Linux 上已通過 Swift parser 靜態語法檢查（非型別檢查）、Bash `-n`、Python 語法及核心檢查腳本的模擬測試；**未能下載 v6.21.1 的標頭或實際 dylib、無法在此環境執行 Xcode，也沒有實機測試結果**。即使未再出現第二次編譯錯誤，仍需檢查 Swift 型別、連結、最低部署版本、簽名與 macOS 13.7.4 真機的啟動、連線和作業。

本版本和官方版沿用 Bundle ID；真機測試前先備份原設定，在不同資料夾啟動，避免直接覆蓋原有的 App。

官方來源：
- https://github.com/MaaAssistantArknights/MaaAssistantArknights
- https://github.com/MaaAssistantArknights/MaaMacGui

完整 GUI 變更差異見 `GUI-changes.diff`。
