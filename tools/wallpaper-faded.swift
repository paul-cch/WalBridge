#!/usr/bin/env swift
//
// wallpaper-faded.swift
// Persistent wallpaper transition daemon.
//
// Keeps an always-on overlay showing the current wallpaper. When the real
// wallpaper changes behind it, animates the overlay away — zero flash.
//
// Build: swiftc -O wallpaper-faded.swift -o wallpaper-faded
//

import AppKit
import QuartzCore

// MARK: - Transitions

enum Transition: String, CaseIterable {
    case fade
    case slideLeft = "slide-left"
    case slideRight = "slide-right"
    case slideUp = "slide-up"
    case slideDown = "slide-down"
    case grow
    case wipeLeft = "wipe-left"
    case wipeRight = "wipe-right"
    case wipeUp = "wipe-up"
    case wipeDown = "wipe-down"

    static var random: Transition { allCases.randomElement()! }
}

// MARK: - Overlay helpers

let desktopLevel = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.desktopWindow)) + 1)

func makeOverlay(image: NSImage, on screen: NSScreen) -> NSWindow {
    let window = NSWindow(
        contentRect: screen.frame,
        styleMask: .borderless,
        backing: .buffered,
        defer: false
    )
    window.level = desktopLevel
    window.isOpaque = false
    window.hasShadow = false
    window.ignoresMouseEvents = true
    window.collectionBehavior = [.canJoinAllSpaces, .stationary]
    window.backgroundColor = .clear

    let view = NSView(frame: NSRect(origin: .zero, size: screen.frame.size))
    view.wantsLayer = true
    view.layer?.contents = image
    view.layer?.contentsGravity = .resizeAspectFill
    view.autoresizingMask = []
    window.contentView = view
    window.orderFront(nil)
    return window
}

func updateOverlayImage(_ window: NSWindow, image: NSImage) {
    window.contentView?.layer?.contents = image
}

// MARK: - Animations

func animateTransition(
    _ transition: Transition,
    windows: [NSWindow],
    duration: TimeInterval,
    completion: @escaping () -> Void
) {
    switch transition {
    case .wipeLeft, .wipeRight, .wipeUp, .wipeDown:
        animateWipe(transition, windows: windows, duration: duration, completion: completion)
    default:
        animateWindowBased(transition, windows: windows, duration: duration, completion: completion)
    }
}

func animateWindowBased(
    _ transition: Transition,
    windows: [NSWindow],
    duration: TimeInterval,
    completion: @escaping () -> Void
) {
    NSAnimationContext.runAnimationGroup({ ctx in
        ctx.duration = duration
        ctx.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
        for window in windows {
            let frame = window.frame
            switch transition {
            case .fade:
                window.animator().alphaValue = 0
            case .slideLeft:
                var t = frame; t.origin.x -= frame.width
                window.animator().setFrame(t, display: false)
                window.animator().alphaValue = 0.2
            case .slideRight:
                var t = frame; t.origin.x += frame.width
                window.animator().setFrame(t, display: false)
                window.animator().alphaValue = 0.2
            case .slideUp:
                var t = frame; t.origin.y += frame.height
                window.animator().setFrame(t, display: false)
                window.animator().alphaValue = 0.2
            case .slideDown:
                var t = frame; t.origin.y -= frame.height
                window.animator().setFrame(t, display: false)
                window.animator().alphaValue = 0.2
            case .grow:
                let t = frame.insetBy(dx: -frame.width * 0.15, dy: -frame.height * 0.15)
                window.animator().setFrame(t, display: false)
                window.animator().alphaValue = 0
            default: break
            }
        }
    }, completionHandler: completion)
}

func animateWipe(
    _ transition: Transition,
    windows: [NSWindow],
    duration: TimeInterval,
    completion: @escaping () -> Void
) {
    for window in windows {
        guard let layer = window.contentView?.layer else { continue }
        let bounds = layer.bounds

        let mask = CALayer()
        mask.backgroundColor = CGColor.white
        mask.frame = bounds
        layer.mask = mask
        CATransaction.flush()

        var endPosition = mask.position
        switch transition {
        case .wipeLeft:  endPosition.x -= bounds.width
        case .wipeRight: endPosition.x += bounds.width
        case .wipeUp:    endPosition.y += bounds.height
        case .wipeDown:  endPosition.y -= bounds.height
        default: break
        }

        let anim = CABasicAnimation(keyPath: "position")
        anim.fromValue = NSValue(point: mask.position)
        anim.toValue = NSValue(point: endPosition)
        anim.duration = duration
        anim.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
        anim.fillMode = .forwards
        anim.isRemovedOnCompletion = false
        mask.add(anim, forKey: "wipe")
    }
    DispatchQueue.main.asyncAfter(deadline: .now() + duration + 0.05, execute: completion)
}

