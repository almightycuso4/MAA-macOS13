//
//  MeoAsstMacApp.swift
//  MeoAsstMac
//
//  Created by hguandl on 8/10/2022.
//

import Sparkle
import SwiftUI

@main
struct MeoAsstMacApp: App {
    @NSApplicationDelegateAdaptor private var appDelegate: AppDelegate
    @StateObject private var appViewModel: MAAViewModel
    @StateObject private var newViewModel: NewViewModel

    private let updaterController: SPUStandardUpdaterController
    private let updaterDelegate = MaaUpdaterDelegate()

    init() {
        let viewModel = MAAViewModel()
        let newModel = NewViewModel(parent: viewModel)
        _appViewModel = StateObject(wrappedValue: viewModel)
        _newViewModel = StateObject(wrappedValue: newModel)
        updaterController = .init(startingUpdater: false, updaterDelegate: updaterDelegate, userDriverDelegate: nil)
        appDelegate.beforeTermination = {
            await newModel.waitLogStoreToFinish()
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appViewModel)
                .environmentObject(newViewModel)
                .onAppear {
                    TaskTimerManager.shared.connectToModel(viewModel: appViewModel)
                }
        }
        .commands {
            CommandGroup(replacing: .newItem) {
                OpenLogFileView()
            }
            // Binary updates point to upstream macOS 14+ builds.
            // Resource updates remain available from the sidebar.
            SidebarCommands()
            TaskCommands(viewModel: appViewModel)
        }

        Settings {
            TabView {
                ConnectionSettingsView()
                    .tabItem {
                        Label("连接设置", systemImage: "rectangle.connected.to.line.below")
                    }

                GameSettingsView()
                    .tabItem {
                        Label("游戏设置", systemImage: "gamecontroller")
                    }


                UpdaterSettingsView(updater: updaterController.updater)
                    .tabItem {
                        Label("更新设置", systemImage: "square.and.arrow.down")
                    }

                SystemSettingsView()
                    .tabItem {
                        Label("系统设置", systemImage: "wrench.adjustable")
                    }
            }
            .environmentObject(appViewModel)
            .frame(maxWidth: 360, minHeight: 240)
        }
    }
}

final class MaaUpdaterDelegate: NSObject, SPUUpdaterDelegate {
    @AppStorage("MaaUseBetaChannel") private var useBetaChannel = false

    func allowedChannels(for updater: SPUUpdater) -> Set<String> {
        if useBetaChannel {
            return Set(["beta"])
        } else {
            return Set()
        }
    }
}

private class AppDelegate: NSObject, NSApplicationDelegate {
    fileprivate var beforeTermination: (() async -> Void)?
    private var terminationTask: Task<Void, Never>?

    func applicationWillFinishLaunching(_ notification: Notification) {
        NSWindow.allowsAutomaticWindowTabbing = false
    }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        guard let beforeTermination else { return .terminateNow }
        if terminationTask != nil { return .terminateLater }

        terminationTask = Task {
            await beforeTermination()
            sender.reply(toApplicationShouldTerminate: true)
        }

        return .terminateLater
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }
}

// macOS 13 equivalent of the two-value onChange API introduced in macOS 14.
extension View {
    func maaOnChange<Value: Equatable>(of value: Value, initial: Bool = false,
        _ action: @escaping (Value, Value) -> Void) -> some View {
        modifier(MAAChangeObserver(value: value, initial: initial, action: action))
    }
}

private struct MAAChangeObserver<Value: Equatable>: ViewModifier {
    let value: Value
    let initial: Bool
    let action: (Value, Value) -> Void
    @State private var previous: Value
    @State private var appeared = false

    init(value: Value, initial: Bool, action: @escaping (Value, Value) -> Void) {
        self.value = value
        self.initial = initial
        self.action = action
        _previous = State(initialValue: value)
    }

    func body(content: Content) -> some View {
        content.onAppear {
            if !appeared {
                appeared = true
                previous = value
                if initial { action(value, value) }
            }
        }.onChange(of: value) { newValue in
            let oldValue = previous
            previous = newValue
            action(oldValue, newValue)
        }
    }
}
