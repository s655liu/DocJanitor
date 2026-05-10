# GEMINI.md — Google Antigravity & Sponsor Integration
## (Cursor / VS Code Plugin)

## 🚀 Overview

**Auto-Doc Janitor** is an autonomous background agent designed for the Google Antigravity ecosystem, now packaged as a plugin for **Cursor** and **VS Code**. It solves the "Documentation Debt" problem by using a multi-model reasoning loop to keep `STRUCTURE.md` and `ARCHITECTURE.md` perfectly synced with your code in real-time — directly inside your editor.

## 🤖 Google Antigravity & Gemini Integration

### 1. Agentic Plugin View
The Janitor runs as a background process within your **Cursor/VS Code** editor, providing live documentation updates.

Users can observe the agent's internal reasoning — from filesystem observation to semantic classification — via a dedicated sidebar panel or output channel.

### 2. Dual-Model Strategy (Gemini 3.1)
- **Gemini 3.1 Flash**: Used for Minor Tiers (function renames, small diffs) to provide sub-second documentation patches with high efficiency.
- **Gemini 3.1 Pro**: Triggered for Major Tiers (architectural shifts, new modules) where deep reasoning is required to generate ADRs (Architecture Decision Records).

### 3. Secure Execution
The Python agent runs in a secure subprocess with filesystem scoping, ensuring that `git-diff` parsing and `tree-sitter` AST analysis are performed safely within your workspace.

## 💎 Sponsor Integrations

### 🟢 CLōD — Model Routing ($500)
- **Dynamic Routing**: Our `clod_router.py` acts as the brain of the project, programmatically selecting models based on the "Change Set" complexity.
- **Visible Model Switching**: The plugin highlights real-time switching between Claude and Gemini models through the CLōD API, with the specific model used surfacing in the editor status bar.

### 🔵 Nia by Nozomio — Context Infrastructure
- **Beyond the Code**: Before generating a patch, the agent queries Nia to fetch external context like Slack threads, PDF specs, or existing ADRs.
- **Semantic Grounding**: This ensures the Janitor understands *why* a change was made (e.g., a security requirement discussed in a document) rather than just *what* code changed.

### 🟠 AllScale — Agent Monetization ($300)
- **Feature Gating**: We demonstrate the AllScale Checkout flow by gating "Full-Repo Architecture Regeneration" behind a simulated micropayment inside the editor.
- **Workflow Integration**: This showcases how AI agents can handle their own commercial transactions within a developer workflow.

### ⚪ Greptile
- **Self-Audit**: Post-hackathon, we use Greptile to scan the Janitor’s internal IPC logic and socket handling to identify and fix non-trivial bugs before the final pitch.

## 🛠️ How to Run in Cursor / VS Code

1. Install the plugin from the **VS Code Marketplace** or **Cursor Extension Gallery**.
2. Open any project folder.
3. The plugin activates automatically — watch the status bar for the Janitor icon.
4. As you edit files, the Janitor begins updating `STRUCTURE.md` and `ARCHITECTURE.md` in real time for every non-cosmetic save.