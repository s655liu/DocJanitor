import os

def summarize_impact(change_set, tier_info, model):
    """
    Calls the LLM to summarize the impact and generate a doc patch.
    """
    # In a real scenario, this would call the CLōD/Gemini API
    filename = os.path.basename(change_set['file'])
    summary = f"Updated {filename} with new functionality ({tier_info['reason']})."
    
    return {
        "summary": summary,
        "patch": f"### {filename}\n- {summary}\n"
    }
