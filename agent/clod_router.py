def route_request(tier):
    """
    Picks a model based on the change tier.
    """
    if tier == 'minor':
        return "gemini-3.1-flash"
    elif tier == 'major':
        return "gemini-3.1-pro"
    return "gemini-3.1-flash" # Fallback
