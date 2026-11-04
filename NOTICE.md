# 版权与来源说明

本仓库是 MAA 的非官方 macOS 13 兼容构建，基于 MAA 上游项目进行适配。当前公开版本为 v6.21.3；本仓库的 macOS 13 兼容性修改由维护者整理并于 2026-11-04 更新。

## 上游来源

- `MaaAssistantArknights/MaaAssistantArknights`：MAA 主项目、核心 API 标头及相关源码。
- `MaaAssistantArknights/MaaMacGui`：macOS 图形界面上游源码。
- `MaaAssistantArknights/MaaRelease`：官方 v6.21.3 macOS 发布包；本项目从中提取核心运行库、框架和资源。

本项目的 macOS 13 适配修改包括部署目标调整、macOS 13 API 兼容处理、MaaCore 扩展 API 的 Objective-C++ 桥接，以及停用不适用于本兼容构建的应用程序自动更新入口。

## 许可证

MAA 上游主项目声明使用 GNU Affero General Public License v3.0 only（`AGPL-3.0-only`），本仓库按该许可证发布，完整文本见 [`LICENSE`](LICENSE)。使用 MAA 时还应阅读并遵守上游附带的[用户协议](https://github.com/MaaAssistantArknights/MaaAssistantArknights/blob/dev/terms-of-service.md)。

MAA 上游明确说明，其 Logo 和相关美术素材不属于 AGPL-3.0 授权范围，相关权利由原权利人保留。AGPL 授权不构成对这些 Logo、美术或商标的独立授权，尤其不授予未经许可的商业使用权。

本构建包含的第三方框架和运行库保留其各自的版权声明与许可证。它们的来源版本为 MAA 官方 v6.21.3 macOS 发布包。

## 非官方声明

本项目由社区独立维护，不代表 MAA 官方团队或鹰角网络。`MAA`、`明日方舟`及相关商标、游戏素材的权利归各自权利人所有。
