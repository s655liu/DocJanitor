import subprocess

def parse_change(file_path):
    """
    Runs git diff and extracts changed symbols.
    """
    try:
        diff = subprocess.check_output(['git', 'diff', 'HEAD', '--', file_path]).decode('utf-8')
    except:
        diff = "New file or git error"

    return {
        "file": file_path,
        "raw_diff": diff,
        "added_symbols": [],
        "removed_symbols": [],
        "modified_symbols": []
    }
