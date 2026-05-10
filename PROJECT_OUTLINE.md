# Auto-Doc Janitor — Project Outline

> A Cursor/VSCode extension + background agent that watches your codebase and automatically maintains `STRUCTURE.md` and `ARCHITECTURE.md` as you code.

---

## Hackathon targets

| Sponsor | How it's hit |
|---|---|
| CLōD ($500) | Model router: small diff → fast model, big refactor → smart model. Visible in sidebar. |
| Nia | Agent fetches existing doc context from Nia before every LLM call. |
| Cursor | Native IDE extension — developer tooling at its core. |
| AllScale ($300) | Stretch: gate "Pro" full-doc regeneration behind a micropayment on major refactors. |

---

## Pipeline

```
Filesystem watcher
    ↓
Git diff + AST parser
    ↓
Semantic change detector          ← classify: cosmetic / minor / major
    ↓
Nia context fetch                 ← pull existing docs before rewriting  [Nia]
    ↓
CLōD model router                 ← minor → fast model, major → smart model  [CLōD]
    ↓
LLM impact summarizer             ← what changed and why it matters
    ↓
Doc patcher                       ← surgical edit to STRUCTURE.md / ARCHITECTURE.md
    ↓
ADR writer (optional)             ← only fires on major architectural decisions
    ↓
Extension sidebar update          ← show model used, diff preview, last update time
```

---

## Project structure

```
autodoc-janitor/
│
├── extension/                        ← VSCode/Cursor extension (TypeScript)
│   ├── src/
│   │   ├── extension.ts              ← entry point; activates on workspace open
│   │   ├── sidebar.ts                ← TreeView panel: last update, model used, diff preview
│   │   ├── statusBar.ts              ← bottom bar indicator ("Janitor watching..." / "Updated STRUCTURE.md")
│   │   └── agentBridge.ts            ← spawns agent process; IPC over stdin/stdout or local socket
│   ├── package.json                  ← contributes: commands, views, activationEvents, config schema
│   └── tsconfig.json
│
├── agent/                            ← background agent (Python)
│   ├── main.py                       ← entry point; starts watcher loop; handles IPC with extension
│   ├── watcher.py                    ← watchdog filesystem event handler (on_modified, on_created)
│   ├── parser.py                     ← git diff + tree-sitter AST diff; extracts changed symbols
│   ├── detector.py                   ← semantic change classifier → cosmetic / minor / major
│   ├── nia_client.py                 ← fetches existing doc context from Nia before LLM call
│   ├── clod_router.py                ← picks model based on change tier; logs model name for demo
│   ├── llm_summarizer.py             ← builds prompt with diff + Nia context; calls CLōD API
│   ├── doc_patcher.py                ← finds relevant heading in STRUCTURE.md; replaces only that block
│   ├── adr_writer.py                 ← creates /docs/adr/NNNN-slug.md on major decisions
│   └── ipc.py                        ← sends status payloads back to extension (JSON over socket)
│
├── docs/
│   ├── STRUCTURE.md                  ← auto-maintained; shows module map, exports, dependencies
│   ├── ARCHITECTURE.md               ← auto-maintained; shows system-level design decisions
│   └── adr/
│       └── 0001-initial-setup.md     ← seed ADR; subsequent ones created by adr_writer.py
│
├── .janitor.config.json              ← user config: watch paths, ignore globs, change thresholds, model prefs
├── requirements.txt                  ← watchdog, tree-sitter, requests, python-dotenv
└── README.md
```

---

## File responsibilities

### Extension layer (TypeScript)

**`extension.ts`**
- Registers activation event (`onStartupFinished`)
- Reads `.janitor.config.json` from workspace root
- Calls `agentBridge.start()` to spawn the Python agent
- Registers commands: `janitor.pause`, `janitor.forceUpdate`, `janitor.openDiff`

**`agentBridge.ts`**
- Spawns `agent/main.py` as a child process via `child_process.spawn`
- Listens on stdout for JSON status payloads: `{ event, file, model, summary, patch }`
- Emits VS Code events that sidebar and status bar subscribe to
- Handles agent crashes with automatic restart + exponential backoff

**`sidebar.ts`**
- Implements `TreeDataProvider` for the Janitor panel
- Shows: last updated file, model used (fast/smart), timestamp, one-line summary
- "View diff" button opens a diff editor against the previous STRUCTURE.md version
- Updates live as `agentBridge` emits events

**`statusBar.ts`**
- Shows `$(eye) Janitor: watching` when idle
- Pulses `$(sync~spin) Janitor: updating STRUCTURE.md` during a run
- Shows `$(check) Janitor: updated 2s ago` after completion

---

### Agent layer (Python)

