# Auto-Doc Janitor 🧹

Autonomous background agent that keeps your project's `STRUCTURE.md` and `ARCHITECTURE.md` perfectly synced with your code in real-time.

## Features
- **Real-time Synchronization**: Watches your filesystem and updates documentation as you save.
- **Semantic Change Detection**: Classifies changes as Cosmetic, Minor, or Major to route to the appropriate LLM.
- **Dual-Model Strategy**: Uses fast models (Claude Haiku) for small updates and smart models (Claude Sonnet) for architectural shifts.
- **ADR Generation**: Automatically writes Architecture Decision Records for major changes.

## Setup
1. `cd extension && npm install`
2. `pip install -r requirements.txt`
3. Open in VS Code/Cursor and run the extension.
