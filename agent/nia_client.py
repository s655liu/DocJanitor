import os
import requests

NIA_API_BASE = "https://apigcp.trynia.ai/v2"

def get_nia_context(filename: str) -> str:
    """
    Queries Nia to fetch any existing documentation context
    relevant to the changed file. This grounds the AI prompt
    with real project knowledge before generating a STRUCTURE.md patch.
    
    Returns an empty string gracefully if Nia is unavailable.
    """
    api_key = os.getenv("NIA_API_KEY")
    if not api_key:
        return ""

    query = f"What is documented about {filename} in this project? Include any existing responsibilities, exports, or architectural notes."

    try:
        response = requests.post(
            f"{NIA_API_BASE}/search",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "mode": "query",
                "query": query
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            # Extract text from results
            results = data.get("results", [])
            if not results:
                return ""
            
            context_parts = []
            for item in results[:3]:  # Top 3 relevant results
                text = item.get("text") or item.get("content") or item.get("snippet", "")
                if text:
                    context_parts.append(text.strip())
            
            if context_parts:
                return "\n\n".join(context_parts)
        else:
            print(f"[Nia] Query returned status {response.status_code}: {response.text[:200]}")

    except Exception as e:
        print(f"[Nia] Unavailable, skipping context fetch: {e}")

    return ""
