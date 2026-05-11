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
        self._handle_event(event, "modified")

    def on_created(self, event):
        self._handle_event(event, "created")

    def on_deleted(self, event):
        self._handle_event(event, "deleted")

    def _handle_event(self, event, event_type):
        if event.is_directory:
            return
        
        abs_path = os.path.abspath(event.src_path)
        
        # Debounce logic: cancel previous timer and start a new one
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        self.debounce_timer = threading.Timer(1.0, self.process_change, [abs_path, event_type])
        # Skip internal and ignored directories
        if any(ignored in event.src_path for ignored in ['.git', '__pycache__', '.vscode', '.idea']):
            return
            
        print(f"Detected {event_type} in {os.path.basename(event.src_path)}, waiting for save to settle...")

    def process_change(self, file_path, event_type="modified"):
        send_status({
            "event": "updating", 
            "tier": "Analyzing", 
            "model": "...", 
            "summary": f"Analyzing {os.path.basename(file_path)} ({event_type})...",
            "reasoning": f"Filesystem {event_type} event detected for {os.path.basename(file_path)}. Initiating AST parsing and diff analysis."
        })
        
        # Pipeline execution
        if event_type == "deleted":
            change_set = {"file": file_path, "raw_diff": "", "deleted": True}
            tier_info = {"tier": "major", "reason": "File deletion"}
        else:
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
        
        # Multi-doc orchestration
        from config_loader import load_janitor_config, is_file_in_scope
        watch_path = os.getenv("WATCH_PATH", ".")
        config = load_janitor_config(watch_path)
        
        updated_count = 0
        for doc_config in config.get("docs", []):
            # Skip if file is not in scope for this doc
            if not is_file_in_scope(file_path, doc_config['scope'], watch_path):
                continue

            # Skip Architecture if tier is not major
            if doc_config.get("tier_filter") and tier_info['tier'] not in doc_config['tier_filter']:
                continue

            safe_print(f"-> Updating {doc_config['file']}...")
            summary_info = summarize_impact(change_set, tier_info, model, doc_config)
            
            if summary_info and summary_info['patch']:
                patch_docs(file_path, summary_info)
                updated_count += 1
                
                send_status({
                    "event": "updated",
                    "tier": tier_info['tier'],
                    "model": model,
                    "summary": f"Updated {doc_config['file']}: {summary_info['summary']}",
                    "diff": change_set['raw_diff'],
                    "reasoning": f"Change classified as {tier_info['tier']}. Patching {doc_config['file']} based on scope '{doc_config['scope']}'."
                })

        if updated_count == 0:
            send_status({
                "event": "idle",
                "tier": tier_info['tier'],
                "model": model,
                "summary": "No matching docs in scope.",
                "reasoning": "The changed file did not match any scope patterns in .janitor.config.json."
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
