import json
import os
import fnmatch

def load_janitor_config(watch_path):
    """
    Loads .janitor.config.json from the watch path.
    Returns a list of doc config objects or a default config if not found.
    """
    config_path = os.path.join(watch_path, ".janitor.config.json")
    
    # Default config if file doesn't exist
    default_config = {
        "docs": [
            {
                "file": "STRUCTURE.md",
                "scope": "**/*.{py,js,ts}",
                "describes": "module structure, exports, function signatures"
            }
        ]
    }

    if not os.path.exists(config_path):
        return default_config

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return default_config

def is_file_in_scope(file_path, scope_pattern, watch_path):
    """
    Checks if a relative file path matches a glob pattern.
    Handles comma-separated patterns.
    """
    # Normalize paths
    abs_watch = os.path.abspath(watch_path)
    abs_file = os.path.abspath(file_path)
    rel_path = os.path.relpath(abs_file, abs_watch).replace("\\", "/")
    
    patterns = [p.strip() for p in scope_pattern.split(",")]
    
    import fnmatch

    for pattern in patterns:
        # Handle brace expansion manually {py,js,ts}
        expanded_patterns = []
        if "{" in pattern and "}" in pattern:
            base, ext_part = pattern.split("{", 1)
            extensions = ext_part.split("}", 1)[0].split(",")
            suffix = ext_part.split("}", 1)[1]
            for ext in extensions:
                expanded_patterns.append(f"{base}{ext}{suffix}")
        else:
            expanded_patterns.append(pattern)

        for p in expanded_patterns:
            # Handle the root case carefully
            if "/" not in rel_path:
                # If path is just a filename, only match patterns that don't require a directory
                # or match the filename part of a recursive glob.
                if "/" not in p or p.startswith("**/") or p.startswith("*/"):
                    match_p = p.split("/")[-1]
                    if fnmatch.fnmatch(rel_path, match_p):
                        return True
            else:
                # Standard matching for files in subdirectories
                if fnmatch.fnmatch(rel_path, p):
                    return True
            
    return False
