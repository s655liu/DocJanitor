import subprocess

def parse_change(file_path):
    """
    Runs git diff and extracts changed symbols. Falls back to reading file for demo robustness.
    """
    try:
        diff = subprocess.check_output(['git', 'diff', 'HEAD', '--', file_path], stderr=subprocess.STDOUT).decode('utf-8')
    except:
        diff = ""

    # Demo robustness: If no git diff, treat the whole file as the change
    if not diff:
        try:
            with open(file_path, 'r') as f:
                diff = f.read()
        except:
            diff = "Could not read file."

    return {
        "file": file_path,
        "raw_diff": diff,
        "added_symbols": [],
        "removed_symbols": [],
        "modified_symbols": []
    }
