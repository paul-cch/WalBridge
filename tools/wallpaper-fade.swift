#!/usr/bin/env swift
//
// wallpaper-fade.swift
// Sets macOS wallpaper with animated transitions (like swww on Linux).
//
// Usage:  wallpaper-fade <image-path> [--duration <seconds>] [--transition <name>]
// Build:  swiftc -O wallpaper-fade.swift -o wallpaper-fade
//

import AppKit
import QuartzCore
import ScreenCaptureKit

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

    static var random: Transition {
        allCases.randomElement()!
    }
}

// MARK: - Arguments

let args = CommandLine.arguments
guard args.count >= 2 else {
    let names = Transition.allCases.map(\.rawValue).joined(separator: ", ")
    fputs("""
    Usage: wallpaper-fade <image-path> [--duration <seconds>] [--transition <name>]
           wallpaper-fade --from <old-image> [--duration <seconds>] [--transition <name>]

    First form: set wallpaper to <image-path> with animated transition.
    Second form: overlay <old-image> and fade out to reveal the current wallpaper
                 (for use after wallpaper already changed, e.g. from a sync script).

    Transitions: \(names), random (default)

    """, stderr)
    exit(1)
}

let duration: TimeInterval = {
    if let i = args.firstIndex(of: "--duration"), i + 1 < args.count {
        return TimeInterval(args[i + 1]) ?? 0.5
    }
    return 0.5
}()

let chosenTransition: Transition = {
    if let i = args.firstIndex(of: "--transition"), i + 1 < args.count {
        let name = args[i + 1]
        if name == "random" { return .random }
        if let t = Transition(rawValue: name) { return t }
        fputs("Unknown transition: \(name)\n", stderr)
        exit(1)
    }
    return .random
}()

// --from mode: overlay old image, fade out (wallpaper already changed)
// Normal mode: set wallpaper to <image-path>, then fade
let fromPath: String? = {
    if let i = args.firstIndex(of: "--from"), i + 1 < args.count {
        return (args[i + 1] as NSString).expandingTildeInPath
    }
    return nil
}()

let imagePath: String = fromPath ?? (args[1] as NSString).expandingTildeInPath
let setWallpaper = fromPath == nil
let newURL = URL(fileURLWithPath: imagePath)

guard FileManager.default.fileExists(atPath: imagePath) else {
    fputs("Error: file not found: \(imagePath)\n", stderr)
    exit(1)
}

// MARK: - Capture current wallpaper via ScreenCaptureKit

@Sendable func captureDesktop(displayID: CGDirectDisplayID) async -> NSImage? {
    do {
        let content = try await SCShareableContent.excludingDesktopWindows(
            false, onScreenWindowsOnly: true
        )
        guard let display = content.displays.first(where: { $0.displayID == displayID }) else {
            return nil
        }
        let filter = SCContentFilter(
            display: display,
            excludingApplications: content.applications,
            exceptingWindows: []
        )
        let config = SCStreamConfiguration()
        config.width = display.width * 2
        config.height = display.height * 2
        config.showsCursor = false
        config.captureResolution = .best

        let cgImage = try await SCScreenshotManager.captureImage(
            contentFilter: filter, configuration: config
        )
        return NSImage(
            cgImage: cgImage,
            size: NSSize(width: display.width, height: display.height)
        )
    } catch {
        return nil
    }
}

// MARK: - Get current wallpaper image for a screen

func currentWallpaperImage(for screen: NSScreen) -> NSImage? {
    if let url = NSWorkspace.shared.desktopImageURL(for: screen) {
        var isDir: ObjCBool = false
        if FileManager.default.fileExists(atPath: url.path, isDirectory: &isDir), !isDir.boolValue {
            if let image = NSImage(contentsOf: url) {
                return image
            }
        }
    }
    return nil
}

// MARK: - Create overlay window at desktop level

