import os
import re
import requests
from datetime import datetime
from nia_client import get_nia_context

def summarize_impact(change_set, tier_info, model_name, target_doc):
    """
    Reads target document, sends it + the diff to CLōD AI,
    and returns the updated content.
    """
    filename = os.path.basename(change_set['file'])
    is_deleted = change_set.get('deleted', False)
    
    # Read the current documentation file
    doc_path = os.path.join(os.path.dirname(change_set['file']), target_doc['file'])
    # If the file is at the root of the watch path
    watch_path = os.getenv("WATCH_PATH", ".")
    if not os.path.exists(doc_path):
        doc_path = os.path.join(watch_path, target_doc['file'])
    
    current_content = ""
    if os.path.exists(doc_path):
        with open(doc_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
    
    # Fetch Nia context to ground the AI with real project knowledge
    nia_context = get_nia_context(os.path.basename(change_set['file']))

    # Try CLōD API first
    clod_key = os.getenv("CLOD_API_KEY")
    if clod_key:
        result = _call_clod(change_set, tier_info, model_name, current_content, clod_key, is_deleted, nia_context, target_doc)
        if result:
            result['structure_path'] = doc_path
            return result

    # Fallback: offline heuristic (only for STRUCTURE.md)
    if target_doc['file'] == "STRUCTURE.md":
        result = _offline_summary(change_set, tier_info, current_content, is_deleted)
        result['structure_path'] = doc_path
        return result
    
    return None


def _call_clod(change_set, tier_info, model_name, current_structure, api_key, is_deleted, nia_context="", target_doc=None):
    """Call CLōD API to generate updated documentation."""
    actual_model = "Qwen/Qwen2.5-7B-Instruct-Turbo" if tier_info['tier'] == 'minor' else "Qwen/Qwen2.5-72B-Instruct-Turbo"
    filename = os.path.basename(change_set['file'])
    now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    doc_type = target_doc['file']
    doc_focus = target_doc.get('describes', 'general project structure')

    if is_deleted:
        action_msg = f"The user just DELETED `{filename}`."
        instruction = f"1. REMOVE the section for `{filename}` entirely from {doc_type}."
    else:
        action_msg = f"The user just modified `{filename}`. Here is the new file content:\n---\n{change_set['raw_diff']}\n---"
        instruction = f"1. Update ONLY the section for `{filename}` in the {doc_type}.\n2. This document focuses on: {doc_focus}.\n3. Ensure the documentation accurately reflects the changes in the code."

    nia_section = f"\n\nAdditional context from Nia (project knowledge base):\n---\n{nia_context}\n---" if nia_context else ""

    prompt = f"""You are Auto-Doc Janitor. Your job is to keep {doc_type} perfectly synced with the codebase.{nia_section}

Here is the CURRENT {doc_type}:
---
{current_structure}
---

{action_msg}

Change tier: {tier_info['tier'].upper()} ({tier_info['reason']})
Model used: {model_name}
Timestamp: {now}

INSTRUCTIONS:
{instruction}
4. Update the **Last Updated** timestamp (if present) to: {now} (Tier: {tier_info['tier'].capitalize()})
5. Update the **Model Used** (if present) to: {model_name}
6. Keep all other sections unchanged.
7. Return the COMPLETE updated {doc_type} content. Nothing else.
"""

    def make_request(token_param):
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a documentation maintenance bot. Return only the updated markdown. No explanations."},
                {"role": "user", "content": prompt}
            ],
            token_param: 1000
        }
        return requests.post(
            "https://api.clod.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )

    try:
        # Try new parameter first
        response = make_request("max_completion_tokens")
        data = response.json()
        
        # If it fails due to the parameter name, retry with the old one
        if response.status_code == 400 and "max_completion_tokens" in data.get("error", {}).get("message", ""):
            response = make_request("max_tokens")
            data = response.json()

        if "error" in data:
            print(f"[CLōD Error] {data['error'].get('message', 'Unknown error')}")
            return None
        
        text = data["choices"][0]["message"]["content"]
        text = data["choices"][0]["message"]["content"]
        # Clean up markdown fences if the model wraps it
        text = re.sub(r'^```(?:markdown)?\s*\n?', '', text.strip())
        text = re.sub(r'\n?```\s*$', '', text.strip())
        
        summary = f"AI removed section for {filename}" if is_deleted else f"AI updated STRUCTURE.md for {filename}"
        return {"summary": summary, "patch": text}
    except Exception as e:
        print(f"[CLōD failed: {str(e)}]")
        return None


def _offline_summary(change_set, tier_info, current_structure, is_deleted):
    """Offline fallback: updates STRUCTURE.md using heuristics."""
    filename = os.path.basename(change_set['file'])
    now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    # Robust pattern: matches from the header until the next header or footer line
    pattern = rf'\n*### [^\n]*`{re.escape(filename)}`.*?(?=\n###|\n---|\Z)'
    
    if is_deleted:
        updated = re.sub(pattern, "", current_structure, flags=re.DOTALL)
        summary = f"{filename}: Removed from structure."
    else:
        raw = change_set.get('raw_diff', '')
        functions = re.findall(r'def (\w+)\s*\(', raw)
        classes = re.findall(r'class (\w+)', raw)
        
        exports = []
        for fn in functions:
            exports.append(f"`{fn}()`")
        for cls in classes:
            exports.append(f"`{cls}`")
        exports_str = ", ".join(exports) if exports else "N/A"
        
        section = f"\n### 🔑 `{filename}`\n"
        section += f"- **Responsibility**: Auto-detected module.\n"
        section += f"- **Exports**: {exports_str}\n"
        section += f"- **Last Updated**: {now} (Tier: {tier_info['tier'].capitalize()})\n"
        section += f"- **Model Used**: Offline Heuristic\n"
        
        if re.search(pattern, current_structure, flags=re.DOTALL):
            updated = re.sub(pattern, "\n" + section, current_structure, flags=re.DOTALL)
        else:
            # Append before the footer
            updated = current_structure.rstrip()
            if "---" in updated:
                parts = updated.rsplit("---", 1)
                updated = parts[0] + "\n" + section + "\n---" + parts[1]
            else:
                updated += "\n\n" + section
        
        summary = f"{filename}: Updated exports to {exports_str}"
        
    return {"summary": summary, "patch": updated}
