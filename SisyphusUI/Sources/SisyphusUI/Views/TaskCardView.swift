import SwiftUI

struct TaskCardView: View {
    let task: TaskInfo

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Image(systemName: statusIcon)
                        .foregroundColor(statusColor)
                    Text(task.worker)
                        .font(.system(size: 12, weight: .semibold))
                    Spacer()
                    Text(task.id.prefix(8))
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(.secondary)
                }
                Text(task.description)
                    .font(.system(size: 12))
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
            .padding(12)
        }
        .background(RoundedRectangle(cornerRadius: 8).fill(Color.secondary.opacity(0.1)))
    }

    private var statusIcon: String {
        switch task.status {
        case .running: return "arrow.triangle.2.circlepath"
        case .done: return "checkmark.circle.fill"
        case .failed: return "xmark.circle.fill"
        }
    }

    private var statusColor: Color {
        switch task.status {
        case .running: return .blue
        case .done: return .green
        case .failed: return .red
        }
    }
}
