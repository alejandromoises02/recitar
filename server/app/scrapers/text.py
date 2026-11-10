def clean_text(value: str) -> str:
    """Collapse runs of whitespace and trim the ends: sources pad titles with stray spaces."""
    return " ".join(value.split())
