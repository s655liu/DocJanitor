def classify_change(change_set):
    """
    Classifies a ChangeSet into cosmetic / minor / major.
    """
    diff = change_set['raw_diff']
    
    if len(diff) < 50:
        return {"tier": "cosmetic", "reason": "Minimal change"}
    
    if "class " in diff or "def " in diff or "export " in diff:
        # Simple heuristic for now
        if len(diff) > 500:
            return {"tier": "major", "reason": "Large structural change"}
        return {"tier": "minor", "reason": "New symbols or significant logic change"}
    
    return {"tier": "cosmetic", "reason": "No structural symbols found"}
