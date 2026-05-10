import os
import re
import requests
from datetime import datetime

def summarize_impact(change_set, tier_info, model_name):
    """
    Reads current STRUCTURE.md, sends it + the diff to CLōD AI,
    and returns the updated STRUCTURE.md content.
    """
    filename = os.path.basename(change_set['file'])
    
    # Read the current STRUCTURE.md
    structure_path = os.path.join(os.path.dirname(change_set['file']), "STRUCTURE.md")
    if not os.path.exists(structure_path):
        structure_path = "STRUCTURE.md"
    
    current_structure = ""
    if os.path.exists(structure_path):
        with open(structure_path, 'r', encoding='utf-8') as f:
            current_structure = f.read()
    
    # Try CLōD API first
    clod_key = os.getenv("CLOD_API_KEY")
    if clod_key:
        result = _call_clod(change_set, tier_info, model_name, current_structure, clod_key)
        if result:
            result['structure_path'] = structure_path
            return result

    # Fallback: offline heuristic
    result = _offline_summary(change_set, tier_info, current_structure)
    result['structure_path'] = structure_path
    return result


def _call_clod(change_set, tier_info, model_name, current_structure, api_key):
    """Call CLōD API to generate updated STRUCTURE.md."""
    actual_model = "Qwen/Qwen2.5-7B-Instruct-Turbo" if tier_info['tier'] == 'minor' else "Qwen/Qwen2.5-72B-Instruct-Turbo"
    filename = os.path.basename(change_set['file'])
    now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    prompt = f"""You are Auto-Doc Janitor. Your job is to keep STRUCTURE.md perfectly synced with the codebase.

Here is the CURRENT STRUCTURE.md:
---
{current_structure}
---

The user just modified `{filename}`. Here is the new file content:
---
{change_set['raw_diff']}
---

Change tier: {tier_info['tier'].upper()} ({tier_info['reason']})
Model used: {model_name}
Timestamp: {now}

INSTRUCTIONS:
1. Update ONLY the section for `{filename}` in the STRUCTURE.md.
2. Update the **Exports** to reflect the actual functions/classes in the file.
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
        
        first_line = text.strip().split('\n')[0][:120]
        return {"summary": f"AI updated STRUCTURE.md for {filename}", "patch": text}
    except Exception as e:
        print(f"[CLōD failed: {str(e)}]")
        return None


def _offline_summary(change_set, tier_info, current_structure):
    """Offline fallback: updates STRUCTURE.md using heuristics."""
    filename = os.path.basename(change_set['file'])
    raw = change_set.get('raw_diff', '')
    now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    functions = re.findall(r'def (\w+)\s*\(', raw)
    classes = re.findall(r'class (\w+)', raw)
    
    exports = []
    for fn in functions:
        exports.append(f"`{fn}()`")
    for cls in classes:
        exports.append(f"`{cls}`")
    exports_str = ", ".join(exports) if exports else "N/A"
    
    # Build the updated section for this file
    section = f"### 🔑 `{filename}`\n"
    section += f"- **Responsibility**: Auto-detected module.\n"
    section += f"- **Exports**: {exports_str}\n"
    section += f"- **Last Updated**: {now} (Tier: {tier_info['tier'].capitalize()})\n"
    section += f"- **Model Used**: Offline Heuristic\n"
    
    # Try to replace the existing section in STRUCTURE.md
    pattern = rf'### [^\n]*`{re.escape(filename)}`\n(?:- [^\n]*\n)*'
    if re.search(pattern, current_structure):
        updated = re.sub(pattern, section, current_structure)
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