**`watcher.py`**
- Uses `watchdog` library with `PatternMatchingEventHandler`
- Ignores: `__pycache__`, `.git`, `node_modules`, `*.pyc`, files in `.janitorignore`
- Debounces rapid saves (500ms window) to avoid duplicate triggers
- Passes changed file path + event type to `parser.py`

**`parser.py`**
- Runs `git diff HEAD -- <file>` to get the raw diff
- Feeds the changed file through `tree-sitter` to extract added/removed/modified symbols (functions, classes, exports)
- Returns a structured `ChangeSet`: `{ file, added_symbols, removed_symbols, modified_symbols, raw_diff }`

**`detector.py`**
- Classifies a `ChangeSet` into one of three tiers:
  - `cosmetic` — formatting, comments, variable rename inside a function → skip
  - `minor` — new function, new parameter, new export → fast model
  - `major` — new module, interface change, cross-file dependency shift, deleted export → smart model
- Returns `{ tier, reason }` — `reason` is included in the LLM prompt

**`nia_client.py`**
- On every non-cosmetic change, fetches the current relevant section of `STRUCTURE.md` from Nia
- Also fetches any linked spec docs or ADRs that mention the changed file/symbol
- Returns context string injected into the LLM prompt so it knows what already exists

**`clod_router.py`**
- `minor` tier → `claude-haiku` (fast, cheap, low latency)
- `major` tier → `claude-sonnet` (smart, thorough)
- Logs `{ model, tier, file }` — this is what surfaces in the extension sidebar for the demo

**`llm_summarizer.py`**
- Builds a structured prompt:
  ```
  Existing doc section (from Nia): ...
  Changed file: auth/middleware.py
  Change tier: minor
  New symbols: validate_jwt_expiry()
  Raw diff: ...

  Update the doc section to reflect this change. Be surgical — preserve existing content.
  ```
- Calls CLōD API; streams response back
- Returns `{ updated_section, one_line_summary }`

**`doc_patcher.py`**
- Reads `STRUCTURE.md`
- Finds the heading that corresponds to the changed file/module (e.g. `## auth/middleware`)
- Replaces only that block with the LLM output — everything else untouched
- Writes back atomically (write to `.tmp`, then rename)
- Keeps a git-tracked history so diffs are always reviewable

**`adr_writer.py`**
- Only fires when `detector.py` returns `major`
- Prompts the LLM for an ADR: context, decision, consequences
- Creates `/docs/adr/NNNN-<slug>.md` with auto-incremented number
- Appends a link to the new ADR at the bottom of `ARCHITECTURE.md`

---

## Configuration (`.janitor.config.json`)

```json
{
  "watch": ["src/**", "lib/**"],
  "ignore": ["**/*.test.*", "**/migrations/**"],
  "debounce_ms": 500,
  "change_thresholds": {
    "minor_min_symbols": 1,
    "major_min_symbols": 3
  },
  "models": {
    "minor": "claude-haiku-4-5-20251001",
    "major": "claude-sonnet-4-6"
  },
  "nia": {
    "enabled": true,
    "workspace_id": "YOUR_NIA_WORKSPACE_ID"
  },
  "allscale": {
    "enabled": false,
    "trigger_on": "major",
    "product_id": "pro-doc-regen"
  },
  "adr": {
    "enabled": true,
    "path": "docs/adr"
  }
}
```

---

## Build order (hackathon sequence)

### Phase 1 — Core agent (2–3 hrs)
1. `watcher.py` + `parser.py` — get file events and diffs working
2. `detector.py` — hardcode the three-tier classifier
3. `llm_summarizer.py` + `doc_patcher.py` — call CLōD, patch the markdown

### Phase 2 — Sponsor integrations (1–2 hrs)
4. `clod_router.py` — wire up model switching; verify it logs visibly
5. `nia_client.py` — fetch existing doc context before each LLM call

### Phase 3 — Extension UI (1–2 hrs)
6. `agentBridge.ts` + `extension.ts` — spawn agent, receive IPC events
7. `sidebar.ts` + `statusBar.ts` — show model, summary, timestamp in panel

### Phase 4 — Polish + extras (1 hr)
8. `adr_writer.py` — ADR generation on major changes
9. `.janitor.config.json` — expose config in VS Code settings UI
10. Demo script — prepare a repo with a staged refactor that triggers each tier

---

## Demo script (for judges)

1. Open the test repo in Cursor — Janitor activates, status bar shows "watching"
2. Add a new function to `auth/middleware.py` → sidebar shows **fast model**, one-line summary, STRUCTURE.md diff
3. Delete a module and add a replacement → sidebar shows **smart model**, ARCHITECTURE.md updated, ADR created
4. Click "View diff" → split editor showing exactly what the Janitor changed
5. Show `.janitor.config.json` → explain model routing thresholds
