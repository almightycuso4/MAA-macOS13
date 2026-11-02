//  CheckForUpdatesView.swift
//  The official application updater installs macOS 14+ binaries.
//  Disable this view's update action in the macOS 13 compatibility build.

import Sparkle
import SwiftUI

struct CheckForUpdatesView: View {
    init(updater: SPUUpdater) {}

    var body: some View {
        Text("相容版本已停用程式自動更新；資源更新仍可使用。")
    }
}
