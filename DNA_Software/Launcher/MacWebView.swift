import AppKit
import WebKit

final class Workspace: NSObject, NSApplicationDelegate, NSWindowDelegate, WKNavigationDelegate, WKUIDelegate, WKDownloadDelegate {
    private let url: URL
    private var window: NSWindow?

    init(url: URL) {
        self.url = url
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        let quitMenu = NSMenu()
        let appItem = NSMenuItem()
        appItem.submenu = NSMenu()
        appItem.submenu?.addItem(withTitle: "Quit DNA Workbench", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        quitMenu.addItem(appItem)
        NSApp.mainMenu = quitMenu

        let view = WKWebView(frame: .zero)
        view.navigationDelegate = self
        view.uiDelegate = self
        view.load(URLRequest(url: url))
        let frame = NSRect(x: 0, y: 0, width: 1280, height: 800)
        let window = NSWindow(contentRect: frame, styleMask: [.titled, .closable, .resizable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "DNA Workbench"
        window.delegate = self
        window.contentView = view
        window.center()
        window.makeKeyAndOrderFront(nil)
        self.window = window
        NSApp.activate(ignoringOtherApps: true)
    }

    func windowWillClose(_ notification: Notification) {
        NSApp.terminate(nil)
    }

    private func isWorkspace(_ candidate: URL) -> Bool {
        candidate.scheme == "http" && candidate.host == "127.0.0.1" && candidate.port == url.port
            && candidate.user == nil && candidate.password == nil
    }

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let target = action.request.url else {
            decisionHandler(.cancel)
            return
        }
        let localBlob = url.port.map { target.absoluteString.hasPrefix("blob:http://127.0.0.1:\($0)/") } ?? false
        if isWorkspace(target) || (localBlob && action.shouldPerformDownload) {
            decisionHandler(action.shouldPerformDownload ? .download : .allow)
        } else {
            if action.navigationType == .linkActivated && target.scheme == "https" {
                NSWorkspace.shared.open(target)
            }
            decisionHandler(.cancel)
        }
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationResponse: WKNavigationResponse,
                 decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        guard let target = navigationResponse.response.url, isWorkspace(target) else {
            decisionHandler(.cancel)
            return
        }
        let response = navigationResponse.response as? HTTPURLResponse
        let disposition = response?.value(forHTTPHeaderField: "Content-Disposition")?.lowercased()
        let download = disposition?.hasPrefix("attachment") == true || !navigationResponse.canShowMIMEType
        decisionHandler(download ? .download : .allow)
    }

    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        guard let window = window, let origin = frame.request.url, isWorkspace(origin) else {
            completionHandler(nil)
            return
        }
        let panel = NSOpenPanel()
        panel.canChooseDirectories = parameters.allowsDirectories
        panel.canChooseFiles = !parameters.allowsDirectories
        panel.allowsMultipleSelection = parameters.allowsMultipleSelection
        panel.beginSheetModal(for: window) { response in
            completionHandler(response == .OK ? panel.urls : nil)
        }
    }

    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) {
        download.delegate = self
    }

    func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) {
        download.delegate = self
    }

    func download(_ download: WKDownload, decideDestinationUsing response: URLResponse,
                  suggestedFilename: String, completionHandler: @escaping (URL?) -> Void) {
        guard let window = window else {
            completionHandler(nil)
            return
        }
        let panel = NSSavePanel()
        panel.canCreateDirectories = true
        panel.nameFieldStringValue = URL(fileURLWithPath: suggestedFilename).lastPathComponent
        panel.beginSheetModal(for: window) { result in
            guard result == .OK, let destination = panel.url,
                  !FileManager.default.fileExists(atPath: destination.path) else {
                completionHandler(nil)
                return
            }
            completionHandler(destination)
        }
    }

    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                 for action: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let target = action.request.url, action.navigationType == .linkActivated {
            if isWorkspace(target) {
                webView.load(action.request)
            } else if target.scheme == "https" {
                NSWorkspace.shared.open(target)
            }
        }
        return nil
    }
}

guard CommandLine.arguments.count == 2,
      let url = URL(string: CommandLine.arguments[1]), url.scheme == "http",
      url.host == "127.0.0.1", url.port != nil, url.path == "/app",
      url.user == nil, url.password == nil, url.query == nil, url.fragment == nil else {
    fputs("Expected a local DNA Workbench URL.\n", stderr)
    exit(2)
}

let app = NSApplication.shared
let workspace = Workspace(url: url)
app.setActivationPolicy(.regular)
app.delegate = workspace
app.run()
