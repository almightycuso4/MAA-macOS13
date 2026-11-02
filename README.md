# MAA macOS 13.3+ ARM64 相容移植候選版

狀態：已修改原始碼，尚未通過 Xcode 編譯或 macOS 13 實機測試。這是第一次雲端編譯用的候選包，不是可直接安裝的 App。

目標機：Apple Silicon、macOS 13.7.4。使用者已確認所檢查的已安裝版本是 v6.21.1；本包以該版本作為核心、資源及標頭來源。最低部署目標採用 13.3，與已檢查的 MaaCore/MaaUtils 一致。

## 已做的修改

- 三個 Observation 模型改為 Combine ObservableObject，加入 Published 屬性與巢狀模型通知轉發。
- SwiftUI 環境注入、綁定及物件生命週期改為 macOS 13 支援的版本。
- 新版雙參數 onChange 改用相容修飾器，保留初始回呼與舊值／新值。
- 檔案樹透過 Combine 訂閱展開事件。
- macOS 13 的設定按鈕使用 AppKit；較新系統保留 SettingsLink。
- 替換 smooth 動畫及 rect 簡寫；新預覽巨集不參與正式編譯。
- 停用 Sparkle 程式更新，避免相容版被官方 macOS 14 版本覆蓋；保留資源更新及其設定頁。
- 提供 ARM64 雲端建置流程，檢查輸出與附帶二進位檔宣告的最低系統版本。

## 第一次使用 GitHub Actions 編譯

1. 在 GitHub 建立空白私人倉庫，例如 `maa-macos13`；建立時不要加入 README。
2. 解壓本包。在終端執行（把 YOUR_ACCOUNT 換成你的 GitHub 帳號）：

```bash
cd ~/Downloads/MAA-macOS13
git init
git add .
git commit -m "Add macOS 13 compatibility candidate"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/maa-macos13.git
git push -u origin main
```

若 Git 要求驗證身分，使用你現有的 GitHub 憑證管理器或 GitHub Desktop 登入；GitHub 帳號密碼不能當作 HTTPS Git 密碼。亦可用 GitHub Desktop 將此資料夾建立為本機倉庫，再 Publish repository。

3. 開啟該倉庫的 Actions → Build MAA for macOS 13 → Run workflow。
4. `core_tag` 預設 `v6.21.1`，會從官方 Release 下載完整 DMG，並取得同一 tag 的 C 標頭；不需要上傳你的 App 或帳號資料。
5. 成功時下載 `MAA-macOS13-arm64-candidate`；解壓 artifact 後再解壓內層 ZIP 才會得到 MAA.app。
6. 失敗時下載 `build-logs`，把 build.log 提供給協作者繼續修正。不要只改最低版本數字跳過檢查。

編譯機使用較新 macOS/Xcode，你的 macOS 13 電腦不安裝 Xcode，也不用升級。

## 編譯與驗證邊界

目前 GUI 是使用者提供的 master 快照，未必與 v6.21.1 的核心 API 完全吻合。流程固定從同一 release 取得核心和標頭，若 API 不匹配會在編譯／連結階段停止，不會偽造標頭強行通過。屆時需根據具體缺失 API 選擇回移植 GUI 呼叫或另一個仍相容 13 的核心版本。

新 Swift 語法保留，交由 Xcode 26 系列編譯。JBird 沿用上游 xcode-26 分支；外部 Swift 套件的實際解析版本會隨 build-logs 一起保存。套件的系統需求與新 SDK 的可用性錯誤需以第一次 Xcode 編譯結果為準。

最低系統版本檢查只驗證二進位檔的宣告，不能代替 macOS 13 真機測試。此環境為 Linux，已完成 shell 語法、Python 語法與原始碼變更檢查，未執行 Xcode。

## 真機測試

先保留原本 MAA.app，候選版先從獨立資料夾啟動。兩者使用相同的 Bundle ID，因此應先備份原有設定。候選版採本機 ad-hoc 簽名，沒有 Developer ID 公證；首次開啟若被攔截，用 Finder 右鍵 → 打開。

依序確認：啟動、設定頁、資源載入、PlayCover/ADB 連接、單一日常任務、日誌更新、作業目錄展開、作業集選取、關閉程式。若有閃退，保留 macOS 的崩潰報告；只通過編譯仍不能稱作實機可用版。

## 來源

GUI 基於使用者上傳的 MaaMacGui-master.zip。原始專案：https://github.com/MaaAssistantArknights/MaaMacGui

核心與執行資源由流程從官方專案下載：https://github.com/MaaAssistantArknights/MaaAssistantArknights

修改不代表上游官方支援；完整修改差異見 GUI-changes.diff。
