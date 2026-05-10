import os

def patch_docs(file_path, summary_info):
    """
    Surgically edits STRUCTURE.md or ARCHITECTURE.md.
    """
    doc_path = os.path.join("docs", "STRUCTURE.md")
    
    if not os.path.exists("docs"):
        os.makedirs("docs")
        
    with open(doc_path, "a") as f:
        f.write(summary_info['patch'])
