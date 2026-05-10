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

class JanitorHandler(PatternMatchingEventHandler):
    def __init__(self):
        super().__init__(ignore_patterns=["*/__pycache__/*", "*.git*", "*/node_modules/*", "*.md"])

    def on_modified(self, event):
        if event.is_directory:
            return
        
        print(f"File modified: {event.src_path}")
        self.process_change(event.src_path)

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
        
        if tier_info['tier'] == 'cosmetic':
            send_status({
                "event": "idle", 
                "tier": "Cosmetic", 
                "model": "N/A", 
                "summary": "Skipped cosmetic change.",
                "reasoning": "Change classified as cosmetic (whitespace or comments). No documentation update required."
            })
            return

        model = route_request(tier_info['tier'])
        summary_info = summarize_impact(change_set, tier_info, model)
        
        patch_docs(file_path, summary_info)
        
        send_status({
            "event": "updated",
            "tier": tier_info['tier'],
            "model": model,
            "summary": summary_info['summary'],
            "reasoning": f"Change classified as {tier_info['tier']}. Routed to {model}. Documentation patched successfully."
        })

def start_watcher():
    path = "."
    event_handler = JanitorHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
