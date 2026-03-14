import Foundation
import SwiftUI

enum SendMode {
    case fireAndForget
    case chat
}

class SpotlightViewModel: ObservableObject {
    @Published var inputText = ""
    @Published var messages: [ChatMessage] = []
    @Published var isExpanded = false
    @Published var isLoading = false
    @Published var currentTask: TaskInfo?

    private var sessionId: String?
    private let client = DaemonClient()

    func send(mode: SendMode) {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }

        inputText = ""

        if text == "/new" {
            newSession()
            return
        }

        let userMsg = ChatMessage(role: .user, content: text)
        messages.append(userMsg)
        isExpanded = true
        isLoading = true

        let apiMode = mode == .fireAndForget ? "fire-forget" : nil

        // Add placeholder for assistant response
        let assistantMsg = ChatMessage(role: .assistant, content: "")
        messages.append(assistantMsg)
        let assistantIndex = messages.count - 1

        client.chat(message: text, sessionId: sessionId, mode: apiMode) { [weak self] event in
            DispatchQueue.main.async {
                guard let self = self else { return }
                switch event {
                case .chunk(let content):
                    self.messages[assistantIndex].content += content
                case .taskCreated(let taskId, let description, let worker):
                    self.currentTask = TaskInfo(id: taskId, description: description, worker: worker, status: .running)
                    self.messages[assistantIndex].content = "📋 Task assigned to \(worker)"
                case .taskDone(let result):
                    self.currentTask?.status = .done
                    self.messages[assistantIndex].content += "\n\n✅ Done:\n\(result ?? "")"
                    self.isLoading = false
                case .taskFailed(let error):
                    self.currentTask?.status = .failed
                    self.messages[assistantIndex].content += "\n\n❌ Failed: \(error ?? "Unknown error")"
                    self.isLoading = false
                case .taskOverride:
                    self.messages[assistantIndex].content = ""
                case .done(let sid):
                    self.sessionId = sid
                    self.isLoading = false
                case .error(let msg):
                    self.messages[assistantIndex].content = "❌ \(msg)"
                    self.isLoading = false
                }
            }
        }
    }

    func dismiss() {
        NotificationCenter.default.post(name: .dismissSpotlight, object: nil)
    }

    func newSession() {
        messages = []
        sessionId = nil
        isExpanded = false
        currentTask = nil
    }
}

extension Notification.Name {
    static let dismissSpotlight = Notification.Name("dismissSpotlight")
}
