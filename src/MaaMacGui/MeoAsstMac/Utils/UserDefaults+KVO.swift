//  UserDefaults+KVO.swift
//  Retired from the macOS 13 compatibility build.
//  CopilotContext (the only former @Defaults consumer) now owns a
//  Combine-published value, reads the existing preference on launch,
//  writes changes back, and observes UserDefaults.didChangeNotification.
//  This file remains in the Xcode project to avoid dangling file references.
