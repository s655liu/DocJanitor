import os
import re
import requests
from datetime import datetime
from nia_client import get_nia_context

def summarize_impact(change_set, tier_info, model_name):
    """
    Reads current STRUCTURE.md, sends it + the diff to CLōD AI,
    and returns the updated STRUCTURE.md content.
    """
    filename = os.path.basename(change_set['file'])
    is_deleted = change_set.get('deleted', False)
    
    # Read the current STRUCTURE.md
    structure_path = os.path.join(os.path.dirname(change_set['file']), "STRUCTURE.md")
    if not os.path.exists(structure_path):
        structure_path = "STRUCTURE.md"
    
    current_structure = ""
    if os.path.exists(structure_path):
        with open(structure_path, 'r', encoding='utf-8') as f:
            current_structure = f.read()
    
    # Fetch Nia context to ground the AI with real project knowledge
    nia_context = get_nia_context(os.path.basename(change_set['file']))

    # Try CLōD API first
    clod_key = os.getenv("CLOD_API_KEY")
    if clod_key:
        result = _call_clod(change_set, tier_info, model_name, current_structure, clod_key, is_deleted, nia_context)
        if result:
            result['structure_path'] = structure_path
            return result

    # Fallback: offline heuristic
    result = _offline_summary(change_set, tier_info, current_structure, is_deleted)
    result['structure_path'] = structure_path
    return result


def _call_clod(change_set, tier_info, model_name, current_structure, api_key, is_deleted, nia_context=""):
    """Call CLōD API to generate updated STRUCTURE.md."""
    actual_model = "Qwen/Qwen2.5-7B-Instruct-Turbo" if tier_info['tier'] == 'minor' else "Qwen/Qwen2.5-72B-Instruct-Turbo"
    filename = os.path.basename(change_set['file'])
    now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    if is_deleted:
        action_msg = f"The user just DELETED `{filename}`."
        instruction = f"1. REMOVE the section for `{filename}` entirely from STRUCTURE.md."
    else:
        action_msg = f"The user just modified `{filename}`. Here is the new file content:\n---\n{change_set['raw_diff']}\n---"
        instruction = f"1. Update ONLY the section for `{filename}` in the STRUCTURE.md.\n2. Update the **Exports** to reflect only the functions/classes CURRENTLY PRESENT in the file. If something was removed from the code, REMOVE it from the Exports list in STRUCTURE.md."

    nia_section = f"\n\nAdditional context from Nia (project knowledge base):\n---\n{nia_context}\n---" if nia_context else ""

    prompt = f"""You are Auto-Doc Janitor. Your job is to keep STRUCTURE.md perfectly synced with the codebase.{nia_section}

Here is the CURRENT STRUCTURE.md:
---
{current_structure}
---

{action_msg}

Change tier: {tier_info['tier'].upper()} ({tier_info['reason']})
Model used: {model_name}
Timestamp: {now}

INSTRUCTIONS:
{instruction}
3. Update the **Last Updated** timestamp to: {now} (Tier: {tier_info['tier'].capitalize()})
4. Update the **Model Used** to: {model_name}
5. Keep all other sections unchanged.
6. Return the COMPLETE updated STRUCTURE.md content. Nothing else.
"""

    try:
        response = requests.post(
            "https://api.clod.io/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": actual_model,
                "messages": [
                    {"role": "system", "content": "You are a documentation maintenance bot. Return only the updated markdown. No explanations."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000
            },
            timeout=30
        )
        data = response.json()
        if "error" in data:
            print(f"[CLōD unavailable: {data['error'].get('message', '')}]")
            return None
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
