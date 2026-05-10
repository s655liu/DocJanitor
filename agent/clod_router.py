def route_request(tier):
    """
    CLōD-powered model routing.
    Minor changes -> Qwen 2.5 7B (fast, efficient)
    Major changes -> Qwen 2.5 72B (deep reasoning)
    """
    if tier == 'minor':
        return "qwen-2.5-7b-instruct"
    elif tier == 'major':
        return "qwen-2.5-72b-instruct"
    return "qwen-2.5-7b-instruct"  # Fallback