// MARK: - Daemon

class WallpaperDaemon {
    let duration: TimeInterval = 0.7
    let watchPath: String

    var cachedPath: String?
    var cachedImage: NSImage?

    // Persistent overlays — always showing current wallpaper on top
    var persistentOverlays: [NSWindow] = []

    var source: DispatchSourceFileSystemObject?
    var animating = false

    init() {
        watchPath = NSString(
            string: "~/Library/Application Support/com.apple.wallpaper/Store"
        ).expandingTildeInPath
    }

    func start() {
        // Load current wallpaper and create persistent overlays
        updateCache()
        createPersistentOverlays()
        startWatching()
        fputs("wallpaper-faded: running (persistent overlay active)\n", stderr)
    }

    // MARK: Cache

    func currentWallpaperPath() -> String? {
        guard let screen = NSScreen.main,
              let url = NSWorkspace.shared.desktopImageURL(for: screen) else { return nil }
        var isDir: ObjCBool = false
        if FileManager.default.fileExists(atPath: url.path, isDirectory: &isDir), !isDir.boolValue {
            return url.path
        }
        return nil
    }

    func updateCache() {
        guard let path = currentWallpaperPath() else { return }
        cachedPath = path
        cachedImage = NSImage(contentsOf: URL(fileURLWithPath: path))
    }

    // MARK: Persistent overlay

    func createPersistentOverlays() {
        guard let image = cachedImage else { return }
        for screen in NSScreen.screens {
            persistentOverlays.append(makeOverlay(image: image, on: screen))
        }
    }

    func refreshPersistentOverlays(with image: NSImage) {
        let screens = NSScreen.screens
        if persistentOverlays.isEmpty {
            for screen in screens {
                persistentOverlays.append(makeOverlay(image: image, on: screen))
            }
        } else {
            // Remove extra overlays if screens were disconnected
            while persistentOverlays.count > screens.count {
                persistentOverlays.removeLast().close()
            }
            // Reset each overlay to its matching screen
            for (i, overlay) in persistentOverlays.enumerated() {
                overlay.setFrame(screens[i].frame, display: false)
                overlay.alphaValue = 1.0
                overlay.contentView?.layer?.mask = nil
                updateOverlayImage(overlay, image: image)
                overlay.orderFront(nil)
            }
            // Add overlays for any newly connected screens
            for i in persistentOverlays.count..<screens.count {
                persistentOverlays.append(makeOverlay(image: image, on: screens[i]))
            }
        }
    }

    // MARK: File watching

    func startWatching() {
        let fd = open(watchPath, O_EVTONLY)
        guard fd >= 0 else {
            fputs("wallpaper-faded: cannot watch \(watchPath)\n", stderr)
            return
        }

        source = DispatchSource.makeFileSystemObjectSource(
            fileDescriptor: fd,
            eventMask: [.write, .rename, .attrib],
            queue: .main
        )
        source?.setEventHandler { [weak self] in
            self?.onFileChange()
        }
        source?.setCancelHandler { close(fd) }
        source?.resume()
    }

    // MARK: Change detection

    func onFileChange() {
        guard !animating else { return }

        // Small delay for desktoppr path to update
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { [self] in
            let newPath = currentWallpaperPath()
            guard let newPath, newPath != cachedPath else { return }

            fputs("wallpaper-faded: \(cachedPath?.components(separatedBy: "/").last ?? "?") → \(newPath.components(separatedBy: "/").last ?? "?")\n", stderr)

            // The persistent overlays are ALREADY showing the old wallpaper.
            // The new wallpaper is already set behind them.
            // Just animate the overlays away!
            animating = true
            let transition = Transition.random
            animateTransition(transition, windows: persistentOverlays, duration: duration) { [self] in
                // Load the new wallpaper and reset the persistent overlays
                cachedPath = newPath
                cachedImage = NSImage(contentsOf: URL(fileURLWithPath: newPath))
                if let image = cachedImage {
                    refreshPersistentOverlays(with: image)
                }
                animating = false
            }
        }
    }
}

// MARK: - Main

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

let daemon = WallpaperDaemon()
daemon.start()

app.run()
