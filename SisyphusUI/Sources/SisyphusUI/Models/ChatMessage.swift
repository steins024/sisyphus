import Foundation

struct ChatMessage: Identifiable {
    let id = UUID()
    var role: Role
    var content: String
    let timestamp = Date()

    enum Role {
        case user, assistant, system
    }
}

struct TaskInfo {
    let id: String
    let description: String
    let worker: String
    var status: TaskStatus

    enum TaskStatus {
        case running, done, failed
    }
}
