import time
import os
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from parser import parse_change
from detector import classify_change
from clod_router import route_request
from llm_summarizer import summarize_impact
from doc_patcher import patch_docs
from ipc import send_status

import threading

def safe_print(msg):
    """Safely prints message to console handling Unicode on Windows."""
    try:
        print(str(msg).encode('ascii', errors='replace').decode('ascii'))
    except:
        print("Log error (Unicode)")

class JanitorHandler(PatternMatchingEventHandler):
    def __init__(self):
        super().__init__(ignore_patterns=[
            "*/__pycache__/*", 
            "*/.git/*", 
            "*/node_modules/*", 
            "*.md",
            "*.git*"
        ])
        self.debounce_timer = None

    def on_modified(self, event):
        self._handle_event(event)

    def on_created(self, event):
        self._handle_event(event)

    def _handle_event(self, event):
        if event.is_directory:
            return
        
        # Debounce logic: cancel previous timer and start a new one
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        self.debounce_timer = threading.Timer(1.0, self.process_change, [event.src_path])
        self.debounce_timer.start()
        safe_print(f"Detected event in {os.path.basename(event.src_path)}, waiting for save to settle...")

    def process_change(self, file_path):
        send_status({
            "event": "updating", 
            "tier": "Analyzing", 
            "model": "...", 
            "summary": f"Analyzing {os.path.basename(file_path)}...",
            "reasoning": f"Filesystem event detected for {file_path}. Initiating AST parsing and diff analysis."
        })
        
        # Pipeline execution
        change_set = parse_change(file_path)
        tier_info = classify_change(change_set)
        
        safe_print(f"\n--- Analysis Results for {os.path.basename(file_path)} ---")
        safe_print(f"Tier: {tier_info['tier'].upper()} ({tier_info['reason']})")
        safe_print(f"Raw Diff Length: {len(change_set['raw_diff'])} characters")
        
        if tier_info['tier'] == 'cosmetic':
            safe_print("Action: Skipping cosmetic change.\n")
            send_status({
                "event": "idle", 
                "tier": "Cosmetic", 
                "model": "N/A", 
                "summary": "Skipped cosmetic change.",
                "reasoning": "Change classified as cosmetic (whitespace or comments). No documentation update required."
            })
            return

        model = route_request(tier_info['tier'])
        safe_print(f"Routing to Model: {model}")
        
        summary_info = summarize_impact(change_set, tier_info, model)
        safe_print(f"LLM Summary: {summary_info['summary']}")
        safe_print(f"\n--- AI Response ---")
        patch_preview = summary_info['patch'][:500] if summary_info['patch'] else "No patch"
        safe_print(patch_preview)
        safe_print("-------------------------------------------\n")
        
        patch_docs(file_path, summary_info)
        
        send_status({
            "event": "updated",
            "tier": tier_info['tier'],
            "model": model,
            "summary": summary_info['summary'],
            "diff": change_set['raw_diff'],
            "reasoning": f"Change classified as {tier_info['tier']}. Routed to {model}. Documentation patched successfully."
        })

def start_watcher():
    # Allow watching an external directory via environment variable
    path = os.getenv("WATCH_PATH", ".")
    safe_print(f"Janitor is now watching: {os.path.abspath(path)}")
    event_handler = JanitorHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        # Cancel any pending debounce timer before stopping
        if event_handler.debounce_timer:
            event_handler.debounce_timer.cancel()
        safe_print("Agent stopping...")
        observer.stop()
        observer.join()
