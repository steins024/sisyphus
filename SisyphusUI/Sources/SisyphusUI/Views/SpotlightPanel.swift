import Cocoa

class SpotlightPanel: NSPanel {
    init() {
        super.init(
            contentRect: NSRect(x: 0, y: 0, width: SisyphusConstants.panelWidth, height: SisyphusConstants.panelCollapsedHeight),
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        self.level = .floating
        self.backgroundColor = .clear
        self.isOpaque = false
        self.hasShadow = true
        self.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        self.isMovableByWindowBackground = false

        // Center on screen, upper third
        if let screen = NSScreen.main {
            let x = (screen.frame.width - SisyphusConstants.panelWidth) / 2
            let y = screen.frame.height * 0.65
            self.setFrameOrigin(NSPoint(x: x, y: y))
        }
    }

    // NSPanel requires this
    override var canBecomeKey: Bool { true }

    func updateHeight(_ height: CGFloat) {
        var frame = self.frame
        let oldHeight = frame.height
        frame.size.height = height
        frame.origin.y -= (height - oldHeight) // grow upward
        self.setFrame(frame, display: true, animate: true)
    }
}
