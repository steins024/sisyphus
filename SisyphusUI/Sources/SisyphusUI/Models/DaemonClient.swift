import Foundation

enum DaemonEvent {
    case chunk(String)
    case taskCreated(taskId: String, description: String, worker: String)
    case taskDone(result: String?)
    case taskFailed(error: String?)
    case taskOverride
    case done(sessionId: String?)
    case error(String)
}

class DaemonClient {
    private let baseURL: URL

    init(port: Int = SisyphusConstants.daemonPort) {
        self.baseURL = URL(string: "http://localhost:\(port)")!
    }

    func chat(message: String, sessionId: String?, mode: String?, onEvent: @escaping (DaemonEvent) -> Void) {
        var body: [String: Any] = ["message": message]
        if let sid = sessionId { body["sessionId"] = sid }
        if let m = mode { body["mode"] = m }

        guard let url = URL(string: "/api/chat", relativeTo: baseURL) else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        let session = URLSession(configuration: .default, delegate: SSEDelegate(onEvent: onEvent), delegateQueue: nil)
        let task = session.dataTask(with: request)
        task.resume()
    }
}

private class SSEDelegate: NSObject, URLSessionDataDelegate {
    let onEvent: (DaemonEvent) -> Void
    private var buffer = ""

    init(onEvent: @escaping (DaemonEvent) -> Void) {
        self.onEvent = onEvent
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        guard let text = String(data: data, encoding: .utf8) else { return }
        buffer += text

        while let range = buffer.range(of: "\n\n") {
            let chunk = String(buffer[buffer.startIndex..<range.lowerBound])
            buffer = String(buffer[range.upperBound...])

            for line in chunk.split(separator: "\n") {
                let lineStr = String(line)
                guard lineStr.hasPrefix("data: ") else { continue }
                let jsonStr = String(lineStr.dropFirst(6))

                guard let jsonData = jsonStr.data(using: .utf8),
                      let json = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any],
                      let type = json["type"] as? String else { continue }

                switch type {
                case "chunk":
                    if let content = json["content"] as? String {
                        onEvent(.chunk(content))
                    }
                case "task_created":
                    onEvent(.taskCreated(
                        taskId: json["taskId"] as? String ?? "",
                        description: json["description"] as? String ?? "",
                        worker: json["worker"] as? String ?? ""
                    ))
                case "task_done":
                    onEvent(.taskDone(result: json["result"] as? String))
                case "task_failed":
                    onEvent(.taskFailed(error: json["error"] as? String))
                case "task_override":
                    onEvent(.taskOverride)
                case "done":
                    onEvent(.done(sessionId: json["sessionId"] as? String))
                case "error":
                    onEvent(.error(json["content"] as? String ?? "Unknown error"))
                default:
                    break
                }
            }
        }
    }
}
