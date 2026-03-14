import SwiftUI

struct ChatBubbleView: View {
    let message: ChatMessage

    var body: some View {
        HStack {
            if message.role == .user { Spacer(minLength: 60) }

            Text(message.content)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .fill(message.role == .user ? Color.accentColor.opacity(0.8) : Color.secondary.opacity(0.2))
                )
                .foregroundColor(message.role == .user ? .white : .primary)
                .font(.system(size: 14))
                .textSelection(.enabled)

            if message.role == .assistant { Spacer(minLength: 60) }
        }
        .id(message.id)
    }
}
