import re

def normalize_layer_name(name: str, remove_prefixes: list[str], uppercase: bool, strip_chars: list[str]) -> str:
    s = name or ""
    for ch in strip_chars:
        s = s.replace(ch, "")
    if uppercase:
        s = s.upper()
    for pref in remove_prefixes:
        if s.startswith(pref.upper() if uppercase else pref):
            s = s[len(pref):]
    return s

def semantic_from_name(name: str, rules: list[dict]) -> str | None:
    for rule in rules:
        if re.search(rule["match"], name, flags=re.IGNORECASE):
            return rule["semantic"]
    return None

def decide_keep(semantic: str | None, include: set[str], exclude: set[str]) -> bool:
    if semantic in exclude:
        return False
    if include and semantic not in include:
        return False
    return True
