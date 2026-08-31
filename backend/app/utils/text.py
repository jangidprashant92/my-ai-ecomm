def limit_to_words(text: str, max_words: int = 10) -> str:
    words = text.split()

    if len(words) <= max_words:
        return text

    return " ".join(words[:max_words]) + "..."
