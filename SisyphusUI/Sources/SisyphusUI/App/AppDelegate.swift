import Cocoa
import SwiftUI

class AppDelegate: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem!
    private var panel: SpotlightPanel!
    private var hotKeyManager: HotKeyManager!

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Hide from dock
        NSApplication.shared.setActivationPolicy(.accessory)

        // Create the panel
        panel = SpotlightPanel()
        let hostingView = NSHostingView(rootView: SpotlightView())
        hostingView.translatesAutoresizingMaskIntoConstraints = false
        panel.contentView = hostingView

        // Menu bar icon
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        if let button = statusItem.button {
            button.image = NSImage(systemSymbolName: "brain.head.profile", accessibilityDescription: "Sisyphus")
        }

        let menu = NSMenu()
        menu.addItem(NSMenuItem(title: "Show Sisyphus (⌥Space)", action: #selector(togglePanel), keyEquivalent: ""))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(NSMenuItem(title: "Quit", action: #selector(quitApp), keyEquivalent: "q"))
        statusItem.menu = menu

        // Register hotkey
        hotKeyManager = HotKeyManager { [weak self] in
            self?.togglePanel()
        }
        hotKeyManager.register()

        // Listen for dismiss notification
        NotificationCenter.default.addObserver(self, selector: #selector(hidePanel), name: .dismissSpotlight, object: nil)

        // Listen for resize notification
        NotificationCenter.default.addObserver(forName: .resizePanel, object: nil, queue: .main) { [weak self] notification in
            if let height = notification.userInfo?["height"] as? CGFloat {
                self?.panel.updateHeight(height)
            }
        }
    }

    @objc func togglePanel() {
        if panel.isVisible {
            hidePanel()
        } else {
            showPanel()
        }
    }

    private func showPanel() {
        panel.makeKeyAndOrderFront(nil)
        NSApplication.shared.activate(ignoringOtherApps: true)
    }

    @objc private func hidePanel() {
        panel.orderOut(nil)
    }

    @objc private func quitApp() {
        NSApplication.shared.terminate(nil)
    }
}
