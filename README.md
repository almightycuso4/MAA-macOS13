# MAA macOS 13 兼容版

面向 Apple Silicon Mac 的 MAA（明日方舟小助手）macOS 13 兼容构建。当前稳定版本为 **v6.21.3**，无需将 macOS 升级到 14 或更高版本。

> 本项目是社区维护的非官方兼容构建，不代表 MAA 官方团队或鹰角网络发布、背书或提供支持。

## 当前版本

| 项目 | 信息 |
| --- | --- |
| MAA 版本 | v6.21.3 |
| 处理器架构 | Apple Silicon（arm64） |
| 编译最低系统版本 | macOS 13.3 |
| 实机验证环境 | Apple Silicon，macOS 13.7.4 |
| 当前状态 | 已完成实机功能验收 |

已在 macOS 13.7.4 实机完成以下验证：应用启动、核心初始化、资源加载、游戏连接及任务执行。该结果不代表已在所有 macOS 13 小版本和所有设备组合上完成测试。

## 下载与安装

1. 打开本仓库的 **Releases** 页面，下载标记为 `macOS 13 ARM64` 的 v6.21.3 安装压缩包。
2. 解压压缩包，取得 `MAA.app`。
3. 将 `MAA.app` 拖入 `/Applications`（应用程序）文件夹。
4. 首次启动时，如 macOS 阻止打开，在 Finder 中按住 Control 并点按 `MAA.app`，选择“打开”；如系统设置仍显示拦截提示，前往“系统设置 → 隐私与安全性”确认打开。

### 签名与首次启动提示

当前构建使用 ad-hoc 本地签名，不包含 Apple Developer ID 公证。首次启动时 macOS 可能显示安全性提示，这是签名方式导致的系统提示，不代表应用已通过 Apple 公证。

## v6.21.3 更新内容

本构建同步了官方 v6.21.3 核心与资源更新中的相关修正，包括：

- 修正黑流树海第五层返回地图时的错误滑动。
- 修正黑流树海点击出发后未等待场景加载的问题。
- 更新繁中服幸运墙活动界面的 OCR 适配。
- 修正繁中服干员“凯尔希·思衡托”的识别，并新增 `GALLUS²` 识别。
- 修正生息演算中“荧光棒”的 OCR 误读。

本构建没有同步上游 v6.21.3 的全部 Mac GUI 交互改动；任务右键排序等 GUI 变更不在本次移植范围内。PC 客户端专属功能不适用于本 macOS GUI 构建。

## 平台与功能范围

- 仅提供 Apple Silicon（arm64）构建；不支持 Intel Mac（x86_64）。
- 编译目标为 macOS 13.3，已实际验证的系统版本为 macOS 13.7.4。
- MaaCore、运行时框架和游戏资源来自 MAA 官方 v6.21.3 macOS 发布包；公开 C API 标头来自同版本主仓库标签。
- GUI 基于 MAA Mac GUI 上游代码，并包含本项目维护的 macOS 13 兼容性修改。
- 为避免应用自动更新覆盖为要求较新 macOS 的官方构建，本兼容版已停用 **应用程序自动更新**。请通过本仓库 Releases 手动更新应用；应用内资源更新功能仍可使用。
- 上游 GUI 的后续改动不会自动进入本项目。每次跟进 MAA 新版本时，都会单独检查 GUI、核心 API、资源和构建流程的差异。

## 构建方式

本仓库通过 GitHub Actions 构建，不要求维护者在本地安装完整的 MAA 编译环境。

1. 打开 GitHub 仓库的 **Actions** 页面。
2. 选择 **Build MAA for macOS 13** 工作流。
3. 点击 **Run workflow**。
4. 选择需要构建的分支，并确认 `core_tag` 是 `config/release-manifest.json` 中已登记的版本。
5. 点击 **Run workflow** 开始构建。
6. 成功后，在 **Artifacts** 下载 `MAA-macOS13-arm64-candidate`；失败时下载 `build-logs` 供排查。

### 构建校验

构建流程会执行以下检查：

- 从 MAA 官方发布仓库下载指定版本的 macOS DMG，并校验 SHA-256。
- 从 MAA 主仓库同一版本标签获取 `include/` 标头，逐文件校验 Git blob SHA-1。
- 检查核心 API 声明与 arm64 动态库导出符号。
- 执行 C、Objective-C++ 和 Swift 接口导入检查。
- 创建 XCFramework，使用 Xcode 编译 arm64 GUI。
- 检查应用内 Mach-O 文件的最低 macOS 版本，并验证签名。

`patches/macos13-gui-compatibility.patch` 保存 GUI 兼容性修改的差异参考；当前源码已经包含这些修改，构建时不会重复应用。

版本号、官方 DMG 文件名和 SHA-256 集中记录在 `config/release-manifest.json`。未登记校验值的版本会在下载前被拒绝，不会自动回退到其他版本。

### 本地回归测试

在仓库根目录运行：

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
bash -n scripts/build.sh
```

完整 GUI 构建依赖 macOS、Xcode、Apple 工具链及官方发布资源，推荐使用仓库内的 GitHub Actions 工作流。

## 跟进 MAA 新版本

新版本应在独立分支中移植和验收，不要直接覆盖已发布的稳定版本。

1. 从上游 MAA Release 确认新版本、macOS DMG 文件名和 SHA-256。
2. 在 `config/release-manifest.json` 登记该版本及校验值。
3. 更新 `.github/workflows/build.yml` 的默认 `core_tag`，并同步 `src/MaaMacGui/Version.xcconfig`。
4. 检查同版本核心标头、API、arm64 符号、GUI 上游差异和 macOS 13 API。
5. 运行本地回归测试，再执行 GitHub Actions。
6. 在 macOS 13.7.4 Apple Silicon 实机验证启动、资源、连接和任务。
7. 全部通过后，才合并到 `main` 并发布对应版本标签。

建议使用 `update/vX.Y.Z` 作为更新分支，稳定版本保留在 `main`。

## 问题反馈

提交 Issue 时请提供：

- MAA 版本和 macOS 版本；
- Mac 芯片型号（例如 M1、M2、M3 或 M4）；
- 可复现的操作步骤；
- MAA 日志或崩溃报告中与问题相关的部分。

请勿公开上传账号密码、访问令牌、个人配置或其他敏感信息。

## 上游项目与许可

- MAA 主仓库：<https://github.com/MaaAssistantArknights/MaaAssistantArknights>
- MAA 官方发布：<https://github.com/MaaAssistantArknights/MaaRelease/releases>
- MAA Mac GUI：<https://github.com/MaaAssistantArknights/MaaMacGui>
- MAA 用户协议：<https://github.com/MaaAssistantArknights/MaaAssistantArknights/blob/dev/terms-of-service.md>
- 本仓库源码许可：GNU AGPL-3.0-only，详见 [`LICENSE`](LICENSE)。

MAA 上游声明其软件使用 AGPL-3.0-only，并附带额外用户协议。MAA Logo 和相关美术素材不属于 AGPL 授权范围；本仓库不授予这些素材独立使用或商业使用的额外权利。第三方依赖仍适用各自的许可证。

《明日方舟》及相关游戏素材的权利归其各自权利人所有。本项目与鹰角网络及 MAA 官方团队没有隶属或授权关系。
