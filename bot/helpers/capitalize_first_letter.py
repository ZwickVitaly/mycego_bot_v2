def cap_first(s: str) -> str:
    if not s:
        return s
    return s.replace(s[0], s[0].upper(), 1)
