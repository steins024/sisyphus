import SwiftUI

struct SpotlightView: View {
    @StateObject private var viewModel = SpotlightViewModel()
    @FocusState private var isInputFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            if viewModel.isExpanded {
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            ForEach(viewModel.messages) { msg in
                                ChatBubbleView(message: msg)
                            }
                        }
                        .padding()
                    }
                    .frame(maxHeight: 400)
                    .onChange(of: viewModel.messages.count) { _ in
                        if let last = viewModel.messages.last {
                            withAnimation {
                                proxy.scrollTo(last.id, anchor: .bottom)
                            }
                        }
                    }
                }
            }

            // Input field
            HStack(spacing: 12) {
                Image(systemName: "sparkle")
                    .font(.system(size: 20))
                    .foregroundColor(.secondary)

                TextField("Ask Sisyphus...", text: $viewModel.inputText)
                    .textFieldStyle(.plain)
                    .font(.system(size: 20, weight: .light))
                    .focused($isInputFocused)
                    .onSubmit {
                        viewModel.send(mode: .fireAndForget)
                    }

                if viewModel.isLoading {
                    ProgressView()
                        .scaleEffect(0.7)
                }
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 14)
        }
        .background(
            VisualEffectBackground(material: .hudWindow, blendingMode: .behindWindow)
        )
        .clipShape(RoundedRectangle(cornerRadius: SisyphusConstants.cornerRadius))
        .shadow(color: .black.opacity(0.3), radius: 20, y: 10)
        .frame(width: SisyphusConstants.panelWidth)
        .onAppear { isInputFocused = true }
        .onExitCommand { viewModel.dismiss() }
    }
}

// NSVisualEffectView wrapper
struct VisualEffectBackground: NSViewRepresentable {
    let material: NSVisualEffectView.Material
    let blendingMode: NSVisualEffectView.BlendingMode

    func makeNSView(context: Context) -> NSVisualEffectView {
        let view = NSVisualEffectView()
        view.material = material
        view.blendingMode = blendingMode
        view.state = .active
        return view
    }

    func updateNSView(_ nsView: NSVisualEffectView, context: Context) {
        nsView.material = material
        nsView.blendingMode = blendingMode
    }
}