func makeOverlay(image: NSImage, on screen: NSScreen) -> NSWindow {
    let window = NSWindow(
        contentRect: screen.frame,
        styleMask: .borderless,
        backing: .buffered,
        defer: false
    )
    window.level = NSWindow.Level(
        rawValue: Int(CGWindowLevelForKey(.desktopWindow)) + 1
    )
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

// MARK: - Animate transition

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

/// Window-frame and alpha based animations
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
                var target = frame
                target.origin.x -= frame.width
                window.animator().setFrame(target, display: false)
                window.animator().alphaValue = 0.2

            case .slideRight:
                var target = frame
                target.origin.x += frame.width
                window.animator().setFrame(target, display: false)
                window.animator().alphaValue = 0.2

            case .slideUp:
                var target = frame
                target.origin.y += frame.height
                window.animator().setFrame(target, display: false)
                window.animator().alphaValue = 0.2

            case .slideDown:
                var target = frame
                target.origin.y -= frame.height
                window.animator().setFrame(target, display: false)
                window.animator().alphaValue = 0.2

            case .grow:
                let target = frame.insetBy(dx: -frame.width * 0.15, dy: -frame.height * 0.15)
                window.animator().setFrame(target, display: false)
                window.animator().alphaValue = 0

            default:
                break
            }
        }
    }, completionHandler: completion)
}

/// Layer-mask based wipe animations using explicit CABasicAnimation
func animateWipe(
    _ transition: Transition,
    windows: [NSWindow],
    duration: TimeInterval,
    completion: @escaping () -> Void
) {
    for window in windows {
        guard let layer = window.contentView?.layer else { continue }
        let bounds = layer.bounds

        // Create mask covering the full content — old wallpaper is fully visible
        let mask = CALayer()
        mask.backgroundColor = CGColor.white
        mask.frame = bounds
        layer.mask = mask

        // Flush so CA commits the initial mask state before we animate
        CATransaction.flush()

        // Calculate where the mask slides to (off-screen = old wallpaper hidden)
        var endPosition = mask.position
        switch transition {
        case .wipeLeft:
            endPosition.x -= bounds.width
        case .wipeRight:
            endPosition.x += bounds.width
        case .wipeUp:
            endPosition.y += bounds.height
        case .wipeDown:
            endPosition.y -= bounds.height
        default:
            break
        }

        // Explicit animation so CA knows from → to
        let anim = CABasicAnimation(keyPath: "position")
        anim.fromValue = NSValue(point: mask.position)
        anim.toValue = NSValue(point: endPosition)
        anim.duration = duration
        anim.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
        anim.fillMode = .forwards
        anim.isRemovedOnCompletion = false
        mask.add(anim, forKey: "wipe")
    }

    // Completion after animation finishes
    DispatchQueue.main.asyncAfter(deadline: .now() + duration + 0.05) {
        completion()
    }
}

// MARK: - Main

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

// Step 1: determine overlay image
// --from mode: load the provided image (the OLD wallpaper)
// Normal mode: read current wallpaper from system, then set the new one
var overlayImage: NSImage?

if fromPath != nil {
    // --from: use the provided old wallpaper image directly
    overlayImage = NSImage(contentsOf: newURL)
} else {
    // Normal: grab current wallpaper before we replace it
    if let screen = NSScreen.screens.first {
        overlayImage = currentWallpaperImage(for: screen)
    }
    if overlayImage == nil {
        // Fallback to ScreenCaptureKit
        let ready = DispatchSemaphore(value: 0)
        let displayID = (NSScreen.main?.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")]
            as? CGDirectDisplayID) ?? CGMainDisplayID()
        Task {
            overlayImage = await captureDesktop(displayID: displayID)
            ready.signal()
        }
        ready.wait()
    }
}

guard let image = overlayImage else {
    fputs("Error: could not load overlay image\n", stderr)
    exit(1)
}

// Step 2: create overlays on all screens
var overlays: [NSWindow] = []
for screen in NSScreen.screens {
    overlays.append(makeOverlay(image: image, on: screen))
}

// Step 3: set the new wallpaper behind the overlay (skip in --from mode)
if setWallpaper {
    for screen in NSScreen.screens {
        try? NSWorkspace.shared.setDesktopImageURL(newURL, for: screen, options: [:])
    }
    let desktoppr = "/usr/local/bin/desktoppr"
    if FileManager.default.fileExists(atPath: desktoppr) {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: desktoppr)
        task.arguments = [imagePath]
        try? task.run()
        task.waitUntilExit()
    }
}

// Step 4: animate the transition
DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
    animateTransition(chosenTransition, windows: overlays, duration: duration) {
        overlays.forEach { $0.close() }
    }
}

// Timed run loop — guarantees exit even if animation callback doesn't fire
// (e.g. when spawned from a launchd agent)
RunLoop.main.run(until: Date(timeIntervalSinceNow: duration + 0.5))
